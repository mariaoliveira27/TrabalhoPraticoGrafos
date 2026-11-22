"""
Testes de apoio_interface.py: a lógica que app.py usa, sem Streamlit e sem rede.

    python -m pytest codigo/tests/test_apoio_interface.py -v

Os POIs são montados a partir dos vértices de dados/mapa.json, deslocados alguns metros,
para os testes não dependerem do catálogo (que o app altera ao salvar ou remover locais).
"""

import math
import os

import pytest

from apoio_interface import (
    ALGORITMOS,
    MOTIVO_FORA_DA_AREA,
    MOTIVO_MESMO_LOCAL,
    MOTIVO_MESMO_VERTICE,
    ROTULOS_CRITERIOS,
    aviso_poucos_pois_na_area,
    calcular_rota_entre_pois,
    formatar_decimal,
    formatar_distancia,
    formatar_km,
    formatar_minutos,
    formatar_reais,
    legenda_pois_fora_da_area,
    limites_do_enquadramento,
    limites_dos_pontos,
    motivo_fora_da_area,
    parametros_da_selecao,
    preparar_pedido_rota,
    rota_corresponde_a_selecao,
    rotulo_para_criterio,
    trechos_do_mapa,
)
from grafo import (
    CRITERIO_CUSTO,
    CRITERIO_DISTANCIA,
    CRITERIO_TEMPO,
    CRITERIOS_VALIDOS,
    SITUACAO_ENCONTRADA,
    SITUACAO_INVALIDA,
)
from mapa import RAIO_TERRA_METROS, associar_poi_ao_vertice, carregar_mapa, construir_grafo
from rotas import calcularRotaBellmanFord, calcularRotaDijkstra

ARQUIVO_MAPA = os.path.join(os.path.dirname(__file__), "..", "dados", "mapa.json")

# Ligados pela R. Coração Eucarístico de Jesus, de mão dupla nesse trecho, e a mais de
# 100 m de qualquer outro vértice (um POI a 20 m deles continua associado a eles)
VERTICE_A = "no_lucio_coracao"
VERTICE_B = "no_rotatoria_dom_serafim"

# Coordenadas do catálogo; os dois caíam no mesmo vértice, a quilômetros de distância
PRACA_DA_LIBERDADE = {
    "id": "praca_da_liberdade",
    "nome": "Praça da Liberdade (Circuito Cultural)",
    "coordenadas": [-19.932, -43.9378],
}
MERCADO_CENTRAL = {
    "id": "mercado_central",
    "nome": "Mercado Central de Belo Horizonte",
    "coordenadas": [-19.925, -43.9415],
}


@pytest.fixture(scope="module")
def grafo_real():
    grafo = construir_grafo(carregar_mapa(ARQUIVO_MAPA))
    # premissas dos testes abaixo sobre o mapa
    assert grafo.getArestasEntre(VERTICE_A, VERTICE_B) and grafo.getArestasEntre(VERTICE_B, VERTICE_A)
    return grafo


def poi_perto_do_vertice(grafo, id_vertice, nome, norte_m=0.0, leste_m=0.0):
    """POI a norte_m metros ao norte e leste_m metros a leste do vértice (negativo = sul/oeste)."""
    vertice = grafo.getVertice(id_vertice)
    latitude = vertice.latitude + math.degrees(norte_m / RAIO_TERRA_METROS)
    longitude = vertice.longitude + math.degrees(
        leste_m / (RAIO_TERRA_METROS * math.cos(math.radians(vertice.latitude)))
    )
    return {"id": nome.lower().replace(" ", "_"), "nome": nome, "coordenadas": [latitude, longitude]}


@pytest.fixture
def lanchonete(grafo_real):
    return poi_perto_do_vertice(grafo_real, VERTICE_A, "Lanchonete")


@pytest.fixture
def banca(grafo_real):
    return poi_perto_do_vertice(grafo_real, VERTICE_B, "Banca da Praça", leste_m=-20.0)


@pytest.fixture
def dois_pois_no_mesmo_vertice(grafo_real):
    # ~20 m ao norte e ~20 m a oeste da rotatória
    return (
        poi_perto_do_vertice(grafo_real, VERTICE_B, "Padaria", norte_m=20.0),
        poi_perto_do_vertice(grafo_real, VERTICE_B, "Farmácia", leste_m=-20.0),
    )


# ---------------------------------------------------------------------------
# Rótulos da interface -> critérios do grafo (bug 1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rotulo, criterio", [
    ("Distância", CRITERIO_DISTANCIA),
    ("Tempo", CRITERIO_TEMPO),
    ("Custo", CRITERIO_CUSTO),
])
def test_rotulo_da_interface_vira_criterio(rotulo, criterio):
    assert rotulo_para_criterio(rotulo) == criterio


def test_selects_mostram_rotulos_convertiveis():
    # o app monta os selects com list(ROTULOS_CRITERIOS) e list(ALGORITMOS)
    assert list(ROTULOS_CRITERIOS) == ["Distância", "Tempo", "Custo"]
    assert sorted(ROTULOS_CRITERIOS.values()) == sorted(CRITERIOS_VALIDOS)
    assert ALGORITMOS == {"Dijkstra": calcularRotaDijkstra, "Bellman-Ford": calcularRotaBellmanFord}


@pytest.mark.parametrize("rotulo", ["Velocidade", "", None, 3])
def test_rotulo_desconhecido_gera_erro(rotulo):
    with pytest.raises(ValueError):
        rotulo_para_criterio(rotulo)


@pytest.mark.parametrize("nome_algoritmo", list(ALGORITMOS))
def test_regressao_bug1_distancia_no_mapa_real(grafo_real, nome_algoritmo):
    calcular_rota = ALGORITMOS[nome_algoritmo]
    # o bug: o rótulo com acento chegava cru ao algoritmo e a rota voltava 'invalida'
    assert calcular_rota(grafo_real, VERTICE_A, VERTICE_B, "Distância").situacao == SITUACAO_INVALIDA

    resultado = calcular_rota(grafo_real, VERTICE_A, VERTICE_B, rotulo_para_criterio("Distância"))
    assert resultado.situacao == SITUACAO_ENCONTRADA
    assert resultado.distanciaTotalMetros > 0


@pytest.mark.parametrize("nome_algoritmo", list(ALGORITMOS))
def test_regressao_bug1_calculo_do_app_com_rotulo_distancia(grafo_real, lanchonete, banca,
                                                           nome_algoritmo):
    rota, aviso = calcular_rota_entre_pois(grafo_real, lanchonete, banca, "Distância", nome_algoritmo)
    assert aviso is None
    assert rota["resultado"].situacao == SITUACAO_ENCONTRADA
    assert rota["nomes_caminho"][0] == grafo_real.getVertice(VERTICE_A).nome
    assert rota["nomes_caminho"][-1] == grafo_real.getVertice(VERTICE_B).nome


def test_calculo_com_rotulo_ou_algoritmo_desconhecido_gera_erro(grafo_real, lanchonete, banca):
    with pytest.raises(ValueError):
        calcular_rota_entre_pois(grafo_real, lanchonete, banca, "distância", "Dijkstra")
    with pytest.raises(ValueError):
        calcular_rota_entre_pois(grafo_real, lanchonete, banca, "Distância", "A*")


# ---------------------------------------------------------------------------
# Pedido de rota: mesmo local, fora da área e mesmo vértice (bugs 2 e 3)
# ---------------------------------------------------------------------------


def test_dois_pois_a_20_m_do_mesmo_vertice(grafo_real, dois_pois_no_mesmo_vertice):
    padaria, farmacia = dois_pois_no_mesmo_vertice
    pedido = preparar_pedido_rota(padaria, farmacia, grafo_real)
    assert pedido["motivo"] == MOTIVO_MESMO_VERTICE
    assert pedido["id_origem"] == pedido["id_destino"] == VERTICE_B
    assert pedido["distancia_origem_m"] == pytest.approx(20.0, abs=0.1)
    assert pedido["distancia_destino_m"] == pytest.approx(20.0, abs=0.1)
    assert "mesmo cruzamento" in pedido["aviso"]


def test_mesmo_vertice_avisa_sem_chamar_o_algoritmo(grafo_real, dois_pois_no_mesmo_vertice,
                                                    monkeypatch):
    def algoritmo_que_nao_pode_rodar(*_argumentos):
        raise AssertionError("o algoritmo não deveria ser chamado")

    monkeypatch.setitem(ALGORITMOS, "Dijkstra", algoritmo_que_nao_pode_rodar)
    padaria, farmacia = dois_pois_no_mesmo_vertice
    rota, aviso = calcular_rota_entre_pois(grafo_real, padaria, farmacia, "Distância", "Dijkstra")
    assert rota is None
    assert "mesmo cruzamento" in aviso


def test_mesmo_local_como_origem_e_destino(grafo_real, lanchonete):
    pedido = preparar_pedido_rota(lanchonete, dict(lanchonete), grafo_real)
    assert pedido["motivo"] == MOTIVO_MESMO_LOCAL
    assert pedido["aviso"] == "A origem e o destino devem ser diferentes."


def test_poi_fora_da_area_nao_chega_ao_algoritmo(grafo_real, lanchonete):
    pedido = preparar_pedido_rota(lanchonete, PRACA_DA_LIBERDADE, grafo_real)
    assert pedido["motivo"] == MOTIVO_FORA_DA_AREA
    assert PRACA_DA_LIBERDADE["nome"] in pedido["aviso"]
    rota, aviso = calcular_rota_entre_pois(grafo_real, lanchonete, PRACA_DA_LIBERDADE, "Distância", "Dijkstra")
    assert rota is None
    assert aviso == pedido["aviso"]


def test_regressao_bug3_praca_da_liberdade_e_mercado_central(grafo_real):
    # antes os dois caíam no mesmo vértice e a tela mostrava rota "encontrada" de 0,00 km
    rota, aviso = calcular_rota_entre_pois(
        grafo_real, PRACA_DA_LIBERDADE, MERCADO_CENTRAL, "Distância", "Dijkstra"
    )
    assert rota is None
    assert "fora da área do mapa" in aviso


def test_destino_inalcancavel_vira_aviso_sem_rota():
    # rua de mão única A -> B: de B não se volta para A
    grafo = construir_grafo({
        "vertices": [
            {"id": "A", "latitude": -19.9240, "longitude": -43.9900},
            {"id": "B", "latitude": -19.9250, "longitude": -43.9900},
        ],
        "arestas": [{"id": "e1", "origem": "A", "destino": "B", "oneway": True}],
    })
    poi_em_a = {"id": "a", "nome": "Local A", "coordenadas": [-19.9240, -43.9900]}
    poi_em_b = {"id": "b", "nome": "Local B", "coordenadas": [-19.9250, -43.9900]}
    assert calcular_rota_entre_pois(grafo, poi_em_a, poi_em_b, "Tempo", "Bellman-Ford")[1] is None
    rota, aviso = calcular_rota_entre_pois(grafo, poi_em_b, poi_em_a, "Tempo", "Bellman-Ford")
    assert rota is None
    assert aviso.startswith("Destino inalcançável")


def test_motivo_fora_da_area(grafo_real, lanchonete):
    assert motivo_fora_da_area(lanchonete, grafo_real) is None
    _id_vertice, distancia_m = associar_poi_ao_vertice(PRACA_DA_LIBERDADE, grafo_real)
    assert motivo_fora_da_area(PRACA_DA_LIBERDADE, grafo_real) == (
        f"fica a {formatar_distancia(distancia_m)} do cruzamento mais próximo do grafo (limite: 200 m)"
    )
    assert formatar_distancia(distancia_m).endswith(" km")


# ---------------------------------------------------------------------------
# Rota guardada: totais, trechos a pé, enquadramento e parâmetros (bugs 4, 6 e 7)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rotulo", list(ROTULOS_CRITERIOS))
def test_trechos_a_pe_ficam_fora_do_total(grafo_real, banca, rotulo):
    cafe = poi_perto_do_vertice(grafo_real, VERTICE_A, "Café", leste_m=-20.0)
    rota, aviso = calcular_rota_entre_pois(grafo_real, cafe, banca, rotulo, "Dijkstra")
    assert aviso is None

    # o total é exatamente o que o algoritmo devolve entre os dois vértices
    esperado = calcularRotaDijkstra(grafo_real, VERTICE_A, VERTICE_B, rotulo_para_criterio(rotulo))
    resultado = rota["resultado"]
    assert resultado.distanciaTotalMetros == esperado.distanciaTotalMetros
    assert resultado.tempoTotalSegundos == esperado.tempoTotalSegundos
    assert resultado.custoTotalReais == esperado.custoTotalReais

    for trecho, poi, id_vertice in ((rota["origem"], cafe, VERTICE_A),
                                    (rota["destino"], banca, VERTICE_B)):
        assert trecho["id_vertice"] == id_vertice
        assert trecho["distancia_m"] == pytest.approx(20.0, abs=0.1)
        assert trecho["poi"]["coordenadas"] == poi["coordenadas"]
    assert rota["caminho"][0] == rota["origem"]["coordenadas_vertice"]
    assert rota["caminho"][-1] == rota["destino"]["coordenadas_vertice"]


def test_trechos_do_mapa_um_segmento_por_rua(grafo_real):
    # as duas arestas de uma rua de mão dupla viram um segmento só
    registros = carregar_mapa(ARQUIVO_MAPA)["arestas"]
    trechos = trechos_do_mapa(grafo_real)
    assert len(trechos) == len(registros)
    pontas = {(v.latitude, v.longitude) for v in grafo_real.vertices.values()}
    for trecho in trechos:
        assert len(trecho) == 2
        assert all(tuple(ponto) in pontas for ponto in trecho)


def test_limites_dos_pontos():
    pontos = [[-19.92, -43.99], [-19.93, -43.98], [-19.925, -43.995]]
    assert limites_dos_pontos(pontos) == [[-19.93, -43.995], [-19.92, -43.98]]


def test_enquadramento_inclui_pois_e_vertices():
    rota = {
        "origem": {"poi": {"coordenadas": [-19.9200, -43.9950]}},
        "caminho": [[-19.9229, -43.9926], [-19.9242, -43.9930]],
        "destino": {"poi": {"coordenadas": [-19.9250, -43.9900]}},
    }
    assert limites_do_enquadramento(rota) == [[-19.9250, -43.9950], [-19.9200, -43.9900]]


def test_rota_guarda_os_parametros_do_calculo(grafo_real, lanchonete, banca):
    rota, _aviso = calcular_rota_entre_pois(grafo_real, lanchonete, banca, "Tempo", "Bellman-Ford")
    selecao = parametros_da_selecao("Lanchonete", "Banca da Praça", "Tempo", "Bellman-Ford")
    assert rota["parametros"] == selecao
    assert rota_corresponde_a_selecao(rota, selecao)


@pytest.mark.parametrize("campo, novo_valor", [
    ("origem", "Outro local"),
    ("destino", "Outro local"),
    ("criterio", "Custo"),
    ("algoritmo", "Dijkstra"),
])
def test_rota_antiga_nao_vale_para_outra_selecao(grafo_real, lanchonete, banca, campo, novo_valor):
    rota, _aviso = calcular_rota_entre_pois(grafo_real, lanchonete, banca, "Tempo", "Bellman-Ford")
    selecao = dict(rota["parametros"], **{campo: novo_valor})
    assert not rota_corresponde_a_selecao(rota, selecao)


def test_sem_rota_ou_sem_selecao_nao_ha_correspondencia():
    selecao = parametros_da_selecao("A", "B", "Tempo", "Dijkstra")
    assert not rota_corresponde_a_selecao(None, selecao)
    assert not rota_corresponde_a_selecao({"parametros": selecao}, None)
    assert not rota_corresponde_a_selecao({"caminho": []}, selecao)  # rota sem parâmetros


# ---------------------------------------------------------------------------
# Textos da tela e formatação com vírgula decimal (bugs 3 e 5)
# ---------------------------------------------------------------------------


def test_formatacao_com_virgula_decimal():
    assert formatar_km(600.0) == "0,60 km"
    assert formatar_km(1234.0) == "1,23 km"
    assert formatar_minutos(72.0) == "1,2 min"
    assert formatar_reais(0.0348) == "R$ 0,03"
    assert formatar_reais(1234.5) == "R$ 1.234,50"
    assert formatar_distancia(19.6) == "20 m"
    assert formatar_distancia(4965.3) == "4,97 km"
    assert formatar_decimal(1234567.891, 2) == "1.234.567,89"


def test_legenda_conta_os_locais_fora_da_area():
    assert legenda_pois_fora_da_area(0, 12) is None
    assert legenda_pois_fora_da_area(1, 12).startswith("1 de 12 locais do catálogo ficou de fora")
    legenda = legenda_pois_fora_da_area(11, 12)
    assert legenda.startswith("11 de 12 locais do catálogo ficaram de fora")
    assert "200 m" in legenda


@pytest.mark.parametrize("quantidade, aviso_esperado", [(0, True), (1, True), (2, False), (5, False)])
def test_aviso_quando_ha_menos_de_dois_pois_na_area(quantidade, aviso_esperado):
    assert (aviso_poucos_pois_na_area(quantidade) is not None) == aviso_esperado
