"""
Módulo de dados viários e pontos de interesse (POIs).
Responsável pela leitura de dados locais, geolocalização (Haversine),
associação de POIs aos nós viários, busca via API (OpenStreetMap) e montagem do Grafo.
"""

import json
import math
import os
from typing import Any, Dict, List, Optional, Tuple

import requests

from grafo import Aresta, Grafo, Vertice

# Constantes padrão do projeto (conforme documentação em artefatos/planejamento)
VELOCIDADE_PADRAO_KMH = 30.0
CONSUMO_PADRAO_KML = 10.0
PRECO_PADRAO_GASOLINA = 5.80
RAIO_TERRA_METROS = 6371000.0

# Bounding box de Belo Horizonte - MG (abrangência ampla da cidade)
BBOX_BH = {
    "min_lat": -20.0600,
    "max_lat": -19.7500,
    "min_lon": -44.1000,
    "max_lon": -43.8500,
}

# Bounding box do bairro Coração Eucarístico (preservada para consultas locais)
BBOX_COREU = {
    "min_lat": -19.9320,
    "max_lat": -19.9180,
    "min_lon": -43.9960,
    "max_lon": -43.9750,
}


def calcular_distancia_haversine(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calcula a distância geodésica em metros entre duas coordenadas
    utilizando a fórmula de Haversine.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return RAIO_TERRA_METROS * c


def calcular_tempo_segundos(distancia_m: float, velocidade_kmh: float = VELOCIDADE_PADRAO_KMH) -> float:
    """
    Calcula o tempo estimado em segundos a partir da distância (m) e velocidade (km/h).
    tempo = distancia / (velocidade / 3.6)
    """
    if velocidade_kmh <= 0:
        raise ValueError("A velocidade deve ser estritamente positiva (> 0).")
    if distancia_m < 0:
        raise ValueError("A distância não pode ser negativa.")

    velocidade_ms = velocidade_kmh / 3.6
    return distancia_m / velocidade_ms


def calcular_custo_reais(
    distancia_m: float,
    consumo_kml: float = CONSUMO_PADRAO_KML,
    preco_combustivel: float = PRECO_PADRAO_GASOLINA
) -> float:
    """
    Calcula o custo financeiro estimado em Reais (R$) para o percurso do segmento.
    custo = (distancia_m / (1000.0 * consumo)) * preco
    """
    if consumo_kml <= 0:
        raise ValueError("Consumo do veículo deve ser positivo (> 0 km/l).")
    if preco_combustivel < 0:
        raise ValueError("Preço do combustível não pode ser negativo.")
    if distancia_m < 0:
        raise ValueError("A distância não pode ser negativa.")

    distancia_km = distancia_m / 1000.0
    litros = distancia_km / consumo_kml
    return litros * preco_combustivel


def carregar_mapa(caminho_mapa: str) -> Dict[str, Any]:
    """
    Carrega e valida o arquivo JSON com o snapshot viário.
    """
    if not os.path.exists(caminho_mapa):
        raise FileNotFoundError(f"Arquivo do mapa não encontrado: {caminho_mapa}")

    with open(caminho_mapa, "r", encoding="utf-8") as f:
        dados = json.load(f)

    if not isinstance(dados, dict):
        raise ValueError("Estrutura inválida do mapa: esperado objeto JSON raiz.")

    if "vertices" not in dados or "arestas" not in dados:
        raise ValueError("Arquivo de mapa deve conter as chaves 'vertices' e 'arestas'.")

    return dados


def carregar_pois(caminho_pois: str) -> List[Dict[str, Any]]:
    """
    Carrega o catálogo de pontos de interesse (POIs) salvos localmente.
    """
    if not os.path.exists(caminho_pois):
        raise FileNotFoundError(f"Arquivo de POIs não encontrado: {caminho_pois}")

    with open(caminho_pois, "r", encoding="utf-8") as f:
        pois = json.load(f)

    if not isinstance(pois, list):
        raise ValueError("Estrutura inválida de POIs: esperado array JSON.")

    for idx, poi in enumerate(pois):
        if not all(k in poi for k in ("id", "nome", "coordenadas")):
            raise ValueError(f"POI no índice {idx} está incompleto (faltam id, nome ou coordenadas).")

    return pois


def salvar_poi_cache(poi: Dict[str, Any], caminho_pois: str) -> bool:
    """
    Adiciona um novo POI ao arquivo de cache local caso ainda não exista.
    Retorna True se foi adicionado, False se já existia.
    """
    pois = carregar_pois(caminho_pois) if os.path.exists(caminho_pois) else []

    # Verifica se já existe por id ou pelo mesmo nome exato
    id_novo = str(poi.get("id", ""))
    nome_novo = str(poi.get("nome", "")).strip().lower()

    for existente in pois:
        if id_novo and existente.get("id") == id_novo:
            return False
        if existente.get("nome", "").strip().lower() == nome_novo:
            return False

    pois.append(poi)
    with open(caminho_pois, "w", encoding="utf-8") as f:
        json.dump(pois, f, indent=2, ensure_ascii=False)
    return True


def remover_poi_cache(identificador: str, caminho_pois: str) -> bool:
    """
    Remove um POI do arquivo de cache pelo 'id' ou pelo 'nome'.
    Retorna True se removeu com sucesso, False se o identificador não foi encontrado.
    """
    if not os.path.exists(caminho_pois):
        return False

    pois = carregar_pois(caminho_pois)
    alvo = identificador.strip().lower()

    pois_filtrados = [
        p for p in pois
        if p.get("id", "").strip().lower() != alvo and p.get("nome", "").strip().lower() != alvo
    ]

    if len(pois_filtrados) == len(pois):
        return False

    with open(caminho_pois, "w", encoding="utf-8") as f:
        json.dump(pois_filtrados, f, indent=2, ensure_ascii=False)
    return True


def buscar_poi_api(
    termo_busca: str,
    bbox: Optional[Dict[str, float]] = None,
    timeout_segundos: float = 5.0
) -> List[Dict[str, Any]]:
    """
    Consulta a API pública do OpenStreetMap (Nominatim) para buscar pontos de interesse
    ou endereços em Belo Horizonte, retornando nome, categoria, endereço e coordenadas.
    Possui tratamento gracioso para falha de conexão / timeout (fallback offline).
    """
    if not termo_busca or not termo_busca.strip():
        return []

    if bbox is None:
        bbox = BBOX_BH

    url = "https://nominatim.openstreetmap.org/search"
    viewbox = f"{bbox['min_lon']},{bbox['max_lat']},{bbox['max_lon']},{bbox['min_lat']}"

    parametros = {
        "q": termo_busca,
        "format": "json",
        "addressdetails": 1,
        "bounded": 1,
        "viewbox": viewbox,
        "limit": 8
    }

    headers = {
        "User-Agent": "TrabalhoPraticoGrafos-PUCMinas/1.0 (academic-project)"
    }

    try:
        resposta = requests.get(url, params=parametros, headers=headers, timeout=timeout_segundos)
        if resposta.status_code != 200:
            return []

        itens = resposta.json()
        resultados = []
        for idx, item in enumerate(itens):
            lat = float(item["lat"])
            lon = float(item["lon"])
            addr = item.get("address", {})
            rua = addr.get("road", "")
            numero = addr.get("house_number", "")
            bairro = addr.get("suburb", addr.get("neighbourhood", addr.get("city_district", "")))
            cidade = addr.get("city", "Belo Horizonte")

            partes_end = [p for p in [f"{rua}, {numero}".strip(", "), bairro, cidade] if p]
            end_formatado = " - ".join(partes_end) if partes_end else item.get("display_name", "")

            nome_base = item.get("display_name", termo_busca).split(",")[0].strip()
            if bairro and bairro.lower() not in nome_base.lower():
                nome_exibicao = f"{nome_base} ({bairro})"
            elif rua and rua.lower() not in nome_base.lower():
                nome_exibicao = f"{nome_base} ({rua})"
            else:
                nome_exibicao = nome_base

            osm_id = item.get("osm_id", f"{idx}_{int(lat * 1000)}")
            osm_type = item.get("osm_type", "poi")

            resultados.append({
                "id": f"osm_{osm_type}_{osm_id}",
                "nome": nome_exibicao,
                "categoria": item.get("type", "ponto"),
                "coordenadas": [lat, lon],
                "endereco": end_formatado
            })
        return resultados
    except Exception:
        # Em caso de erro de rede ou timeout, retorna lista vazia de forma segura
        return []


def geocodificar_endereco(
    endereco: str,
    timeout_segundos: float = 5.0
) -> Optional[Dict[str, Any]]:
    """
    Busca coordenadas a partir de um endereço textual em Belo Horizonte.
    Retorna o dicionário do POI montado ou None se não encontrado.
    """
    if not endereco or not endereco.strip():
        return None

    termo = endereco.strip()
    if "belo horizonte" not in termo.lower() and "bh" not in termo.lower():
        termo += ", Belo Horizonte, MG"

    url = "https://nominatim.openstreetmap.org/search"
    parametros = {
        "q": termo,
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }
    headers = {
        "User-Agent": "TrabalhoPraticoGrafos-PUCMinas/1.0 (academic-project)"
    }

    try:
        resp = requests.get(url, params=parametros, headers=headers, timeout=timeout_segundos)
        if resp.status_code == 200:
            dados = resp.json()
            if dados:
                item = dados[0]
                lat = float(item["lat"])
                lon = float(item["lon"])
                addr = item.get("address", {})
                rua = addr.get("road", "")
                numero = addr.get("house_number", "")
                bairro = addr.get("suburb", addr.get("neighbourhood", ""))
                cidade = addr.get("city", "Belo Horizonte")

                partes_end = [p for p in [f"{rua}, {numero}".strip(", "), bairro, cidade] if p]
                end_formatado = " - ".join(partes_end) if partes_end else item.get("display_name", endereco)

                return {
                    "id": f"end_{item.get('osm_id', int(abs(lat * 10000)))}",
                    "nome": item.get("display_name", endereco).split(",")[0].strip(),
                    "categoria": "endereco",
                    "coordenadas": [lat, lon],
                    "endereco": end_formatado
                }
    except Exception:
        pass
    return None


def associar_poi_ao_no_mais_proximo(
    poi: Dict[str, Any],
    vertices: Dict[str, Vertice]
) -> str:
    """
    Localiza o vértice do grafo viário com menor distância geodésica até o POI.
    Retorna o id do vértice mais próximo.
    """
    if not vertices:
        raise ValueError("Dicionário de vértices está vazio.")

    coord_poi = poi.get("coordenadas")
    if not coord_poi or len(coord_poi) < 2:
        raise ValueError(f"POI '{poi.get('nome')}' possui coordenadas inválidas.")

    lat_poi, lon_poi = coord_poi[0], coord_poi[1]

    menor_distancia = float("inf")
    no_mais_proximo_id = ""

    for v_id, vertice in vertices.items():
        dist = calcular_distancia_haversine(
            lat_poi, lon_poi,
            vertice.latitude, vertice.longitude
        )
        if dist < menor_distancia:
            menor_distancia = dist
            no_mais_proximo_id = v_id

    return no_mais_proximo_id


def construir_grafo(
    dados_mapa: Dict[str, Any],
    dados_pois: Optional[List[Dict[str, Any]]] = None
) -> Grafo:
    """
    Instancia o modelo de Grafo a partir dos dados do mapa e associa os POIs.
    Respeita sentidos de circulação (oneway), limites de velocidade e múltiplos critérios.
    """
    grafo = Grafo()

    # 1. Adicionar vértices do mapa
    for v_dict in dados_mapa.get("vertices", []):
        v = Vertice(
            id_vertice=v_dict["id"],
            latitude=v_dict["latitude"],
            longitude=v_dict["longitude"],
            nome=v_dict.get("nome")
        )
        grafo.adicionarVertice(v)

    # 2. Adicionar arestas do mapa
    for e_dict in dados_mapa.get("arestas", []):
        id_origem = e_dict["origem"]
        id_destino = e_dict["destino"]

        origem = grafo.getVertice(id_origem)
        destino = grafo.getVertice(id_destino)

        if not origem:
            raise ValueError(f"Origem desconhecida '{id_origem}' na aresta '{e_dict.get('id')}'.")
        if not destino:
            raise ValueError(f"Destino desconhecido '{id_destino}' na aresta '{e_dict.get('id')}'.")

        # Distância calculada via Haversine
        distancia_m = calcular_distancia_haversine(
            origem.latitude, origem.longitude,
            destino.latitude, destino.longitude
        )

        velocidade_kmh = float(e_dict.get("velocidade_kmh", VELOCIDADE_PADRAO_KMH))
        tempo_s = calcular_tempo_segundos(distancia_m, velocidade_kmh)
        custo_rs = calcular_custo_reais(distancia_m)

        # Aresta no sentido direto
        aresta_direta = Aresta(
            id_aresta=e_dict["id"],
            origem=origem,
            destino=destino,
            distanciaMetros=distancia_m,
            velocidadeKmH=velocidade_kmh,
            tempoSegundos=tempo_s,
            custoReais=custo_rs
        )
        grafo.adicionarAresta(aresta_direta)

        # Se for mão dupla, cria também a aresta no sentido oposto
        if not e_dict.get("oneway", False):
            aresta_reversa = Aresta(
                id_aresta=f"{e_dict['id']}_rev",
                origem=destino,
                destino=origem,
                distanciaMetros=distancia_m,
                velocidadeKmH=velocidade_kmh,
                tempoSegundos=tempo_s,
                custoReais=custo_rs
            )
            grafo.adicionarAresta(aresta_reversa)

    # 3. Associar nós dos POIs se fornecidos
    if dados_pois:
        for poi in dados_pois:
            if not poi.get("no_viario_associado"):
                poi["no_viario_associado"] = associar_poi_ao_no_mais_proximo(poi, grafo.vertices)

    return grafo
