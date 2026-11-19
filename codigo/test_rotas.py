"""
Testes independentes do modelo (grafo.py), da importação (mapa.py) e da busca (rotas.py).

Cada teste monta grafos pequenos com respostas ótimas conhecidas (calculadas à mão ou por
força bruta) e não depende de interface nem de rede: uma fixture bloqueia qualquer conexão.

Como executar, a partir da raiz do repositório:
    python -m pytest codigo/test_rotas.py -v
"""

import itertools
import json
import math
import os
import random
import socket
import sys
from typing import Dict, List, Optional, Tuple

import pytest

PASTA_CODIGO = os.path.dirname(os.path.abspath(__file__))
if PASTA_CODIGO not in sys.path:
    sys.path.insert(0, PASTA_CODIGO)

from grafo import (  # noqa: E402
    CRITERIOS_VALIDOS,
    SITUACAO_ENCONTRADA,
    SITUACAO_INALCANCAVEL,
    SITUACAO_INVALIDA,
    Aresta,
    Grafo,
    ResultadoRota,
    Vertice,
    normalizarCriterio,
)
from mapa import (  # noqa: E402
    calcular_custo_reais,
    calcular_distancia_haversine,
    calcular_tempo_segundos,
    carregar_mapa,
    carregar_pois,
    construir_grafo,
)
from rotas import calcularRotaBellmanFord, calcularRotaDijkstra  # noqa: E402

CAMINHO_MAPA_REAL = os.path.join(PASTA_CODIGO, "dados", "mapa.json")
CAMINHO_POIS_REAIS = os.path.join(PASTA_CODIGO, "dados", "pontos_interesse.json")

ALGORITMOS = [
    pytest.param(calcularRotaDijkstra, id="dijkstra"),
    pytest.param(calcularRotaBellmanFord, id="bellman_ford"),
]

TOLERANCIA = 1e-9


# ---------------------------------------------------------------------------
# Infraestrutura: sem rede e sem interface
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def bloquearRede(monkeypatch):
    """Qualquer tentativa de conexão de rede durante os testes falha imediatamente."""

    def conexaoProibida(*_args, **_kwargs):
        raise RuntimeError("Os testes de rotas não podem acessar a rede")

    monkeypatch.setattr(socket.socket, "connect", conexaoProibida)
    monkeypatch.setattr(socket, "create_connection", conexaoProibida)


def test_modulos_testados_nao_carregam_interface():
    """Importar modelo, mapa e rotas não pode carregar Streamlit/Folium (testes sem interface)."""
    assert "streamlit" not in sys.modules
    assert "folium" not in sys.modules


def test_rede_esta_bloqueada_durante_os_testes():
    """Garante que a fixture bloquearRede realmente impede conexões."""
    with pytest.raises(RuntimeError):
        socket.create_connection(("example.com", 80), timeout=1)


# ---------------------------------------------------------------------------
# Construtores auxiliares de grafos pequenos
# ---------------------------------------------------------------------------

def vertice(id_vertice: str, indice: int = 0) -> Vertice:
    """Cria um vértice com coordenadas válidas (a posição não influencia os pesos)."""
    return Vertice(id_vertice, -19.92 + indice * 0.0001, -43.99 + indice * 0.0001)


def montarGrafo(arestas: List[Tuple[str, str, str, float, float, float]]) -> Grafo:
    """
    Monta um grafo dirigido a partir de tuplas (id, origem, destino, distancia, tempo, custo).
    Os pesos são informados diretamente para que as respostas ótimas sejam conhecidas.
    """
    grafo = Grafo()
    criados: Dict[str, Vertice] = {}
    for id_aresta, origem, destino, distancia, tempo, custo in arestas:
        for nome in (origem, destino):
            if nome not in criados:
                criados[nome] = vertice(nome, len(criados))
        grafo.adicionarAresta(
            Aresta(id_aresta, criados[origem], criados[destino], distancia, 30.0, tempo, custo)
        )
    return grafo


def idsDoCaminho(resultado: ResultadoRota) -> List[str]:
    return [aresta.id for aresta in resultado.caminho]


def verificarCaminhoCoerente(grafo: Grafo, resultado: ResultadoRota, origem: str, destino: str) -> None:
    """
    Confere que o caminho devolvido é válido no grafo e que a soma dos pesos das arestas
    confere com os totais informados, nos três critérios.
    """
    assert resultado.situacao == SITUACAO_ENCONTRADA
    caminho = resultado.caminho
    if origem == destino:
        assert caminho == []
    else:
        assert caminho[0].origem.id == origem
        assert caminho[-1].destino.id == destino
    for anterior, seguinte in zip(caminho, caminho[1:]):
        assert anterior.destino.id == seguinte.origem.id
    for aresta in caminho:
        # A aresta precisa existir no grafo com a mesma orientação (respeita mão única)
        assert grafo.getAresta(aresta.id) is aresta
        assert aresta in grafo.getAdjacencias(aresta.origem.id)
    for criterio in CRITERIOS_VALIDOS:
        soma = math.fsum(aresta.getPeso(criterio) for aresta in caminho)
        assert resultado.getTotal(criterio) == pytest.approx(soma, abs=TOLERANCIA)


def menorCustoPorForcaBruta(grafo: Grafo, origem: str, destino: str, criterio: str) -> Optional[float]:
    """Enumera todos os caminhos simples (com escolha de arestas paralelas) e devolve o menor custo."""
    if origem == destino:
        return 0.0
    melhor: Optional[float] = None
    pilha: List[Tuple[str, float, frozenset]] = [(origem, 0.0, frozenset([origem]))]
    while pilha:
        atual, custo, visitados = pilha.pop()
        for aresta in grafo.getAdjacencias(atual):
            vizinho = aresta.destino.id
            novoCusto = custo + aresta.getPeso(criterio)
            if vizinho == destino:
                if melhor is None or novoCusto < melhor:
                    melhor = novoCusto
            elif vizinho not in visitados:
                pilha.append((vizinho, novoCusto, visitados | {vizinho}))
    return melhor


# Três rotas S -> T, cada uma ótima em um critério diferente:
#   via A: distância 200 (ótima), tempo 200, custo 10
#   via B: distância 600, tempo 40 (ótimo), custo 8
#   via C: distância 800, tempo 300, custo 2 (ótimo)
ARESTAS_TRES_CRITERIOS = [
    ("sa", "S", "A", 100.0, 100.0, 5.0),
    ("at", "A", "T", 100.0, 100.0, 5.0),
    ("sb", "S", "B", 300.0, 20.0, 4.0),
    ("bt", "B", "T", 300.0, 20.0, 4.0),
    ("sc", "S", "C", 400.0, 150.0, 1.0),
    ("ct", "C", "T", 400.0, 150.0, 1.0),
]


# ---------------------------------------------------------------------------
# Modelo (grafo.py)
# ---------------------------------------------------------------------------

def test_aresta_devolve_peso_de_cada_criterio():
    """getPeso devolve o peso certo para cada critério e normaliza maiúsculas/espaços."""
    aresta = Aresta("e", vertice("A", 0), vertice("B", 1), 150.0, 30.0, 18.0, 0.87)
    assert aresta.getPeso("distancia") == 150.0
    assert aresta.getPeso("tempo") == 18.0
    assert aresta.getPeso("custo") == 0.87
    assert aresta.getPeso("  TEMPO ") == 18.0


@pytest.mark.parametrize("criterio", ["velocidade", "", "distância", None, 3])
def test_criterio_desconhecido_e_rejeitado_pelo_modelo(criterio):
    """Critérios fora de distancia/tempo/custo (inclusive com acento ou não-texto) geram ValueError."""
    with pytest.raises(ValueError):
        normalizarCriterio(criterio)


@pytest.mark.parametrize(
    "distancia, velocidade, tempo, custo",
    [
        (-1.0, 30.0, 1.0, 1.0),                  # distância negativa
        (1.0, 0.0, 1.0, 1.0),                    # velocidade zero
        (1.0, -30.0, 1.0, 1.0),                  # velocidade negativa
        (1.0, 30.0, -0.1, 1.0),                  # tempo negativo
        (1.0, 30.0, 1.0, -0.01),                 # custo negativo
        (float("nan"), 30.0, 1.0, 1.0),          # NaN
        (1.0, 30.0, float("inf"), 1.0),          # infinito
        ("dez", 30.0, 1.0, 1.0),                 # texto não numérico
        (None, 30.0, 1.0, 1.0),                  # ausente
    ],
)
def test_aresta_rejeita_pesos_invalidos(distancia, velocidade, tempo, custo):
    """Pesos negativos, NaN, infinitos ou não numéricos são recusados (Dijkstra exige pesos >= 0)."""
    with pytest.raises(ValueError):
        Aresta("e", vertice("A", 0), vertice("B", 1), distancia, velocidade, tempo, custo)


def test_aresta_aceita_pesos_zero():
    """Peso zero é válido (ex.: dois nós na mesma posição)."""
    aresta = Aresta("e", vertice("A", 0), vertice("B", 1), 0.0, 30.0, 0.0, 0.0)
    assert [aresta.getPeso(c) for c in CRITERIOS_VALIDOS] == [0.0, 0.0, 0.0]


def test_aresta_exige_vertices_como_extremidades():
    """Origem e destino da aresta precisam ser objetos Vertice, não ids soltos."""
    with pytest.raises(TypeError):
        Aresta("e", "A", vertice("B", 1), 1.0, 30.0, 1.0, 1.0)


@pytest.mark.parametrize("latitude, longitude", [(91.0, 0.0), (0.0, -181.0), (float("nan"), 0.0)])
def test_vertice_rejeita_coordenadas_invalidas(latitude, longitude):
    """Latitude fora de [-90, 90], longitude fora de [-180, 180] ou NaN são recusadas."""
    with pytest.raises(ValueError):
        Vertice("A", latitude, longitude)


def test_grafo_e_dirigido_mao_unica_nao_gera_volta():
    """Uma aresta A -> B não cria automaticamente B -> A (o grafo é dirigido)."""
    grafo = montarGrafo([("ab", "A", "B", 1.0, 1.0, 1.0)])
    assert [a.id for a in grafo.getAdjacencias("A")] == ["ab"]
    assert grafo.getAdjacencias("B") == []


def test_grafo_guarda_arestas_paralelas_com_ids_distintos():
    """Duas vias entre os mesmos vértices coexistem, diferenciadas pelo id."""
    grafo = montarGrafo([("p1", "A", "B", 10.0, 1.0, 1.0), ("p2", "A", "B", 3.0, 9.0, 1.0)])
    assert sorted(a.id for a in grafo.getArestasEntre("A", "B")) == ["p1", "p2"]
    assert grafo.quantidade_arestas() == 2


def test_grafo_rejeita_id_de_aresta_repetido():
    """O id da aresta é único no grafo."""
    grafo = montarGrafo([("e", "A", "B", 1.0, 1.0, 1.0)])
    with pytest.raises(ValueError):
        grafo.adicionarAresta(Aresta("e", vertice("B", 1), vertice("C", 2), 1.0, 30.0, 1.0, 1.0))


def test_grafo_rejeita_vertice_repetido_com_outra_posicao():
    """Readicionar o mesmo vértice é ignorado; mesmo id com outra posição é erro."""
    grafo = Grafo()
    grafo.adicionarVertice(Vertice("A", -19.0, -43.0))
    grafo.adicionarVertice(Vertice("A", -19.0, -43.0))  # mesmo vértice: sem efeito
    with pytest.raises(ValueError):
        grafo.adicionarVertice(Vertice("A", -19.5, -43.0))
    assert grafo.quantidade_vertices() == 1


def test_resultado_soma_pesos_do_caminho():
    """ResultadoRota.aPartirDoCaminho soma os três pesos das arestas e lista os vértices."""
    grafo = montarGrafo(ARESTAS_TRES_CRITERIOS)
    resultado = ResultadoRota.aPartirDoCaminho([grafo.getAresta("sb"), grafo.getAresta("bt")])
    assert (resultado.distanciaTotalMetros, resultado.tempoTotalSegundos, resultado.custoTotalReais) == (
        600.0, 40.0, 8.0,
    )
    assert [v.id for v in resultado.getVerticesCaminho()] == ["S", "B", "T"]


def test_resultado_rejeita_caminho_descontinuo():
    """Um caminho cujas arestas não se encadeiam é recusado."""
    grafo = montarGrafo(ARESTAS_TRES_CRITERIOS)
    with pytest.raises(ValueError):
        ResultadoRota.aPartirDoCaminho([grafo.getAresta("sa"), grafo.getAresta("bt")])


# ---------------------------------------------------------------------------
# Importação (mapa.py) com arquivos temporários
# ---------------------------------------------------------------------------

def gravarJson(pasta, nome: str, conteudo) -> str:
    caminho = pasta / nome
    caminho.write_text(json.dumps(conteudo), encoding="utf-8")
    return str(caminho)


def mapaMinimo(arestas: List[dict]) -> dict:
    return {
        "vertices": [
            {"id": "A", "latitude": -19.9200, "longitude": -43.9900},
            {"id": "B", "latitude": -19.9210, "longitude": -43.9900},
            {"id": "C", "latitude": -19.9210, "longitude": -43.9910},
        ],
        "arestas": arestas,
    }


def test_importacao_respeita_mao_unica_e_mao_dupla(tmp_path):
    """oneway=True gera uma aresta; mão dupla gera também a reversa '<id>_rev'."""
    caminho = gravarJson(tmp_path, "mapa.json", mapaMinimo([
        {"id": "ab", "origem": "A", "destino": "B", "velocidade_kmh": 36.0, "oneway": True},
        {"id": "bc", "origem": "B", "destino": "C"},
    ]))
    grafo = construir_grafo(carregar_mapa(caminho))

    assert grafo.getArestasEntre("A", "B") and not grafo.getArestasEntre("B", "A")
    assert grafo.getAresta("bc") is not None and grafo.getAresta("bc_rev") is not None
    assert grafo.quantidade_arestas() == 3


def test_importacao_calcula_os_tres_pesos_de_forma_consistente(tmp_path):
    """Distância vem de Haversine, tempo = distância / velocidade e custo da fórmula de combustível."""
    caminho = gravarJson(tmp_path, "mapa.json", mapaMinimo([
        {"id": "ab", "origem": "A", "destino": "B", "velocidade_kmh": 36.0, "oneway": True},
    ]))
    aresta = construir_grafo(carregar_mapa(caminho)).getAresta("ab")

    distanciaEsperada = calcular_distancia_haversine(-19.9200, -43.9900, -19.9210, -43.9900)
    assert aresta.distanciaMetros == pytest.approx(distanciaEsperada)
    assert aresta.distanciaMetros == pytest.approx(111.19, abs=0.01)  # 0,001° de latitude
    assert aresta.tempoSegundos == pytest.approx(aresta.distanciaMetros / 10.0)  # 36 km/h = 10 m/s
    assert aresta.custoReais == pytest.approx(calcular_custo_reais(aresta.distanciaMetros))


def test_importacao_arquivo_inexistente(tmp_path):
    """Caminho de mapa ou de POIs inexistente gera FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        carregar_mapa(str(tmp_path / "nao_existe.json"))
    with pytest.raises(FileNotFoundError):
        carregar_pois(str(tmp_path / "nao_existe.json"))


def test_importacao_json_malformado(tmp_path):
    """Arquivo que não é JSON válido é recusado."""
    caminho = tmp_path / "mapa.json"
    caminho.write_text("{ isto não é json", encoding="utf-8")
    with pytest.raises(ValueError):  # json.JSONDecodeError herda de ValueError
        carregar_mapa(str(caminho))


@pytest.mark.parametrize(
    "conteudo",
    [[], {"vertices": []}, {"arestas": []}, "texto"],
    ids=["raiz_lista", "sem_arestas", "sem_vertices", "raiz_texto"],
)
def test_importacao_estrutura_de_mapa_invalida(tmp_path, conteudo):
    """O mapa precisa ser um objeto com as chaves 'vertices' e 'arestas'."""
    with pytest.raises(ValueError):
        carregar_mapa(gravarJson(tmp_path, "mapa.json", conteudo))


@pytest.mark.parametrize(
    "conteudo",
    [{"id": "x"}, [{"id": "x", "nome": "Sem coordenadas"}]],
    ids=["raiz_objeto", "poi_incompleto"],
)
def test_importacao_pois_invalidos(tmp_path, conteudo):
    """POIs precisam ser uma lista e cada um precisa de id, nome e coordenadas."""
    with pytest.raises(ValueError):
        carregar_pois(gravarJson(tmp_path, "pois.json", conteudo))


@pytest.mark.parametrize(
    "aresta",
    [
        {"id": "e", "origem": "Z", "destino": "B"},
        {"id": "e", "origem": "A", "destino": "Z"},
    ],
    ids=["origem_desconhecida", "destino_desconhecido"],
)
def test_importacao_referencia_a_vertice_inexistente(aresta):
    """Aresta que aponta para vértice não declarado é uma referência inválida."""
    with pytest.raises(ValueError):
        construir_grafo(mapaMinimo([aresta]))


@pytest.mark.parametrize("velocidade", [0.0, -20.0, float("nan"), "rapido"])
def test_importacao_velocidade_invalida(velocidade):
    """Velocidade zero, negativa, NaN ou texto impede montar a aresta."""
    with pytest.raises(ValueError):
        construir_grafo(mapaMinimo([{"id": "e", "origem": "A", "destino": "B", "velocidade_kmh": velocidade}]))


def test_importacao_id_de_aresta_repetido():
    """Dois registros com o mesmo id de aresta no arquivo são recusados."""
    with pytest.raises(ValueError):
        construir_grafo(mapaMinimo([
            {"id": "e", "origem": "A", "destino": "B", "oneway": True},
            {"id": "e", "origem": "B", "destino": "C", "oneway": True},
        ]))


def test_importacao_vertice_com_coordenada_invalida():
    """Vértice com latitude impossível no arquivo é recusado."""
    dados = mapaMinimo([])
    dados["vertices"][0]["latitude"] = 123.0
    with pytest.raises(ValueError):
        construir_grafo(dados)


@pytest.mark.parametrize(
    "funcao, argumentos",
    [
        (calcular_tempo_segundos, (100.0, 0.0)),
        (calcular_tempo_segundos, (-1.0, 30.0)),
        (calcular_custo_reais, (100.0, 0.0)),
        (calcular_custo_reais, (100.0, 10.0, -1.0)),
        (calcular_custo_reais, (-1.0,)),
    ],
)
def test_importacao_parametros_de_peso_invalidos(funcao, argumentos):
    """As funções de cálculo de peso recusam velocidade, consumo, preço ou distância inválidos."""
    with pytest.raises(ValueError):
        funcao(*argumentos)


# ---------------------------------------------------------------------------
# Busca (rotas.py): três critérios
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("calcularRota", ALGORITMOS)
@pytest.mark.parametrize(
    "criterio, caminhoEsperado, totaisEsperados",
    [
        ("distancia", ["sa", "at"], (200.0, 200.0, 10.0)),
        ("tempo", ["sb", "bt"], (600.0, 40.0, 8.0)),
        ("custo", ["sc", "ct"], (800.0, 300.0, 2.0)),
    ],
)
def test_cada_criterio_tem_sua_rota_otima(calcularRota, criterio, caminhoEsperado, totaisEsperados):
    """No grafo ARESTAS_TRES_CRITERIOS, cada critério escolhe a rota ótima conhecida, com totais exatos."""
    grafo = montarGrafo(ARESTAS_TRES_CRITERIOS)
    resultado = calcularRota(grafo, "S", "T", criterio)

    assert idsDoCaminho(resultado) == caminhoEsperado
    assert (
        resultado.distanciaTotalMetros, resultado.tempoTotalSegundos, resultado.custoTotalReais
    ) == totaisEsperados
    verificarCaminhoCoerente(grafo, resultado, "S", "T")


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_criterios_diferentes_geram_rotas_diferentes(calcularRota):
    """Os três critérios produzem três rotas distintas para o mesmo par origem/destino."""
    grafo = montarGrafo(ARESTAS_TRES_CRITERIOS)
    rotas = {tuple(idsDoCaminho(calcularRota(grafo, "S", "T", c))) for c in CRITERIOS_VALIDOS}
    assert len(rotas) == 3


# ---------------------------------------------------------------------------
# Busca: mão única, arestas paralelas, empates, origem = destino, inalcançável
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_mao_unica_nao_e_usada_no_sentido_contrario(calcularRota):
    """Um atalho de mão única só é usado no sentido permitido."""
    # Atalho T -> S de peso 1 só vale nesse sentido; de S até T é preciso passar por A.
    grafo = montarGrafo([
        ("sa", "S", "A", 10.0, 10.0, 10.0),
        ("at", "A", "T", 10.0, 10.0, 10.0),
        ("atalho_ts", "T", "S", 1.0, 1.0, 1.0),
    ])
    ida = calcularRota(grafo, "S", "T", "distancia")
    volta = calcularRota(grafo, "T", "S", "distancia")

    assert idsDoCaminho(ida) == ["sa", "at"] and ida.distanciaTotalMetros == 20.0
    assert idsDoCaminho(volta) == ["atalho_ts"] and volta.distanciaTotalMetros == 1.0
    verificarCaminhoCoerente(grafo, ida, "S", "T")
    verificarCaminhoCoerente(grafo, volta, "T", "S")


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_mao_unica_sem_caminho_de_volta_e_inalcancavel(calcularRota):
    """Sem aresta de volta, o caminho reverso é 'inalcancavel'."""
    grafo = montarGrafo([("ab", "A", "B", 5.0, 5.0, 5.0)])
    assert calcularRota(grafo, "A", "B", "distancia").situacao == SITUACAO_ENCONTRADA
    assert calcularRota(grafo, "B", "A", "distancia").situacao == SITUACAO_INALCANCAVEL


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
@pytest.mark.parametrize(
    "criterio, arestaEsperada, totalEsperado",
    [("distancia", "p2", 3.0), ("tempo", "p1", 1.0), ("custo", "p3", 0.5)],
)
def test_aresta_paralela_mais_barata_no_criterio_e_escolhida(calcularRota, criterio, arestaEsperada, totalEsperado):
    """Entre arestas paralelas, cada critério escolhe a sua mais barata (pode ser uma diferente)."""
    grafo = montarGrafo([
        ("p1", "A", "B", 10.0, 1.0, 4.0),
        ("p2", "A", "B", 3.0, 9.0, 2.0),
        ("p3", "A", "B", 7.0, 5.0, 0.5),
    ])
    resultado = calcularRota(grafo, "A", "B", criterio)

    assert idsDoCaminho(resultado) == [arestaEsperada]
    assert resultado.getTotal(criterio) == totalEsperado
    verificarCaminhoCoerente(grafo, resultado, "A", "B")


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_empate_entre_caminhos_devolve_um_caminho_otimo(calcularRota):
    """Com dois caminhos de mesmo custo, qualquer um é aceito, desde que o custo seja o ótimo."""
    # Dois caminhos com distância 10: S-A-T (5 + 5) e S-B-T (4 + 6).
    grafo = montarGrafo([
        ("sa", "S", "A", 5.0, 1.0, 1.0),
        ("at", "A", "T", 5.0, 1.0, 1.0),
        ("sb", "S", "B", 4.0, 2.0, 2.0),
        ("bt", "B", "T", 6.0, 2.0, 2.0),
    ])
    resultado = calcularRota(grafo, "S", "T", "distancia")

    assert resultado.distanciaTotalMetros == 10.0
    assert idsDoCaminho(resultado) in (["sa", "at"], ["sb", "bt"])
    verificarCaminhoCoerente(grafo, resultado, "S", "T")


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_empate_entre_arestas_paralelas_iguais(calcularRota):
    """Arestas paralelas com o mesmo peso: qualquer uma é uma resposta ótima."""
    grafo = montarGrafo([("p1", "A", "B", 4.0, 4.0, 4.0), ("p2", "A", "B", 4.0, 4.0, 4.0)])
    resultado = calcularRota(grafo, "A", "B", "custo")

    assert resultado.custoTotalReais == 4.0
    assert idsDoCaminho(resultado) in (["p1"], ["p2"])


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
@pytest.mark.parametrize("criterio", CRITERIOS_VALIDOS)
def test_origem_igual_ao_destino_tem_custo_zero(calcularRota, criterio):
    """Origem = destino é rota 'encontrada', sem arestas e com totais zero."""
    grafo = montarGrafo(ARESTAS_TRES_CRITERIOS)
    resultado = calcularRota(grafo, "A", "A", criterio)

    assert resultado.situacao == SITUACAO_ENCONTRADA
    assert resultado.caminho == []
    assert (resultado.distanciaTotalMetros, resultado.tempoTotalSegundos, resultado.custoTotalReais) == (0, 0, 0)
    verificarCaminhoCoerente(grafo, resultado, "A", "A")


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_origem_igual_ao_destino_em_vertice_isolado(calcularRota):
    """Mesmo um vértice sem arestas é alcançável a partir de si mesmo."""
    grafo = montarGrafo([("ab", "A", "B", 1.0, 1.0, 1.0)])
    grafo.adicionarVertice(vertice("ISOLADO", 9))
    resultado = calcularRota(grafo, "ISOLADO", "ISOLADO", "tempo")
    assert resultado.situacao == SITUACAO_ENCONTRADA and resultado.tempoTotalSegundos == 0.0


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
@pytest.mark.parametrize("criterio", CRITERIOS_VALIDOS)
def test_destino_em_outro_componente_e_inalcancavel(calcularRota, criterio):
    """Destino em outro componente: situação 'inalcancavel', caminho vazio e totais None."""
    grafo = montarGrafo([
        ("ab", "A", "B", 1.0, 1.0, 1.0),
        ("ba", "B", "A", 1.0, 1.0, 1.0),
        ("cd", "C", "D", 1.0, 1.0, 1.0),
    ])
    resultado = calcularRota(grafo, "A", "D", criterio)

    assert resultado.situacao == SITUACAO_INALCANCAVEL
    assert resultado.caminho == []
    assert resultado.getTotal(criterio) is None
    assert not resultado.foiEncontrada()


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
@pytest.mark.parametrize(
    "origem, destino, criterio",
    [("X", "T", "distancia"), ("S", "X", "tempo"), ("S", "T", "velocidade"), ("S", "T", "")],
    ids=["origem_inexistente", "destino_inexistente", "criterio_desconhecido", "criterio_vazio"],
)
def test_pedido_invalido_e_diferente_de_inalcancavel(calcularRota, origem, destino, criterio):
    """Vértice ou critério inexistente gera 'invalida', não 'inalcancavel'."""
    resultado = calcularRota(montarGrafo(ARESTAS_TRES_CRITERIOS), origem, destino, criterio)
    assert resultado.situacao == SITUACAO_INVALIDA
    assert resultado.caminho == []


# ---------------------------------------------------------------------------
# Busca: otimalidade e soma dos pesos
# ---------------------------------------------------------------------------

def gerarGrafoAleatorio(semente: int, quantidadeVertices: int = 6, quantidadeArestas: int = 14) -> Grafo:
    """Grafo dirigido pequeno, com arestas paralelas possíveis e pesos inteiros independentes."""
    sorteio = random.Random(semente)
    nomes = [f"v{i}" for i in range(quantidadeVertices)]
    arestas = []
    for indice in range(quantidadeArestas):
        origem, destino = sorteio.sample(nomes, 2)
        arestas.append((
            f"e{indice}", origem, destino,
            float(sorteio.randint(0, 20)), float(sorteio.randint(0, 20)), float(sorteio.randint(0, 20)),
        ))
    grafo = montarGrafo(arestas)
    for indice, nome in enumerate(nomes):
        if not grafo.existeVertice(nome):
            grafo.adicionarVertice(vertice(nome, 100 + indice))
    return grafo


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
@pytest.mark.parametrize("semente", range(15))
def test_custo_igual_ao_da_forca_bruta_em_grafos_aleatorios(calcularRota, semente):
    """Em grafos aleatórios pequenos (sementes fixas), o custo bate com a força bruta para todos os pares e critérios."""
    grafo = gerarGrafoAleatorio(semente)
    for origem, destino in itertools.product(grafo.vertices, repeat=2):
        for criterio in CRITERIOS_VALIDOS:
            esperado = menorCustoPorForcaBruta(grafo, origem, destino, criterio)
            resultado = calcularRota(grafo, origem, destino, criterio)
            if esperado is None:
                assert resultado.situacao == SITUACAO_INALCANCAVEL
            else:
                assert resultado.getTotal(criterio) == pytest.approx(esperado)
                verificarCaminhoCoerente(grafo, resultado, origem, destino)


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_soma_dos_pesos_confere_no_mapa_real(calcularRota):
    """Importa o snapshot local (sem rede) e confere todas as rotas entre pares de vértices."""
    grafo = construir_grafo(carregar_mapa(CAMINHO_MAPA_REAL), carregar_pois(CAMINHO_POIS_REAIS))
    assert grafo.quantidade_vertices() > 0
    for origem, destino in itertools.product(grafo.vertices, repeat=2):
        for criterio in CRITERIOS_VALIDOS:
            resultado = calcularRota(grafo, origem, destino, criterio)
            esperado = menorCustoPorForcaBruta(grafo, origem, destino, criterio)
            if esperado is None:
                assert resultado.situacao == SITUACAO_INALCANCAVEL
                continue
            verificarCaminhoCoerente(grafo, resultado, origem, destino)
            assert resultado.getTotal(criterio) == pytest.approx(esperado)


def test_dijkstra_e_bellman_ford_concordam_no_custo():
    """Validação cruzada: os dois algoritmos chegam ao mesmo custo ótimo."""
    grafo = montarGrafo(ARESTAS_TRES_CRITERIOS)
    for criterio in CRITERIOS_VALIDOS:
        dijkstra = calcularRotaDijkstra(grafo, "S", "T", criterio)
        bellmanFord = calcularRotaBellmanFord(grafo, "S", "T", criterio)
        assert dijkstra.getTotal(criterio) == bellmanFord.getTotal(criterio)
