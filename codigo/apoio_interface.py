"""
Funções puras de apoio à interface (app.py).

Nada aqui depende do Streamlit nem da rede, então tudo pode ser testado com pytest:
    - converter os rótulos da tela ("Distância", "Tempo", "Custo") nos critérios do grafo;
    - validar o pedido de rota entre dois POIs e montar a rota que o app guarda em
      st.session_state["rota"], junto com os parâmetros usados no cálculo;
    - conferir se a rota guardada ainda corresponde à seleção atual;
    - montar os textos de aviso e formatar números no padrão brasileiro (0,60 km).
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

from grafo import (
    CRITERIO_CUSTO,
    CRITERIO_DISTANCIA,
    CRITERIO_TEMPO,
    SITUACAO_INALCANCAVEL,
    Grafo,
    ResultadoRota,
    Vertice,
)
from mapa import LIMITE_ASSOCIACAO_METROS, associar_poi_ao_vertice
from rotas import calcularRotaBellmanFord, calcularRotaDijkstra

# Rótulo do selectbox de critério -> critério aceito por rotas.py.
# normalizarCriterio (grafo.py) não remove acentos: "Distância" precisa ser convertido
# antes de chegar aos algoritmos, senão o pedido volta como 'invalida'.
ROTULOS_CRITERIOS: Dict[str, str] = {
    "Distância": CRITERIO_DISTANCIA,
    "Tempo": CRITERIO_TEMPO,
    "Custo": CRITERIO_CUSTO,
}

FuncaoDeRota = Callable[[Grafo, str, str, str], ResultadoRota]

# Nome do selectbox de algoritmo -> função de rotas.py
ALGORITMOS: Dict[str, FuncaoDeRota] = {
    "Dijkstra": calcularRotaDijkstra,
    "Bellman-Ford": calcularRotaBellmanFord,
}

# Motivos para não chamar o algoritmo (campo "motivo" de preparar_pedido_rota)
MOTIVO_MESMO_LOCAL = "mesmo_local"
MOTIVO_FORA_DA_AREA = "fora_da_area"
MOTIVO_MESMO_VERTICE = "mesmo_vertice"

# Troca vírgula por ponto e vice-versa: "1,234.50" (padrão americano) -> "1.234,50"
_TROCA_SEPARADORES = str.maketrans(",.", ".,")


# ---------------------------------------------------------------------------
# Seleção feita na tela
# ---------------------------------------------------------------------------

def rotulo_para_criterio(rotulo: str) -> str:
    """
    Converte o rótulo da interface no critério do grafo:
    'Distância' -> CRITERIO_DISTANCIA, 'Tempo' -> CRITERIO_TEMPO e 'Custo' -> CRITERIO_CUSTO.
    Lança ValueError para rótulo desconhecido.
    """
    if not isinstance(rotulo, str) or rotulo not in ROTULOS_CRITERIOS:
        raise ValueError(
            f"Rótulo de critério {rotulo!r} desconhecido. "
            f"Utilize um de: {', '.join(ROTULOS_CRITERIOS)}."
        )
    return ROTULOS_CRITERIOS[rotulo]


def obter_algoritmo(nome: str) -> FuncaoDeRota:
    """Devolve a função de rotas.py para o nome mostrado na tela; ValueError se desconhecido."""
    if not isinstance(nome, str) or nome not in ALGORITMOS:
        raise ValueError(
            f"Algoritmo {nome!r} desconhecido. Utilize um de: {', '.join(ALGORITMOS)}."
        )
    return ALGORITMOS[nome]


def parametros_da_selecao(
    origem: str,
    destino: str,
    rotulo_criterio: str,
    nome_algoritmo: str
) -> Dict[str, str]:
    """Parâmetros que identificam um cálculo: nomes dos POIs, rótulo do critério e algoritmo."""
    return {
        "origem": origem,
        "destino": destino,
        "criterio": rotulo_criterio,
        "algoritmo": nome_algoritmo,
    }


def rota_corresponde_a_selecao(
    rota: Optional[Dict[str, Any]],
    parametros: Optional[Dict[str, str]]
) -> bool:
    """Indica se a rota guardada foi calculada exatamente com os parâmetros da seleção atual."""
    if not rota or parametros is None:
        return False
    return rota.get("parametros") == parametros


# ---------------------------------------------------------------------------
# Pedido e cálculo da rota
# ---------------------------------------------------------------------------

def preparar_pedido_rota(
    poi_origem: Dict[str, Any],
    poi_destino: Dict[str, Any],
    grafo: Grafo,
    limite_m: float = LIMITE_ASSOCIACAO_METROS
) -> Dict[str, Any]:
    """
    Associa origem e destino aos vértices do grafo e confere se vale chamar o algoritmo.

    Devolve um dicionário com:
        id_origem, distancia_origem_m: vértice da origem e distância (m) do POI até ele;
        id_destino, distancia_destino_m: o mesmo para o destino;
        motivo: None se o algoritmo pode ser chamado; senão MOTIVO_MESMO_LOCAL,
                MOTIVO_FORA_DA_AREA ou MOTIVO_MESMO_VERTICE;
        aviso: texto para o usuário quando há motivo (None quando não há).
    """
    pedido: Dict[str, Any] = {
        "id_origem": None,
        "distancia_origem_m": None,
        "id_destino": None,
        "distancia_destino_m": None,
        "motivo": None,
        "aviso": None,
    }

    if _mesmo_poi(poi_origem, poi_destino):
        pedido["motivo"] = MOTIVO_MESMO_LOCAL
        pedido["aviso"] = "A origem e o destino devem ser diferentes."
        return pedido

    id_origem, distancia_origem_m = associar_poi_ao_vertice(poi_origem, grafo)
    id_destino, distancia_destino_m = associar_poi_ao_vertice(poi_destino, grafo)
    pedido.update(
        id_origem=id_origem,
        distancia_origem_m=distancia_origem_m,
        id_destino=id_destino,
        distancia_destino_m=distancia_destino_m,
    )

    for poi, distancia_m in ((poi_origem, distancia_origem_m), (poi_destino, distancia_destino_m)):
        if distancia_m > limite_m:
            pedido["motivo"] = MOTIVO_FORA_DA_AREA
            pedido["aviso"] = (
                f"'{poi.get('nome')}' está fora da área do mapa: "
                f"{_explicar_distancia_ao_grafo(distancia_m, limite_m)}."
            )
            return pedido

    if id_origem == id_destino:
        pedido["motivo"] = MOTIVO_MESMO_VERTICE
        pedido["aviso"] = (
            f"'{poi_origem.get('nome')}' e '{poi_destino.get('nome')}' ficam junto ao mesmo "
            f"cruzamento do grafo ({_nome_do_vertice(grafo.getVertice(id_origem))}), então não "
            "há trecho de rua para percorrer entre eles. Escolha locais mais distantes."
        )
    return pedido


def calcular_rota_entre_pois(
    grafo: Grafo,
    poi_origem: Dict[str, Any],
    poi_destino: Dict[str, Any],
    rotulo_criterio: str,
    nome_algoritmo: str,
    limite_m: float = LIMITE_ASSOCIACAO_METROS
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Faz o cálculo do botão "Calcular rota" sem depender do Streamlit.

    Devolve (rota, aviso). Com sucesso, aviso é None e rota é o dicionário que o app
    guarda em st.session_state["rota"]:
        parametros: os de parametros_da_selecao usados neste cálculo;
        resultado: ResultadoRota do algoritmo (totais só do trajeto pelo grafo);
        caminho, nomes_caminho: [lat, lon] e nome de cada vértice percorrido;
        origem, destino: trecho a pé entre cada POI e o seu vértice (fora dos totais).
    Quando não há rota para mostrar, rota é None e aviso explica o motivo: mesmo local,
    POI fora da área ou mesmo vértice (casos em que o algoritmo nem é chamado),
    destino inalcançável ou pedido inválido.

    Lança ValueError para rótulo de critério ou nome de algoritmo desconhecido.
    """
    criterio = rotulo_para_criterio(rotulo_criterio)
    calcular_rota = obter_algoritmo(nome_algoritmo)

    pedido = preparar_pedido_rota(poi_origem, poi_destino, grafo, limite_m)
    if pedido["motivo"] is not None:
        return None, pedido["aviso"]

    resultado = calcular_rota(grafo, pedido["id_origem"], pedido["id_destino"], criterio)
    if not resultado.foiEncontrada():
        if resultado.situacao == SITUACAO_INALCANCAVEL:
            return None, (
                f"Destino inalcançável: não há caminho de '{poi_origem.get('nome')}' até "
                f"'{poi_destino.get('nome')}' no grafo respeitando o sentido das vias."
            )
        return None, "Não foi possível calcular a rota: solicitação inválida ou ciclo negativo."

    vertices_caminho = resultado.getVerticesCaminho()
    rota = {
        "parametros": parametros_da_selecao(
            poi_origem.get("nome"), poi_destino.get("nome"), rotulo_criterio, nome_algoritmo
        ),
        "resultado": resultado,
        "caminho": [[v.latitude, v.longitude] for v in vertices_caminho],
        "nomes_caminho": [_nome_do_vertice(v) for v in vertices_caminho],
        "origem": _trecho_a_pe(
            poi_origem, grafo.getVertice(pedido["id_origem"]), pedido["distancia_origem_m"]
        ),
        "destino": _trecho_a_pe(
            poi_destino, grafo.getVertice(pedido["id_destino"]), pedido["distancia_destino_m"]
        ),
    }
    return rota, None


def trechos_do_mapa(grafo: Grafo) -> List[List[List[float]]]:
    """
    Um segmento [[lat, lon], [lat, lon]] por trecho de rua do grafo, para desenhar a área
    coberta pelo mapa. As duas arestas de uma rua de mão dupla viram um segmento só.
    """
    segmentos = {}
    for aresta in grafo.getArestas():
        chave = frozenset((aresta.origem.id, aresta.destino.id))
        if chave not in segmentos:
            segmentos[chave] = [
                [aresta.origem.latitude, aresta.origem.longitude],
                [aresta.destino.latitude, aresta.destino.longitude],
            ]
    return list(segmentos.values())


def limites_dos_pontos(pontos: List[List[float]]) -> List[List[float]]:
    """[[lat_min, lon_min], [lat_max, lon_max]] que contém todos os pontos [lat, lon]."""
    latitudes = [ponto[0] for ponto in pontos]
    longitudes = [ponto[1] for ponto in pontos]
    return [[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]]


def limites_do_enquadramento(rota: Dict[str, Any]) -> List[List[float]]:
    """
    Limites que contêm os POIs de origem e destino e todos os vértices do caminho,
    para o fit_bounds do mapa.
    """
    return limites_dos_pontos([
        rota["origem"]["poi"]["coordenadas"],
        *rota["caminho"],
        rota["destino"]["poi"]["coordenadas"],
    ])


def _mesmo_poi(poi_a: Dict[str, Any], poi_b: Dict[str, Any]) -> bool:
    """Mesmo local do catálogo: mesmo id (quando há) ou mesmo nome."""
    id_a = poi_a.get("id")
    if id_a and id_a == poi_b.get("id"):
        return True
    return poi_a.get("nome") == poi_b.get("nome")


def _nome_do_vertice(vertice: Vertice) -> str:
    return vertice.nome or vertice.id


def _trecho_a_pe(poi: Dict[str, Any], vertice: Vertice, distancia_m: float) -> Dict[str, Any]:
    """Trecho em linha reta entre o POI e o vértice associado (não entra nos totais da rota)."""
    return {
        "poi": {
            "id": poi.get("id"),
            "nome": poi.get("nome"),
            "coordenadas": [poi["coordenadas"][0], poi["coordenadas"][1]],
        },
        "id_vertice": vertice.id,
        "nome_vertice": _nome_do_vertice(vertice),
        "coordenadas_vertice": [vertice.latitude, vertice.longitude],
        "distancia_m": distancia_m,
    }


# ---------------------------------------------------------------------------
# Área do mapa: textos de aviso
# ---------------------------------------------------------------------------

def motivo_fora_da_area(
    poi: Dict[str, Any],
    grafo: Grafo,
    limite_m: float = LIMITE_ASSOCIACAO_METROS
) -> Optional[str]:
    """
    None se o POI está dentro da área do mapa; senão, a explicação, por exemplo
    "fica a 4,97 km do cruzamento mais próximo do grafo (limite: 200 m)".
    Usada antes de salvar um local vindo da busca ou do cadastro manual.
    """
    _id_vertice, distancia_m = associar_poi_ao_vertice(poi, grafo)
    if distancia_m <= limite_m:
        return None
    return _explicar_distancia_ao_grafo(distancia_m, limite_m)


def legenda_pois_fora_da_area(
    quantidade_fora: int,
    quantidade_total: int,
    limite_m: float = LIMITE_ASSOCIACAO_METROS
) -> Optional[str]:
    """Legenda dos selects de origem e destino: quantos locais do catálogo ficaram de fora."""
    if quantidade_fora <= 0:
        return None
    if quantidade_fora == 1:
        ficaram, estao = "ficou", "está"
    else:
        ficaram, estao = "ficaram", "estão"
    return (
        f"{quantidade_fora} de {quantidade_total} locais do catálogo {ficaram} de fora da "
        f"seleção: {estao} a mais de {formatar_distancia(limite_m)} de qualquer cruzamento "
        "da área do mapa (ruas em cinza)."
    )


def aviso_poucos_pois_na_area(quantidade_na_area: int) -> Optional[str]:
    """Aviso mostrado no lugar dos selects quando não há dois POIs dentro da área do mapa."""
    if quantidade_na_area >= 2:
        return None
    situacao = "não tem nenhum local" if quantidade_na_area == 0 else "tem só 1 local"
    return (
        "Para calcular uma rota são necessários pelo menos dois locais dentro da área do "
        f"mapa (ruas em cinza), mas o catálogo {situacao} nessa área. Cadastre locais "
        "pela barra lateral (busca ou endereço manual)."
    )


def _explicar_distancia_ao_grafo(distancia_m: float, limite_m: float) -> str:
    return (
        f"fica a {formatar_distancia(distancia_m)} do cruzamento mais próximo do grafo "
        f"(limite: {formatar_distancia(limite_m)})"
    )


# ---------------------------------------------------------------------------
# Formatação no padrão brasileiro
# ---------------------------------------------------------------------------

def formatar_decimal(valor: float, casas: int) -> str:
    """Número com vírgula decimal e ponto nos milhares: (1234.5, 1) -> '1.234,5'."""
    return f"{valor:,.{casas}f}".translate(_TROCA_SEPARADORES)


def formatar_km(distancia_m: float) -> str:
    """Distância em metros exibida em km com duas casas: 600 -> '0,60 km'."""
    return f"{formatar_decimal(distancia_m / 1000.0, 2)} km"


def formatar_minutos(tempo_s: float) -> str:
    """Tempo em segundos exibido em minutos com uma casa: 72 -> '1,2 min'."""
    return f"{formatar_decimal(tempo_s / 60.0, 1)} min"


def formatar_reais(valor_reais: float) -> str:
    """Valor em Reais com duas casas: 0.0348 -> 'R$ 0,03'."""
    return f"R$ {formatar_decimal(valor_reais, 2)}"


def formatar_distancia(distancia_m: float) -> str:
    """Metros inteiros abaixo de 1 km ('85 m'); a partir daí, km com duas casas ('4,97 km')."""
    if round(distancia_m) < 1000:
        return f"{formatar_decimal(distancia_m, 0)} m"
    return formatar_km(distancia_m)
