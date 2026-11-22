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
    geocodificar_endereco,
    LIMITE_ASSOCIACAO_METROS,
    RAIO_TERRA_METROS,
    associar_poi_ao_vertice,
    calcular_bbox_area,
    poi_dentro_da_area,
    separar_pois_por_area
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


# ---------------------------------------------------------------------------
# Área do mapa: POI -> vértice com distância, limite de associação e bbox de busca
# ---------------------------------------------------------------------------

# Coordenadas da Praça da Liberdade no catálogo: fora do Coração Eucarístico
PRACA_DA_LIBERDADE = {
    "id": "praca_da_liberdade",
    "nome": "Praça da Liberdade (Circuito Cultural)",
    "coordenadas": [-19.932, -43.9378],
}


@pytest.fixture(scope="module")
def grafo_real():
    return construir_grafo(carregar_mapa(ARQUIVO_MAPA))


def _poi_deslocado(vertice, nome, norte_m=0.0, leste_m=0.0):
    """POI a norte_m metros ao norte e leste_m metros a leste do vértice (negativo = sul/oeste)."""
    latitude = vertice.latitude + _math.degrees(norte_m / RAIO_TERRA_METROS)
    longitude = vertice.longitude + _math.degrees(
        leste_m / (RAIO_TERRA_METROS * _math.cos(_math.radians(vertice.latitude)))
    )
    return {"id": nome, "nome": nome, "coordenadas": [latitude, longitude]}


def test_poi_nas_coordenadas_de_um_vertice_tem_distancia_zero(grafo_real):
    for vertice in grafo_real.vertices.values():
        poi = {"id": "p", "nome": "Ponto", "coordenadas": [vertice.latitude, vertice.longitude]}
        id_vertice, distancia_m = associar_poi_ao_vertice(poi, grafo_real)
        assert id_vertice == vertice.id
        assert distancia_m == pytest.approx(0.0, abs=1e-6)


def _vertice_mais_ao_norte(grafo):
    # andando para o norte a partir dele, nenhum outro vértice fica mais perto
    return max(grafo.vertices.values(), key=lambda v: v.latitude)


def test_associacao_usa_coordenadas_e_ignora_no_viario_associado(grafo_real):
    # o campo do catálogo está desatualizado; aqui ele aponta para outro vértice do grafo
    no_local, outro = list(grafo_real.vertices.values())[:2]
    poi = {
        "id": "poi_teste",
        "nome": "Local de teste",
        "coordenadas": [no_local.latitude, no_local.longitude],
        "no_viario_associado": outro.id,
    }
    copia = dict(poi)
    assert associar_poi_ao_vertice(poi, grafo_real)[0] == no_local.id
    assert poi == copia  # a função não altera o POI


def test_praca_da_liberdade_fora_da_area(grafo_real):
    _id_vertice, distancia_m = associar_poi_ao_vertice(PRACA_DA_LIBERDADE, grafo_real)
    assert distancia_m > 4000  # a Praça da Liberdade fica a uns 5 km do Coração Eucarístico
    assert poi_dentro_da_area(PRACA_DA_LIBERDADE, grafo_real) is False
    assert separar_pois_por_area([PRACA_DA_LIBERDADE], grafo_real) == ([], [PRACA_DA_LIBERDADE])


def test_puc_do_catalogo_fica_dentro_da_area(grafo_real):
    # coordenadas do POI da PUC no catálogo (Cantina): a via interna do campus deixa o
    # vértice mais próximo a menos de 200 m; a Av. Dom José Gaspar passa a 209 m
    puc = {"id": "puc_minas_coreu", "nome": "PUC Minas", "coordenadas": [-19.9229, -43.9926]}
    assert poi_dentro_da_area(puc, grafo_real)


def test_underground_fica_dentro_da_area(grafo_real):
    # "Underground Black Pub", na Av. Itaú (bairro Dom Cabral), com as coordenadas do OSM:
    # o recorte cobre o lado oeste do campus até ele
    pub = {"id": "underground", "nome": "Underground Black Pub", "coordenadas": [-19.91908, -43.99452]}
    assert poi_dentro_da_area(pub, grafo_real)


def test_limite_de_associacao_e_de_200_metros(grafo_real):
    assert LIMITE_ASSOCIACAO_METROS == 200
    norte = _vertice_mais_ao_norte(grafo_real)
    assert poi_dentro_da_area(_poi_deslocado(norte, "a 199,9 m", norte_m=199.9), grafo_real)
    assert not poi_dentro_da_area(_poi_deslocado(norte, "a 200,1 m", norte_m=200.1), grafo_real)
    # exatamente no limite ainda conta como dentro
    no_limite = _poi_deslocado(norte, "no limite", norte_m=200.0)
    id_vertice, distancia_m = associar_poi_ao_vertice(no_limite, grafo_real)
    assert id_vertice == norte.id
    assert distancia_m == pytest.approx(200.0, abs=1e-6)
    assert poi_dentro_da_area(no_limite, grafo_real, limite_m=distancia_m)


def test_separar_pois_por_area_mantem_a_ordem(grafo_real):
    norte = _vertice_mais_ao_norte(grafo_real)
    pois = [
        _poi_deslocado(norte, "a 250 m", norte_m=250.0),
        _poi_deslocado(norte, "no vértice"),
        _poi_deslocado(norte, "a 199 m", norte_m=199.0),
        PRACA_DA_LIBERDADE,
    ]
    dentro, fora = separar_pois_por_area(pois, grafo_real)
    assert [p["id"] for p in dentro] == ["no vértice", "a 199 m"]
    assert [p["id"] for p in fora] == ["a 250 m", "praca_da_liberdade"]


def test_bbox_da_area_contem_todos_os_vertices(grafo_real):
    bbox = calcular_bbox_area(grafo_real)
    for vertice in carregar_mapa(ARQUIVO_MAPA)["vertices"]:
        assert bbox["min_lat"] < vertice["latitude"] < bbox["max_lat"]
        assert bbox["min_lon"] < vertice["longitude"] < bbox["max_lon"]


def test_bbox_da_area_tem_margem_do_limite_de_associacao(grafo_real):
    bbox = calcular_bbox_area(grafo_real)
    vertices = list(grafo_real.vertices.values())
    mais_ao_norte = max(vertices, key=lambda v: v.latitude)
    mais_a_leste = max(vertices, key=lambda v: v.longitude)
    margem_norte = calcular_distancia_haversine(
        mais_ao_norte.latitude, mais_ao_norte.longitude, bbox["max_lat"], mais_ao_norte.longitude
    )
    margem_leste = calcular_distancia_haversine(
        mais_a_leste.latitude, mais_a_leste.longitude, mais_a_leste.latitude, bbox["max_lon"]
    )
    assert margem_norte == pytest.approx(LIMITE_ASSOCIACAO_METROS, abs=0.5)
    assert margem_leste == pytest.approx(LIMITE_ASSOCIACAO_METROS, abs=0.5)


def test_todo_ponto_dentro_da_area_cai_na_bbox_de_busca(grafo_real):
    # a busca online nunca pode cortar um local que os selects aceitariam
    bbox = calcular_bbox_area(grafo_real)
    distancia_m = LIMITE_ASSOCIACAO_METROS * 0.999
    for vertice in grafo_real.vertices.values():
        for angulo in range(0, 360, 45):
            norte_m = distancia_m * _math.cos(_math.radians(angulo))
            leste_m = distancia_m * _math.sin(_math.radians(angulo))
            lat, lon = _poi_deslocado(vertice, "p", norte_m, leste_m)["coordenadas"]
            assert bbox["min_lat"] <= lat <= bbox["max_lat"]
            assert bbox["min_lon"] <= lon <= bbox["max_lon"]


def test_geocodificar_endereco_restringe_a_busca_a_bbox(monkeypatch):
    parametros_enviados = []

    class RespostaSemResultados:
        status_code = 200

        def json(self):
            return []

    def get_falso(url, params=None, headers=None, timeout=None):
        parametros_enviados.append(params)
        return RespostaSemResultados()

    monkeypatch.setattr("mapa.requests.get", get_falso)
    bbox = {"min_lat": -19.93, "max_lat": -19.92, "min_lon": -43.99, "max_lon": -43.98}

    assert geocodificar_endereco("Rua Dom José Gaspar, 500", bbox=bbox) is None
    assert geocodificar_endereco("Rua Dom José Gaspar, 500", bbox=bbox, somente_na_bbox=False) is None
    assert geocodificar_endereco("Rua Dom José Gaspar, 500") is None
    restrita, preferencia, sem_bbox = parametros_enviados
    assert restrita["bounded"] == 1
    assert restrita["viewbox"] == "-43.99,-19.92,-43.98,-19.93"
    # só preferência: o resultado de fora volta e o app avisa onde ele fica
    assert preferencia["viewbox"] == restrita["viewbox"] and "bounded" not in preferencia
    assert "viewbox" not in sem_bbox and "bounded" not in sem_bbox
