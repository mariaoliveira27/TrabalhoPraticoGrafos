"""
Bateria de testes automatizados para o módulo mapa.py e dados viários.
"""

import json
import os
import tempfile
import pytest

from grafo import Vertice
from mapa import (
    calcular_custo_reais,
    calcular_distancia_haversine,
    calcular_tempo_segundos,
    carregar_mapa,
    carregar_pois,
    salvar_poi_cache,
    remover_poi_cache,
    associar_poi_ao_no_mais_proximo,
    construir_grafo,
    buscar_poi_api,
    geocodificar_endereco
)


CAMINHO_DADOS = os.path.join(os.path.dirname(__file__), "..", "dados")
ARQUIVO_MAPA = os.path.join(CAMINHO_DADOS, "mapa.json")
ARQUIVO_POIS = os.path.join(CAMINHO_DADOS, "pontos_interesse.json")


def test_haversine_distancia_conhecida():
    """
    Testa a precisão da fórmula de Haversine.
    Distância entre PUC Coreu (-19.9229, -43.9926) e Praça da Federação (-19.9242, -43.9930)
    é de aproximadamente 150 metros.
    """
    distancia = calcular_distancia_haversine(
        -19.9229, -43.9926,
        -19.9242, -43.9930
    )
    assert 130.0 < distancia < 170.0


def test_haversine_mesmo_ponto():
    """Distância de um ponto para ele mesmo deve ser zero."""
    dist = calcular_distancia_haversine(-19.9229, -43.9926, -19.9229, -43.9926)
    assert dist == pytest.approx(0.0, abs=1e-5)


def test_tempo_calculo():
    """
    Testa o cálculo do tempo em segundos:
    1000 metros a 36 km/h (10 m/s) deve resultar em exatamente 100 segundos.
    """
    tempo = calcular_tempo_segundos(distancia_m=1000.0, velocidade_kmh=36.0)
    assert tempo == pytest.approx(100.0)


def test_tempo_velocidade_invalida():
    """Velocidade <= 0 deve disparar ValueError."""
    with pytest.raises(ValueError):
        calcular_tempo_segundos(distancia_m=500.0, velocidade_kmh=0)

    with pytest.raises(ValueError):
        calcular_tempo_segundos(distancia_m=500.0, velocidade_kmh=-20.0)


def test_custo_calculo():
    """
    Testa a fórmula de custo financeiro:
    (distancia / (1000 * 10)) * 5.80
    Para 10 km (10000 m), consumo 10 km/l e R$ 5,80/l, custo = R$ 5,80.
    """
    custo = calcular_custo_reais(
        distancia_m=10000.0,
        consumo_kml=10.0,
        preco_combustivel=5.80
    )
    assert custo == pytest.approx(5.80)


def test_carregar_mapa_sucesso():
    """Verifica se o snapshot mapa.json carrega corretamente e possui a estrutura esperada."""
    mapa = carregar_mapa(ARQUIVO_MAPA)
    assert "vertices" in mapa
    assert "arestas" in mapa
    assert len(mapa["vertices"]) >= 10
    assert len(mapa["arestas"]) >= 10


def test_carregar_mapa_inexistente():
    """Verifica se arquivo inexistente levanta FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        carregar_mapa("caminho_inexistente_123.json")


def test_carregar_pois_offline():
    """Verifica se há pelo menos 10 POIs pré-carregados para uso offline."""
    pois = carregar_pois(ARQUIVO_POIS)
    assert len(pois) >= 10
    for poi in pois:
        assert "id" in poi
        assert "nome" in poi
        assert len(poi["coordenadas"]) == 2
        lat, lon = poi["coordenadas"]
        assert -90.0 <= lat <= 90.0
        assert -180.0 <= lon <= 180.0


def test_associar_poi_ao_no_mais_proximo():
    """Testa a lógica de snapping de um POI para o vértice mais próximo."""
    v1 = Vertice("v1", latitude=-19.9200, longitude=-43.9900, nome="Ponto A")
    v2 = Vertice("v2", latitude=-19.9250, longitude=-43.9950, nome="Ponto B")
    vertices = {"v1": v1, "v2": v2}

    # POI muito próximo de v1
    poi = {
        "id": "poi_teste",
        "nome": "Loja Teste",
        "coordenadas": [-19.9201, -43.9901]
    }
    no_encontrado = associar_poi_ao_no_mais_proximo(poi, vertices)
    assert no_encontrado == "v1"


def test_construir_grafo_e_oneway():
    """
    Testa a construção do Grafo garantindo:
    - Vértices carregados corretamente
    - Ruas de mão única (oneway=True) geram 1 aresta
    - Ruas de mão dupla (oneway=False) geram 2 arestas direcionadas
    """
    dados_mapa = {
        "vertices": [
            {"id": "A", "latitude": -19.9200, "longitude": -43.9900},
            {"id": "B", "latitude": -19.9210, "longitude": -43.9910},
            {"id": "C", "latitude": -19.9220, "longitude": -43.9920}
        ],
        "arestas": [
            {"id": "e1", "origem": "A", "destino": "B", "velocidade_kmh": 30.0, "oneway": True},
            {"id": "e2", "origem": "B", "destino": "C", "velocidade_kmh": 40.0, "oneway": False}
        ]
    }

    grafo = construir_grafo(dados_mapa)
    assert grafo.quantidade_vertices() == 3

    # A -> B é mão única: apenas 1 aresta saindo de A para B
    adj_A = grafo.getAdjacencias("A")
    assert len(adj_A) == 1
    assert adj_A[0].destino.id == "B"

    # B -> C é mão dupla: saindo de B deve ter B->C, e saindo de C deve ter C->B
    adj_B = [a.destino.id for a in grafo.getAdjacencias("B")]
    assert "C" in adj_B

    adj_C = [a.destino.id for a in grafo.getAdjacencias("C")]
    assert "B" in adj_C


def test_salvar_poi_cache_temporario():
    """Testa salvar um POI novo no cache sem duplicar."""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as tmp:
        tmp.write("[]")
        tmp_path = tmp.name

    try:
        novo_poi = {
            "id": "novo_cafe",
            "nome": "Café do Coreu",
            "categoria": "alimentacao",
            "coordenadas": [-19.9230, -43.9920]
        }
        # Adiciona primeira vez: deve retornar True
        adicionado = salvar_poi_cache(novo_poi, tmp_path)
        assert adicionado is True

        # Tenta adicionar novamente o mesmo POI: deve retornar False
        adicionado_novamente = salvar_poi_cache(novo_poi, tmp_path)
        assert adicionado_novamente is False

        # Verifica conteúdo salvo
        salvos = carregar_pois(tmp_path)
        assert len(salvos) == 1
        assert salvos[0]["id"] == "novo_cafe"
        # Testa remoção do POI
        removido = remover_poi_cache("Café do Coreu", tmp_path)
        assert removido is True

        # Verifica se lista ficou vazia
        salvos_apos_remocao = carregar_pois(tmp_path)
        assert len(salvos_apos_remocao) == 0

        # Tentar remover novamente deve retornar False
        removido_de_novo = remover_poi_cache("Café do Coreu", tmp_path)
        assert removido_de_novo is False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_buscar_poi_api_offline_fallback():
    """
    Testa se a busca na API não quebra quando uma busca inválida ou offline é simulada,
    retornando lista vazia com segurança.
    """
    res = buscar_poi_api("", timeout_segundos=0.1)
    assert res == []


def test_geocodificar_endereco_vazio():
    """Testa se endereço vazio retorna None com segurança."""
    res = geocodificar_endereco("", timeout_segundos=0.1)
    assert res is None



# ---------------------------------------------------------------------------
# Testes do modelo do grafo (grafo.py) — Issue 04
# ---------------------------------------------------------------------------

import math as _math

from grafo import (
    Aresta,
    Grafo,
    ResultadoRota,
    CRITERIO_CUSTO,
    CRITERIO_DISTANCIA,
    CRITERIO_TEMPO,
    SITUACAO_ENCONTRADA,
    SITUACAO_INALCANCAVEL,
    SITUACAO_INVALIDA,
    normalizarCriterio,
)


def _vertices_abc():
    return (
        Vertice("A", -19.9200, -43.9900),
        Vertice("B", -19.9210, -43.9910),
        Vertice("C", -19.9220, -43.9920),
    )


def _aresta(id_aresta, origem, destino, dist=100.0, vel=30.0, tempo=12.0, custo=0.058):
    return Aresta(id_aresta, origem, destino, dist, vel, tempo, custo)


@pytest.mark.parametrize("lat, lon", [
    (91.0, 0.0), (-91.0, 0.0), (0.0, 181.0), (0.0, -181.0),
    (float("nan"), 0.0), (0.0, float("inf")), ("abc", 0.0),
])
def test_vertice_coordenadas_invalidas(lat, lon):
    with pytest.raises(ValueError):
        Vertice("X", lat, lon)


def test_vertice_id_vazio():
    with pytest.raises(ValueError):
        Vertice("  ", 0.0, 0.0)


def test_aresta_get_peso_por_criterio():
    a, b, _ = _vertices_abc()
    aresta = _aresta("e1", a, b, dist=150.0, tempo=18.0, custo=0.087)
    assert aresta.getPeso(CRITERIO_DISTANCIA) == 150.0
    assert aresta.getPeso(CRITERIO_TEMPO) == 18.0
    assert aresta.getPeso(CRITERIO_CUSTO) == 0.087
    assert aresta.getPeso("  Tempo ") == 18.0


@pytest.mark.parametrize("criterio", ["velocidade", "", None, 3])
def test_aresta_criterio_invalido(criterio):
    a, b, _ = _vertices_abc()
    with pytest.raises(ValueError):
        _aresta("e1", a, b).getPeso(criterio)


@pytest.mark.parametrize("campo, valor", [
    ("dist", -1.0), ("dist", float("nan")), ("dist", float("inf")),
    ("vel", 0.0), ("vel", -10.0), ("vel", float("nan")),
    ("tempo", -0.1), ("tempo", float("inf")),
    ("custo", -0.01), ("custo", float("nan")),
])
def test_aresta_pesos_invalidos(campo, valor):
    a, b, _ = _vertices_abc()
    with pytest.raises(ValueError):
        _aresta("e1", a, b, **{campo: valor})


def test_aresta_peso_zero_permitido():
    a, b, _ = _vertices_abc()
    aresta = _aresta("e1", a, b, dist=0.0, tempo=0.0, custo=0.0)
    assert aresta.getPeso(CRITERIO_DISTANCIA) == 0.0


def test_aresta_exige_vertices():
    a, _, _ = _vertices_abc()
    with pytest.raises(TypeError):
        _aresta("e1", a, "B")


def test_grafo_dirigido_mao_unica():
    a, b, _ = _vertices_abc()
    grafo = Grafo()
    grafo.adicionarAresta(_aresta("e1", a, b))
    assert [x.destino.id for x in grafo.getAdjacencias("A")] == ["B"]
    assert grafo.getAdjacencias("B") == []
    assert grafo.quantidade_vertices() == 2
    assert grafo.quantidade_arestas() == 1


def test_grafo_arestas_paralelas_identificaveis():
    a, b, _ = _vertices_abc()
    grafo = Grafo()
    grafo.adicionarAresta(_aresta("curta", a, b, dist=100.0))
    grafo.adicionarAresta(_aresta("longa", a, b, dist=300.0))
    paralelas = grafo.getArestasEntre("A", "B")
    assert {x.id for x in paralelas} == {"curta", "longa"}
    assert grafo.getAresta("longa").distanciaMetros == 300.0
    assert grafo.quantidade_arestas() == 2


def test_grafo_rejeita_id_de_aresta_repetido():
    a, b, c = _vertices_abc()
    grafo = Grafo()
    grafo.adicionarAresta(_aresta("e1", a, b))
    with pytest.raises(ValueError):
        grafo.adicionarAresta(_aresta("e1", b, c))
    assert grafo.quantidade_arestas() == 1


def test_grafo_vertice_repetido():
    grafo = Grafo()
    grafo.adicionarVertice(Vertice("A", -19.92, -43.99))
    grafo.adicionarVertice(Vertice("A", -19.92, -43.99))  # mesmo vértice: sem efeito
    assert grafo.quantidade_vertices() == 1
    with pytest.raises(ValueError):
        grafo.adicionarVertice(Vertice("A", -19.93, -43.99))


def test_grafo_vertice_inexistente():
    grafo = Grafo()
    assert grafo.getVertice("Z") is None
    assert not grafo.existeVertice("Z")
    assert grafo.getAdjacencias("Z") == []


def test_resultado_a_partir_do_caminho_soma_pesos():
    a, b, c = _vertices_abc()
    caminho = [
        _aresta("e1", a, b, dist=100.0, tempo=12.0, custo=0.058),
        _aresta("e2", b, c, dist=250.0, tempo=22.5, custo=0.145),
    ]
    resultado = ResultadoRota.aPartirDoCaminho(caminho, nosExpandidos=3)
    assert resultado.situacao == SITUACAO_ENCONTRADA
    assert resultado.foiEncontrada()
    assert resultado.distanciaTotalMetros == 350.0
    assert resultado.tempoTotalSegundos == 34.5
    assert _math.isclose(resultado.custoTotalReais, 0.203)
    assert resultado.getTotal(CRITERIO_DISTANCIA) == 350.0
    assert resultado.getDistanciaKm() == 0.35
    assert resultado.getTempoMinutos() == 34.5 / 60
    assert [v.id for v in resultado.getVerticesCaminho()] == ["A", "B", "C"]
    assert resultado.nosExpandidos == 3


def test_resultado_origem_igual_destino():
    resultado = ResultadoRota.aPartirDoCaminho([], nosExpandidos=1)
    assert resultado.foiEncontrada()
    assert resultado.distanciaTotalMetros == 0.0
    assert resultado.tempoTotalSegundos == 0.0
    assert resultado.custoTotalReais == 0.0
    assert resultado.getVerticesCaminho() == []


def test_resultado_inalcancavel_e_invalida():
    inalcancavel = ResultadoRota.inalcancavel(nosExpandidos=4)
    invalida = ResultadoRota.invalida()
    assert inalcancavel.situacao == SITUACAO_INALCANCAVEL
    assert invalida.situacao == SITUACAO_INVALIDA
    for resultado in (inalcancavel, invalida):
        assert not resultado.foiEncontrada()
        assert resultado.caminho == []
        assert resultado.distanciaTotalMetros is None
        assert resultado.getDistanciaKm() is None
        assert resultado.getTempoMinutos() is None
    assert inalcancavel.nosExpandidos == 4


def test_resultado_rejeita_estados_incoerentes():
    a, b, c = _vertices_abc()
    with pytest.raises(ValueError):
        ResultadoRota("achou", [])
    with pytest.raises(ValueError):
        ResultadoRota(SITUACAO_ENCONTRADA, [], 1.0, None, 1.0)
    with pytest.raises(ValueError):
        ResultadoRota(SITUACAO_INALCANCAVEL, [_aresta("e1", a, b)])
    with pytest.raises(ValueError):
        ResultadoRota(SITUACAO_INVALIDA, [], distanciaTotalMetros=10.0)
    with pytest.raises(ValueError):  # caminho descontínuo: A->B seguido de A->C
        ResultadoRota.aPartirDoCaminho([_aresta("e1", a, b), _aresta("e2", a, c)])
    with pytest.raises(ValueError):
        ResultadoRota.inalcancavel(nosExpandidos=-1)


def test_resultado_repr():
    texto = repr(ResultadoRota.aPartirDoCaminho([]))
    assert "situacao='encontrada'" in texto
    assert "custo=R$0.0" in texto


def test_construir_grafo_com_dados_reais():
    """O snapshot do projeto deve montar um grafo válido no novo modelo."""
    grafo = construir_grafo(carregar_mapa(ARQUIVO_MAPA))
    assert grafo.quantidade_vertices() > 0
    assert grafo.quantidade_arestas() > 0
    for aresta in grafo.getArestas():
        for criterio in (CRITERIO_DISTANCIA, CRITERIO_TEMPO, CRITERIO_CUSTO):
            peso = aresta.getPeso(criterio)
            assert _math.isfinite(peso) and peso >= 0
