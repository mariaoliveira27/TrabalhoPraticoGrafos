"""
Gera dados/mapa.json a partir do OpenStreetMap (OSM).

O grafo é um recorte do Coração Eucarístico e arredores, em volta da PUC Minas: as ruas de
RUAS_DO_RECORTE dentro dos retângulos de REGIAO. Ele cobre a grade a sudeste do campus (Av.
Dom José Gaspar, R. Dom Lúcio Antunes e R. Dom Joaquim Silvério com seis transversais) e o lado
oeste do campus até a Av. Itaú (Av. Edgar da Mata Machado e as ruas entre ela e o campus).

Os vértices são os cruzamentos dessas ruas. Nós do OSM muito próximos, como as duas pistas de
uma avenida no mesmo cruzamento ou os nós de uma rotatória, viram um vértice só. Há também
vértices fixos: a portaria de carros da PUC, um ponto da via interna do campus e pontos de
quebra, que fazem a linha reta entre dois vértices acompanhar uma rua curva. As arestas são os
trechos de rua entre vértices vizinhos.

Do OSM vêm as coordenadas, o sentido de circulação (tags oneway e junction) e, quando existe,
a velocidade máxima (maxspeed). Sem maxspeed, vale o limite padrão do CTB (art. 61) para a
classe da via. A distância de cada aresta continua sendo calculada em mapa.py (Haversine
entre os dois vértices).

Uso, na raiz do repositório (precisa de internet):
    python codigo/dados/gerar_mapa.py
    python codigo/dados/gerar_mapa.py --osm extrato.json   # reaproveita um extrato salvo
"""

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

import requests

CAMINHO_SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mapa.json")

# Retângulo da consulta (sul, oeste, norte, leste): a REGIAO inteira e uma folga
BBOX_CONSULTA = (-19.9295, -43.9985, -19.9170, -43.9855)

SERVIDORES_OVERPASS = (
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
)
# Os servidores recusam o User-Agent padrão do requests (erro 406 ou 429)
CABECALHOS_HTTP = {"User-Agent": "gerar-mapa/1.0 (python-requests)"}

CONSULTA_OVERPASS = """
[out:json][timeout:90];
way["highway"~"^(trunk|primary|secondary|tertiary|unclassified|residential|living_street|service)(_link)?$"]
  ({sul},{oeste},{norte},{leste});
out body geom;
"""

# Sem maxspeed no OSM: limite do CTB (art. 61) para a classe da via, com a classe do OSM
# aproximada pela do CTB (residential = local, tertiary = coletora, secondary e primary =
# arterial, trunk = trânsito rápido). A via interna do campus (service) usa 20 km/h.
VELOCIDADE_PADRAO_POR_CLASSE = {
    "service": 20.0,
    "living_street": 20.0,
    "residential": 30.0,
    "unclassified": 30.0,
    "tertiary": 40.0,
    "secondary": 60.0,
    "primary": 60.0,
    "trunk": 80.0,
}

# Ruas do recorte: nome no OSM -> (chave usada nos ids, nome curto mostrado na interface).
# A ordem define a ordem das ruas nos ids e nomes dos cruzamentos.
RUAS_DO_RECORTE: Dict[str, Tuple[str, str]] = {
    # grade a sudeste do campus
    "Avenida Dom José Gaspar": ("gaspar", "Av. Dom José Gaspar"),
    "Rua Dom Lúcio Antunes": ("lucio", "R. Dom Lúcio Antunes"),
    "Rua Dom Joaquim Silvério": ("joaquim", "R. Dom Joaquim Silvério"),
    "Rua Padre João Crisóstomo": ("crisostomo", "R. Padre João Crisóstomo"),
    "Rua Padre Rossini Cândido": ("rossini", "R. Padre Rossini Cândido"),
    "Rua Padre Pedro Evangelista": ("pedro", "R. Padre Pedro Evangelista"),
    "Rua Coração Eucarístico de Jesus": ("coracao", "R. Coração Eucarístico de Jesus"),
    "Rua Padre Demerval Gomes": ("demerval", "R. Padre Demerval Gomes"),
    "Rua Dom Aristides Porto": ("aristides", "R. Dom Aristides Porto"),
    # lado oeste do campus até a Av. Itaú; nesse trecho a pista que sobe da
    # Av. Edgar da Mata Machado se chama Avenida 31 de Março no OSM
    "Avenida Edgar da Mata Machado": ("edgar", "Av. Edgar da Mata Machado"),
    "Avenida 31 de Março": ("edgar", "Av. Edgar da Mata Machado"),
    "Avenida Itaú": ("itau", "Av. Itaú"),
    "Rua Padre Júlio Lombaerde": ("lombaerde", "R. Padre Júlio Lombaerde"),
    "Rua Madre Mazzarello": ("mazzarello", "R. Madre Mazzarello"),
    "Rua Madre Beatriz Frambach": ("frambach", "R. Madre Beatriz Frambach"),
    "Rua Ivan Moraes de Andrade": ("ivan", "R. Ivan Moraes de Andrade"),
    "Rua Osvaldo Gattoni": ("gattoni", "R. Osvaldo Gattoni"),
    "Rua São Pedro Julião": ("sao_pedro", "R. São Pedro Julião"),
    "Rua Edna Maria da Paixão": ("edna", "R. Edna Maria da Paixão"),
}

# Rotatórias com nome próprio no OSM -> chave do id; as outras levam o nome das ruas que chegam
ROTATORIAS_COM_NOME = {"Praça Cardeal Dom Serafim": "dom_serafim"}

# Retângulos (sul, oeste, norte, leste) do recorte; o que fica fora deles é descartado
REGIAO = [
    (-19.9277, -43.9935, -19.9218, -43.9871),  # grade a sudeste do campus
    (-19.9272, -43.9968, -19.9183, -43.9925),  # lado oeste do campus e Av. Itaú, até o Underground
]

# Cruzamentos do OSM a até esta distância viram um vértice só
RAIO_AGRUPAMENTO_M = 25.0

# Acesso de carros ao campus: nó em que a via interna encontra a Av. Dom José Gaspar e um nó
# dessa via ~70 m campus adentro, a 147 m do POI da PUC no catálogo (limite: 200 m). Sem ele,
# a PUC ficaria fora da área do mapa: a Av. Dom José Gaspar passa a 209 m do POI.
NO_PORTARIA_PUC = 8878373449
NO_VIA_INTERNA_PUC = 7794420795

# Pontos de quebra (id, nome, coordenada, raio em m): os nós do recorte a até esse raio da
# coordenada viram um vértice, para a reta entre vértices acompanhar uma rua curva
PONTOS_DE_QUEBRA: List[Tuple[str, str, Tuple[float, float], float]] = [
    ("no_edgar_curva", "Av. Edgar da Mata Machado (curva junto ao campus)", (-19.92404, -43.99603), 30.0),
    ("no_lombaerde_curva", "R. Padre Júlio Lombaerde (curva)", (-19.92041, -43.99447), 12.0),
]

# Trecho que se afasta mais que isto da reta entre seus vértices gera aviso (pede ponto de quebra)
LIMITE_DESVIO_M = 20.0

RAIO_TERRA_METROS = 6371000.0

Coordenada = Tuple[float, float]


def distancia_m(a: Coordenada, b: Coordenada) -> float:
    """Haversine, como em mapa.calcular_distancia_haversine."""
    phi1, phi2 = math.radians(a[0]), math.radians(b[0])
    dphi, dlambda = phi2 - phi1, math.radians(b[1] - a[1])
    h = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return RAIO_TERRA_METROS * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def desvio_m(ponto: Coordenada, a: Coordenada, b: Coordenada) -> float:
    """Distância (m) do ponto ao segmento a-b, numa aproximação plana local."""
    k = math.cos(math.radians(ponto[0]))
    ax, ay = (a[1] - ponto[1]) * k, a[0] - ponto[0]
    bx, by = (b[1] - ponto[1]) * k, b[0] - ponto[0]
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
    return math.radians(math.hypot(ax + t * dx, ay + t * dy)) * RAIO_TERRA_METROS


def dentro_da_regiao(ponto: Coordenada) -> bool:
    return any(sul <= ponto[0] <= norte and oeste <= ponto[1] <= leste
               for sul, oeste, norte, leste in REGIAO)


# ---------------------------------------------------------------------------
# Extrato do OSM
# ---------------------------------------------------------------------------

def baixar_extrato() -> Dict[str, Any]:
    """Baixa as vias do retângulo; tenta cada servidor Overpass até um responder."""
    sul, oeste, norte, leste = BBOX_CONSULTA
    consulta = CONSULTA_OVERPASS.format(sul=sul, oeste=oeste, norte=norte, leste=leste)
    erros = []
    for servidor in SERVIDORES_OVERPASS:
        try:
            resposta = requests.post(servidor, data={"data": consulta}, headers=CABECALHOS_HTTP, timeout=120)
            resposta.raise_for_status()
            return resposta.json()
        except (requests.RequestException, ValueError) as erro:
            erros.append(f"{servidor}: {erro}")
    raise RuntimeError("Nenhum servidor Overpass respondeu:\n  " + "\n  ".join(erros))


def sentidos(tags: Dict[str, str]) -> Tuple[bool, bool]:
    """(ida, volta) em relação à ordem dos nós da via."""
    oneway = tags.get("oneway")
    if oneway in ("yes", "true", "1"):
        return True, False
    if oneway == "-1":
        return False, True
    if oneway is None and tags.get("junction") in ("roundabout", "circular"):
        return True, False  # rotatória: mão única implícita
    return True, True


class Malha:
    """Todas as vias do extrato como grafo dirigido de nós do OSM, respeitando a mão de cada via."""

    def __init__(self, extrato: Dict[str, Any]) -> None:
        self.vias: Dict[int, Dict[str, Any]] = {}
        self.coord: Dict[int, Coordenada] = {}
        self.arcos: Dict[int, List[Tuple[int, int]]] = defaultdict(list)  # nó -> [(vizinho, via)]

        for via in extrato["elements"]:
            if via.get("type") != "way":
                continue
            self.vias[via["id"]] = via
            nos = via["nodes"]
            for no, ponto in zip(nos, via["geometry"]):
                self.coord[no] = (ponto["lat"], ponto["lon"])
            ida, volta = sentidos(via["tags"])
            for a, b in zip(nos, nos[1:]):
                if ida:
                    self.arcos[a].append((b, via["id"]))
                if volta:
                    self.arcos[b].append((a, via["id"]))

    def caminho(self, origens: FrozenSet[int], destinos: FrozenSet[int],
                vias_permitidas: Set[int]) -> Optional[Tuple[float, Counter]]:
        """
        Menor caminho (m) de qualquer nó de origens a qualquer nó de destinos andando só pelas
        vias permitidas e no sentido permitido. Devolve (comprimento, metros por via) ou None.
        """
        melhor = {no: 0.0 for no in origens}
        via_usada: Dict[int, Tuple[int, int]] = {}
        pendentes = set(origens)
        while pendentes:
            atual = min(pendentes, key=melhor.__getitem__)
            pendentes.remove(atual)
            if atual in destinos:
                metros_por_via: Counter = Counter()
                no = atual
                while no in via_usada:
                    anterior, via_id = via_usada[no]
                    metros_por_via[via_id] += distancia_m(self.coord[anterior], self.coord[no])
                    no = anterior
                return melhor[atual], metros_por_via
            for vizinho, via_id in self.arcos[atual]:
                if via_id not in vias_permitidas:
                    continue
                novo = melhor[atual] + distancia_m(self.coord[atual], self.coord[vizinho])
                if novo < melhor.get(vizinho, math.inf):
                    melhor[vizinho] = novo
                    via_usada[vizinho] = (atual, via_id)
                    pendentes.add(vizinho)
        return None

    def velocidade_kmh(self, metros_por_via: Counter) -> float:
        """maxspeed (ou o padrão da classe) da via que cobre a maior parte do trecho."""
        via_principal = self.vias[metros_por_via.most_common(1)[0][0]]["tags"]
        maxspeed = via_principal.get("maxspeed", "").split(" ")[0]
        if maxspeed.isdigit():
            return float(maxspeed)
        classe = via_principal.get("highway", "residential").replace("_link", "")
        return VELOCIDADE_PADRAO_POR_CLASSE.get(classe, 30.0)


# ---------------------------------------------------------------------------
# Recorte: ruas escolhidas dentro da região
# ---------------------------------------------------------------------------

def eh_rotatoria(tags: Dict[str, str]) -> bool:
    return tags.get("junction") in ("roundabout", "circular")


class Recorte:
    """As ruas do recorte dentro da REGIAO, como grafo não dirigido de nós do OSM."""

    def __init__(self, malha: Malha) -> None:
        self.malha = malha
        self.vizinhos: Dict[int, Set[int]] = defaultdict(set)
        self.via_do_segmento: Dict[FrozenSet[int], int] = {}
        self.permitidos: Set[Tuple[int, int]] = set()  # (a, b): dá para ir de a até b

        for via_id, via in malha.vias.items():
            tags = via["tags"]
            if tags.get("highway") == "service":
                continue
            if tags.get("name") not in RUAS_DO_RECORTE and not eh_rotatoria(tags):
                continue
            ida, volta = sentidos(tags)
            for a, b in zip(via["nodes"], via["nodes"][1:]):
                if not (dentro_da_regiao(malha.coord[a]) and dentro_da_regiao(malha.coord[b])):
                    continue
                self.vizinhos[a].add(b)
                self.vizinhos[b].add(a)
                self.via_do_segmento[frozenset((a, b))] = via_id
                if ida:
                    self.permitidos.add((a, b))
                if volta:
                    self.permitidos.add((b, a))

    def vias_do_no(self, no: int) -> Set[int]:
        return {self.via_do_segmento[frozenset((no, vizinho))] for vizinho in self.vizinhos[no]}

    def chave_da_via(self, via_id: int) -> str:
        """Chave da rua em RUAS_DO_RECORTE (as duas pistas da mesma avenida têm a mesma chave)."""
        tags = self.malha.vias[via_id]["tags"]
        if tags.get("name") in RUAS_DO_RECORTE:
            return RUAS_DO_RECORTE[tags["name"]][0]
        return "rotatoria"

    def caminhar(self, inicio: int, segundo: int, grupo_do_no: Dict[int, str]) -> Optional[List[int]]:
        """Segue a rua a partir de inicio -> segundo até o próximo vértice (None se a rua acaba)."""
        caminho = [inicio, segundo]
        while caminho[-1] not in grupo_do_no:
            seguintes = self.vizinhos[caminho[-1]] - {caminho[-2]}
            if len(seguintes) != 1 or len(caminho) > len(self.vizinhos):
                return None  # rua sem saída ou cortada pela borda da região
            caminho.append(next(iter(seguintes)))
        return caminho


def _ordem_das_chaves() -> Dict[str, int]:
    chaves = dict.fromkeys(chave for chave, _curto in RUAS_DO_RECORTE.values())
    return {chave: posicao for posicao, chave in enumerate(chaves)}


def descrever_grupo(nos: Set[int], recorte: Recorte) -> Tuple[str, str]:
    """(id, nome) do vértice a partir das ruas que passam pelos nós do grupo."""
    tags = [recorte.malha.vias[v]["tags"] for no in nos for v in recorte.vias_do_no(no)]
    ordem = _ordem_das_chaves()
    ruas = sorted({RUAS_DO_RECORTE[t["name"]] for t in tags if t.get("name") in RUAS_DO_RECORTE},
                  key=lambda rua: ordem[rua[0]])
    chaves = "_".join(chave for chave, _curto in ruas)
    nomes = " x ".join(curto for _chave, curto in ruas)
    aneis = [t for t in tags if eh_rotatoria(t)]
    if aneis:
        nome_anel = next((t["name"] for t in aneis if t.get("name")), None)
        if nome_anel in ROTATORIAS_COM_NOME:
            return f"no_rotatoria_{ROTATORIAS_COM_NOME[nome_anel]}", f"{nome_anel} (rotatória: {nomes})"
        return f"no_rotatoria_{chaves}", f"Rotatória: {nomes}"
    return f"no_{chaves}", nomes


def agrupar_vertices(recorte: Recorte) -> Dict[str, Dict[str, Any]]:
    """id do vértice -> {nome, nós}: cruzamentos, rotatórias, pontos fixos e de quebra."""
    coord = recorte.malha.coord
    pai: Dict[int, int] = {}

    def raiz(no: int) -> int:
        while pai[no] != no:
            pai[no] = pai[pai[no]]
            no = pai[no]
        return no

    def unir(a: int, b: int) -> None:
        pai[raiz(a)] = raiz(b)

    fixos = {NO_PORTARIA_PUC, NO_VIA_INTERNA_PUC}
    quebras = {nome_id: {no for no in recorte.vizinhos if distancia_m(coord[no], ponto) <= raio}
               for nome_id, _nome, ponto, raio in PONTOS_DE_QUEBRA}
    reservados = fixos.union(*quebras.values()) if quebras else set(fixos)

    # cruzamento: nó de onde saem 3 ou mais trechos, ou esquina em que uma rua do recorte vira outra
    candidatos = [no for no, vizinhos in recorte.vizinhos.items()
                  if no not in reservados
                  and (len(vizinhos) >= 3 or len({recorte.chave_da_via(v) for v in recorte.vias_do_no(no)}) >= 2)]
    for via_id in {recorte.via_do_segmento[s] for s in recorte.via_do_segmento}:
        if eh_rotatoria(recorte.malha.vias[via_id]["tags"]):
            nos_do_anel = [no for no in recorte.malha.vias[via_id]["nodes"] if no in recorte.vizinhos]
            candidatos.extend(no for no in nos_do_anel if no not in reservados)
            for a, b in zip(nos_do_anel, nos_do_anel[1:]):
                pai.setdefault(a, a)
                pai.setdefault(b, b)
                unir(a, b)
    candidatos = sorted(set(candidatos))
    for no in candidatos:
        pai.setdefault(no, no)
    for i, a in enumerate(candidatos):
        for b in candidatos[i + 1:]:
            if distancia_m(coord[a], coord[b]) <= RAIO_AGRUPAMENTO_M:
                unir(a, b)

    grupos: Dict[int, Set[int]] = defaultdict(set)
    for no in candidatos:
        grupos[raiz(no)].add(no)

    vertices: Dict[str, Dict[str, Any]] = {}
    for nos in grupos.values():
        id_vertice, nome = descrever_grupo(nos, recorte)
        while id_vertice in vertices:  # a mesma dupla de ruas se cruza duas vezes
            id_vertice += "_b"
        vertices[id_vertice] = {"nome": nome, "nos": nos}
    for nome_id, nome, _ponto, _raio in PONTOS_DE_QUEBRA:
        if not quebras[nome_id]:
            raise ValueError(f"Ponto de quebra {nome_id}: nenhum nó do recorte perto da coordenada")
        vertices[nome_id] = {"nome": nome, "nos": quebras[nome_id]}
    vertices["no_portaria_puc"] = {"nome": "Portaria da PUC Minas (Av. Dom José Gaspar)",
                                   "nos": {NO_PORTARIA_PUC}}
    vertices["no_puc_via_interna"] = {"nome": "PUC Minas (via interna do campus)",
                                      "nos": {NO_VIA_INTERNA_PUC}}
    return vertices


def montar_trechos(recorte: Recorte, vertices: Dict[str, Dict[str, Any]],
                   coordenadas: Dict[str, Coordenada]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Arestas entre vértices vizinhos (uma por par, de mão dupla quando os dois sentidos existem)."""
    malha = recorte.malha
    grupo_do_no = {no: id_vertice for id_vertice, dados in vertices.items() for no in dados["nos"]}
    por_par: Dict[Tuple[str, str], Dict[str, Any]] = {}
    avisos = []
    vistos: Set[FrozenSet[FrozenSet[int]]] = set()

    for no, origem in grupo_do_no.items():
        for vizinho in recorte.vizinhos.get(no, ()):
            if grupo_do_no.get(vizinho) == origem:
                continue
            caminho = recorte.caminhar(no, vizinho, grupo_do_no)
            if caminho is None or grupo_do_no[caminho[-1]] == origem:
                continue
            segmentos = frozenset(frozenset(par) for par in zip(caminho, caminho[1:]))
            if segmentos in vistos:
                continue
            vistos.add(segmentos)
            destino = grupo_do_no[caminho[-1]]
            pares = list(zip(caminho, caminho[1:]))
            ida = all(par in recorte.permitidos for par in pares)
            volta = all((b, a) in recorte.permitidos for a, b in pares)
            if not (ida or volta):
                continue
            chave = tuple(sorted((origem, destino)))
            dados = por_par.setdefault(chave, {"sentidos": set(), "metros": Counter()})
            if ida:
                dados["sentidos"].add((origem, destino))
            if volta:
                dados["sentidos"].add((destino, origem))
            for a, b in pares:
                dados["metros"][recorte.via_do_segmento[frozenset((a, b))]] += distancia_m(malha.coord[a], malha.coord[b])
            desvio = max(desvio_m(malha.coord[n], coordenadas[origem], coordenadas[destino]) for n in caminho)
            if desvio > LIMITE_DESVIO_M:
                avisos.append(f"trecho {origem} - {destino} se afasta {desvio:.0f} m da reta "
                              f"(perto de {malha.coord[max(caminho, key=lambda n: desvio_m(malha.coord[n], coordenadas[origem], coordenadas[destino]))]})")

    servico = {v for v, via in malha.vias.items() if via["tags"].get("highway") == "service"}
    portaria, interna = frozenset({NO_PORTARIA_PUC}), frozenset({NO_VIA_INTERNA_PUC})
    for de, para, nos_de, nos_para in (("no_portaria_puc", "no_puc_via_interna", portaria, interna),
                                       ("no_puc_via_interna", "no_portaria_puc", interna, portaria)):
        trajeto = malha.caminho(nos_de, nos_para, servico)
        if trajeto is not None:
            dados = por_par.setdefault(tuple(sorted((de, para))), {"sentidos": set(), "metros": Counter()})
            dados["sentidos"].add((de, para))
            dados["metros"].update(trajeto[1])

    arestas = []
    for (a, b), dados in sorted(por_par.items()):
        mao_dupla = len(dados["sentidos"]) == 2
        origem, destino = (a, b) if mao_dupla else next(iter(dados["sentidos"]))
        via_principal = malha.vias[dados["metros"].most_common(1)[0][0]]["tags"]
        nome_rua = via_principal.get("name") or (
            "Via interna da PUC Minas" if via_principal.get("highway") == "service" else "Rotatória")
        arestas.append({
            "id": f"e_{origem[3:]}__{destino[3:]}",
            "origem": origem,
            "destino": destino,
            "nome_rua": nome_rua,
            "velocidade_kmh": malha.velocidade_kmh(dados["metros"]),
            "oneway": not mao_dupla,
            "osm_vias": sorted(dados["metros"]),
        })
    return arestas, avisos


def pares_sem_caminho(ids: List[str], arestas: List[Dict[str, Any]]) -> int:
    saida: Dict[str, Set[str]] = defaultdict(set)
    for aresta in arestas:
        saida[aresta["origem"]].add(aresta["destino"])
        if not aresta["oneway"]:
            saida[aresta["destino"]].add(aresta["origem"])
    faltando = 0
    for origem in ids:
        alcancados, pilha = {origem}, [origem]
        while pilha:
            for proximo in saida[pilha.pop()]:
                if proximo not in alcancados:
                    alcancados.add(proximo)
                    pilha.append(proximo)
        faltando += len(ids) - len(alcancados)
    return faltando


def gerar_mapa(extrato: Dict[str, Any]) -> Dict[str, Any]:
    malha = Malha(extrato)
    recorte = Recorte(malha)
    vertices = agrupar_vertices(recorte)

    coordenadas: Dict[str, Coordenada] = {}
    for id_vertice, dados in vertices.items():
        pontos = [malha.coord[no] for no in dados["nos"]]
        coordenadas[id_vertice] = (round(sum(p[0] for p in pontos) / len(pontos), 7),
                                   round(sum(p[1] for p in pontos) / len(pontos), 7))

    arestas, avisos = montar_trechos(recorte, vertices, coordenadas)
    usados = {a["origem"] for a in arestas} | {a["destino"] for a in arestas}
    saida_vertices = [
        {
            "id": id_vertice,
            "nome": dados["nome"],
            "latitude": coordenadas[id_vertice][0],
            "longitude": coordenadas[id_vertice][1],
            "osm_nos": sorted(dados["nos"]),
        }
        for id_vertice, dados in vertices.items()
        if id_vertice in usados  # rotatória ou cruzamento sem ligação com o resto fica de fora
    ]

    for aviso in avisos:
        print("  aviso:", aviso)
    ids = [v["id"] for v in saida_vertices]
    print(f"  pares ordenados sem caminho: {pares_sem_caminho(ids, arestas)} de {len(ids) * (len(ids) - 1)}")

    latitudes = [v["latitude"] for v in saida_vertices]
    longitudes = [v["longitude"] for v in saida_vertices]
    return {
        "metadados": {
            "regiao": "Coração Eucarístico e arredores, Belo Horizonte - MG",
            "descricao": (
                "Recorte em volta da PUC Minas: a grade a sudeste do campus (Av. Dom José Gaspar, "
                "R. Dom Lúcio Antunes e R. Dom Joaquim Silvério com seis transversais) e o lado oeste "
                "do campus até a Av. Itaú, com a portaria de carros da PUC e um ponto da via interna."
            ),
            "fonte": "OpenStreetMap, consulta à Overpass API (codigo/dados/gerar_mapa.py)",
            "licenca": "Open Database License (ODbL)",
            "atribuicao": "© colaboradores do OpenStreetMap",
            "data_extracao": extrato.get("osm3s", {}).get("timestamp_osm_base", ""),
            "velocidades": (
                "maxspeed do OSM quando existe; senão o limite do CTB (art. 61) pela classe da via: "
                "residential 30, tertiary 40, secondary e primary 60, trunk 80 km/h; "
                "via interna do campus (service) 20 km/h"
            ),
            "bounding_box": {
                "min_lat": min(latitudes),
                "max_lat": max(latitudes),
                "min_lon": min(longitudes),
                "max_lon": max(longitudes),
            },
        },
        "vertices": saida_vertices,
        "arestas": arestas,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera dados/mapa.json a partir do OpenStreetMap.")
    parser.add_argument("--osm", help="extrato JSON da Overpass já salvo (não baixa de novo)")
    parser.add_argument("--saida", default=CAMINHO_SAIDA, help="arquivo de saída (padrão: dados/mapa.json)")
    argumentos = parser.parse_args()

    if argumentos.osm:
        with open(argumentos.osm, encoding="utf-8") as arquivo:
            extrato = json.load(arquivo)
    else:
        extrato = baixar_extrato()

    mapa = gerar_mapa(extrato)
    with open(argumentos.saida, "w", encoding="utf-8") as arquivo:
        json.dump(mapa, arquivo, indent=2, ensure_ascii=False)
        arquivo.write("\n")

    arcos = sum(1 if a["oneway"] else 2 for a in mapa["arestas"])
    print(f"{len(mapa['vertices'])} vértices, {len(mapa['arestas'])} registros de aresta, "
          f"{arcos} arestas direcionadas -> {argumentos.saida}")


if __name__ == "__main__":
    main()
