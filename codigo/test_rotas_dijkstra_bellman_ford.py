"""
Testes de rotas.py (Issue 07): Método de Dijkstra e algoritmo de Bellman-Ford.

Rodam só com pytest, sem interface e sem rede:
    python -m pytest codigo/test_rotas_dijkstra_bellman_ford.py -v

Feitos para o Integrante 4 incorporar ao test_rotas.py da Issue 08. Usam apenas
as duas funções públicas de rotas.py; as funções com "_" são detalhes internos.
"""

import ast
import doctest
import math
import os
import random
from typing import Callable, List, Tuple

import pytest

import rotas
from grafo import (
    CRITERIO_CUSTO,
    CRITERIO_DISTANCIA,
    CRITERIO_TEMPO,
    CRITERIOS_VALIDOS,
    SITUACAO_ENCONTRADA,
    SITUACAO_INALCANCAVEL,
    SITUACAO_INVALIDA,
    Aresta,
    Grafo,
    ResultadoRota,
    Vertice,
)
from mapa import carregar_mapa, construir_grafo
from rotas import calcularRotaBellmanFord, calcularRotaDijkstra

FuncaoDeRota = Callable[[Grafo, str, str, str], ResultadoRota]

# Os dois algoritmos têm a mesma assinatura, então quase todo teste roda nos dois.
ALGORITMOS = [
    pytest.param(calcularRotaDijkstra, id="dijkstra"),
    pytest.param(calcularRotaBellmanFord, id="bellman_ford"),
]

# Coordenadas e velocidade não influenciam a busca; usamos valores fixos.
LATITUDE_FIXA = -19.9229
LONGITUDE_FIXA = -43.9926
VELOCIDADE_FIXA_KMH = 30.0

ARQUIVO_MAPA = os.path.join(os.path.dirname(__file__), "dados", "mapa.json")

# Grafo dos slides "Caminho Mínimo (1)", raiz c, e as distâncias esperadas.
ARESTAS_DOS_SLIDES = [
    ("c", "a", 5.0), ("c", "e", 1.0), ("a", "b", 6.0), ("e", "b", 1.0),
    ("e", "f", 8.0), ("b", "d", 1.0), ("d", "f", 1.0), ("f", "a", 2.0),
]
DISTANCIAS_DOS_SLIDES = {"c": 0.0, "e": 1.0, "b": 2.0, "d": 3.0, "f": 4.0, "a": 5.0}

# Três rotas de A até D, cada uma a melhor em um critério:
#   via B: curta e lenta; via C: longa e rápida; via E: a mais barata.
ARESTAS_TRES_CRITERIOS = [
    # (id, origem, destino, distância m, tempo s, custo R$)
    ("AB", "A", "B", 100.0, 60.0, 3.0), ("BD", "B", "D", 100.0, 60.0, 3.0),
    ("AC", "A", "C", 300.0, 20.0, 2.5), ("CD", "C", "D", 300.0, 20.0, 2.5),
    ("AE", "A", "E", 400.0, 50.0, 1.0), ("ED", "E", "D", 400.0, 50.0, 1.0),
]

# Sementes fixas para os grafos aleatórios da validação cruzada.
SEMENTES = [1, 2, 3, 7, 42, 2024]


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------


def criarVertice(idDoVertice: str) -> Vertice:
    return Vertice(idDoVertice, LATITUDE_FIXA, LONGITUDE_FIXA)


def montarGrafo(arestas: List[Tuple[str, str, str, float, float, float]]) -> Grafo:
    """Grafo real a partir de (id, origem, destino, distância, tempo, custo)."""
    grafo = Grafo()
    for idDaAresta, origem, destino, distancia, tempo, custo in arestas:
        grafo.adicionarAresta(Aresta(
            idDaAresta, criarVertice(origem), criarVertice(destino),
            distancia, VELOCIDADE_FIXA_KMH, tempo, custo,
        ))
    return grafo


def montarGrafoComPesoUnico(arestas: List[Tuple[str, str, float]]) -> Grafo:
    """Grafo real com o mesmo peso nos três critérios; id da aresta = origem + destino."""
    return montarGrafo([
        (origem + destino, origem, destino, peso, peso, peso)
        for origem, destino, peso in arestas
    ])


def gerarGrafoAleatorio(semente: int) -> Grafo:
    """Grafo aleatório reprodutível: pesos inteiros (muitos empates), zeros, laços e paralelas."""
    gerador = random.Random(semente)
    quantidadeDeVertices = gerador.randint(6, 14)
    quantidadeDeArestas = gerador.randint(quantidadeDeVertices, 3 * quantidadeDeVertices)
    grafo = Grafo()
    for indice in range(quantidadeDeVertices):
        grafo.adicionarVertice(criarVertice(f"v{indice}"))
    idsDosVertices = list(grafo.vertices.keys())
    for indice in range(quantidadeDeArestas):
        origem = grafo.getVertice(gerador.choice(idsDosVertices))
        destino = grafo.getVertice(gerador.choice(idsDosVertices))
        distancia, tempo, custo = (float(gerador.randint(0, 9)) for _ in range(3))
        grafo.adicionarAresta(Aresta(
            f"e{indice}", origem, destino, distancia, VELOCIDADE_FIXA_KMH, tempo, custo,
        ))
    return grafo


def idsDoCaminho(resultado: ResultadoRota) -> List[str]:
    return [vertice.id for vertice in resultado.getVerticesCaminho()]


def conferirCaminho(grafo: Grafo, resultado: ResultadoRota, origem: str, destino: str) -> None:
    """O caminho começa na origem, termina no destino, usa arestas reais e soma os totais."""
    caminho = resultado.caminho
    if origem == destino:
        assert caminho == []
    else:
        assert caminho[0].origem.id == origem
        assert caminho[-1].destino.id == destino
    for aresta in caminho:
        # a aresta existe no grafo, no sentido em que foi percorrida
        assert aresta in grafo.getArestasEntre(aresta.origem.id, aresta.destino.id)
    for criterio in CRITERIOS_VALIDOS:
        somaDasArestas = math.fsum(aresta.getPeso(criterio) for aresta in caminho)
        assert resultado.getTotal(criterio) == pytest.approx(somaDasArestas)


def compararAlgoritmos(grafo: Grafo, pares: List[Tuple[str, str]]) -> None:
    """Dijkstra e Bellman-Ford devem concordar na situação e no custo total."""
    for criterio in CRITERIOS_VALIDOS:
        for origem, destino in pares:
            resultadoDijkstra = calcularRotaDijkstra(grafo, origem, destino, criterio)
            resultadoBellmanFord = calcularRotaBellmanFord(grafo, origem, destino, criterio)
            assert resultadoDijkstra.situacao == resultadoBellmanFord.situacao
            # compara o custo e não o caminho: com empates, os dois podem escolher
            # caminhos diferentes de mesmo custo
            totalDijkstra = resultadoDijkstra.getTotal(criterio)
            totalBellmanFord = resultadoBellmanFord.getTotal(criterio)
            assert totalDijkstra == pytest.approx(totalBellmanFord)
            if resultadoDijkstra.foiEncontrada():
                conferirCaminho(grafo, resultadoDijkstra, origem, destino)
                conferirCaminho(grafo, resultadoBellmanFord, origem, destino)


def todosOsPares(grafo: Grafo) -> List[Tuple[str, str]]:
    idsDosVertices = list(grafo.vertices.keys())
    return [(origem, destino) for origem in idsDosVertices for destino in idsDosVertices]


# ---------------------------------------------------------------------------
# Grafo falso, só para pesos negativos (a Aresta real rejeita peso negativo)
# ---------------------------------------------------------------------------


class ArestaComPesoNegativo:
    """Imita Aresta com o mesmo peso nos três critérios, aceitando valor negativo."""

    def __init__(self, idDaAresta: str, origem: Vertice, destino: Vertice, peso: float) -> None:
        self.id = idDaAresta
        self.origem = origem
        self.destino = destino
        # ResultadoRota.aPartirDoCaminho soma estes três atributos
        self.distanciaMetros = self.tempoSegundos = self.custoReais = peso

    def getPeso(self, criterio: str) -> float:
        return self.distanciaMetros


class GrafoFalso:
    """Só o que rotas.py usa do Grafo: vertices, existeVertice e getAdjacencias."""

    def __init__(self, arestas: List[Tuple[str, str, float]]) -> None:
        self.vertices = {}
        self._adjacencias = {}
        for origem, destino, peso in arestas:
            for idDoVertice in (origem, destino):
                self.vertices.setdefault(idDoVertice, criarVertice(idDoVertice))
                self._adjacencias.setdefault(idDoVertice, [])
            self._adjacencias[origem].append(ArestaComPesoNegativo(
                origem + destino, self.vertices[origem], self.vertices[destino], peso,
            ))

    def existeVertice(self, idDoVertice: str) -> bool:
        return idDoVertice in self.vertices

    def getAdjacencias(self, idDoVertice: str) -> list:
        return self._adjacencias.get(idDoVertice, [])


# ---------------------------------------------------------------------------
# Critérios: caminho mínimo para cada um, com rotas diferentes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
@pytest.mark.parametrize("criterio, caminhoEsperado, totalEsperado", [
    (CRITERIO_DISTANCIA, ["A", "B", "D"], 200.0),
    (CRITERIO_TEMPO, ["A", "C", "D"], 40.0),
    (CRITERIO_CUSTO, ["A", "E", "D"], 2.0),
])
def test_cada_criterio_escolhe_sua_rota(calcularRota: FuncaoDeRota, criterio, caminhoEsperado,
                                        totalEsperado):
    grafo = montarGrafo(ARESTAS_TRES_CRITERIOS)
    resultado = calcularRota(grafo, "A", "D", criterio)
    assert resultado.situacao == SITUACAO_ENCONTRADA
    assert idsDoCaminho(resultado) == caminhoEsperado
    assert resultado.getTotal(criterio) == pytest.approx(totalEsperado)
    conferirCaminho(grafo, resultado, "A", "D")


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_criterio_aceita_maiusculas_e_espacos(calcularRota: FuncaoDeRota):
    grafo = montarGrafo(ARESTAS_TRES_CRITERIOS)
    assert idsDoCaminho(calcularRota(grafo, "A", "D", "  Tempo ")) == ["A", "C", "D"]
    assert idsDoCaminho(calcularRota(grafo, "A", "D", "DISTANCIA")) == ["A", "B", "D"]


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
@pytest.mark.parametrize("destino", list(DISTANCIAS_DOS_SLIDES))
def test_grafo_dos_slides(calcularRota: FuncaoDeRota, destino):
    grafo = montarGrafoComPesoUnico(ARESTAS_DOS_SLIDES)
    resultado = calcularRota(grafo, "c", destino, CRITERIO_DISTANCIA)
    assert resultado.distanciaTotalMetros == DISTANCIAS_DOS_SLIDES[destino]
    conferirCaminho(grafo, resultado, "c", destino)


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_caminho_do_slide_ate_f(calcularRota: FuncaoDeRota):
    grafo = montarGrafoComPesoUnico(ARESTAS_DOS_SLIDES)
    resultado = calcularRota(grafo, "c", "f", CRITERIO_DISTANCIA)
    assert idsDoCaminho(resultado) == ["c", "e", "b", "d", "f"]


# ---------------------------------------------------------------------------
# Direção, arestas paralelas e empates
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_mao_unica_nao_pode_ser_percorrida_ao_contrario(calcularRota: FuncaoDeRota):
    # anel de mão única A -> B -> C -> A: de B até A só dando a volta por C
    grafo = montarGrafoComPesoUnico([("A", "B", 1.0), ("B", "C", 1.0), ("C", "A", 1.0)])
    resultado = calcularRota(grafo, "B", "A", CRITERIO_DISTANCIA)
    assert idsDoCaminho(resultado) == ["B", "C", "A"]
    assert resultado.distanciaTotalMetros == 2.0


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_mao_unica_sem_volta_e_inalcancavel(calcularRota: FuncaoDeRota):
    grafo = montarGrafoComPesoUnico([("A", "B", 1.0)])
    assert calcularRota(grafo, "A", "B", CRITERIO_DISTANCIA).foiEncontrada()
    assert calcularRota(grafo, "B", "A", CRITERIO_DISTANCIA).situacao == SITUACAO_INALCANCAVEL


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_aresta_paralela_mais_barata_e_escolhida(calcularRota: FuncaoDeRota):
    # a mais cara foi inserida primeiro; pred[] guarda a aresta, não só o vértice
    grafo = montarGrafo([
        ("longa", "A", "B", 300.0, 10.0, 1.0),
        ("curta", "A", "B", 100.0, 50.0, 1.0),
    ])
    porDistancia = calcularRota(grafo, "A", "B", CRITERIO_DISTANCIA)
    porTempo = calcularRota(grafo, "A", "B", CRITERIO_TEMPO)
    assert [aresta.id for aresta in porDistancia.caminho] == ["curta"]
    assert [aresta.id for aresta in porTempo.caminho] == ["longa"]
    assert porDistancia.distanciaTotalMetros == 100.0
    assert porTempo.tempoTotalSegundos == 10.0


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_empate_mantem_a_primeira_estimativa(calcularRota: FuncaoDeRota):
    # A -> D direto custa 2 e é examinada antes de A -> B -> D, que também custa 2;
    # como só relaxamos com "estritamente menor", a aresta direta permanece
    grafo = montarGrafoComPesoUnico([("A", "D", 2.0), ("A", "B", 1.0), ("B", "D", 1.0)])
    resultado = calcularRota(grafo, "A", "D", CRITERIO_DISTANCIA)
    assert idsDoCaminho(resultado) == ["A", "D"]
    assert resultado.distanciaTotalMetros == 2.0


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_empate_entre_dois_caminhos_devolve_um_deles(calcularRota: FuncaoDeRota):
    grafo = montarGrafoComPesoUnico([
        ("A", "B", 1.0), ("B", "D", 1.0), ("A", "C", 1.0), ("C", "D", 1.0),
    ])
    resultado = calcularRota(grafo, "A", "D", CRITERIO_DISTANCIA)
    assert idsDoCaminho(resultado) in (["A", "B", "D"], ["A", "C", "D"])
    assert resultado.distanciaTotalMetros == 2.0


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_aresta_de_peso_zero(calcularRota: FuncaoDeRota):
    grafo = montarGrafoComPesoUnico([("A", "B", 0.0), ("B", "C", 0.0), ("A", "C", 1.0)])
    resultado = calcularRota(grafo, "A", "C", CRITERIO_DISTANCIA)
    assert idsDoCaminho(resultado) == ["A", "B", "C"]
    assert resultado.distanciaTotalMetros == 0.0


# ---------------------------------------------------------------------------
# Casos de borda: origem = destino, inalcançável, pedido inválido
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_origem_igual_ao_destino_tem_custo_zero(calcularRota: FuncaoDeRota):
    grafo = montarGrafoComPesoUnico(ARESTAS_DOS_SLIDES)
    resultado = calcularRota(grafo, "c", "c", CRITERIO_TEMPO)
    assert resultado.situacao == SITUACAO_ENCONTRADA
    assert resultado.caminho == []
    assert resultado.distanciaTotalMetros == 0.0
    assert resultado.tempoTotalSegundos == 0.0
    assert resultado.custoTotalReais == 0.0
    assert resultado.nosExpandidos == 0


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_destino_inalcancavel_tem_estado_proprio(calcularRota: FuncaoDeRota):
    grafo = montarGrafoComPesoUnico([("A", "B", 1.0)])
    grafo.adicionarVertice(criarVertice("Z"))  # vértice isolado
    resultado = calcularRota(grafo, "A", "Z", CRITERIO_DISTANCIA)
    assert resultado.situacao == SITUACAO_INALCANCAVEL
    assert resultado.caminho == []
    assert resultado.distanciaTotalMetros is None
    assert resultado.nosExpandidos > 0  # a busca rodou antes de desistir


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
@pytest.mark.parametrize("origem, destino", [("X", "B"), ("A", "X"), ("X", "Y"), ("X", "X")])
def test_vertice_inexistente_e_pedido_invalido(calcularRota: FuncaoDeRota, origem, destino):
    grafo = montarGrafoComPesoUnico([("A", "B", 1.0)])
    resultado = calcularRota(grafo, origem, destino, CRITERIO_DISTANCIA)
    assert resultado.situacao == SITUACAO_INVALIDA
    assert resultado.situacao != SITUACAO_INALCANCAVEL


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
@pytest.mark.parametrize("criterio", ["velocidade", "", "   ", None, 3])
def test_criterio_invalido_e_pedido_invalido(calcularRota: FuncaoDeRota, criterio):
    grafo = montarGrafoComPesoUnico([("A", "B", 1.0)])
    assert calcularRota(grafo, "A", "B", criterio).situacao == SITUACAO_INVALIDA


@pytest.mark.parametrize("calcularRota", ALGORITMOS)
def test_criterio_com_acento_e_invalido_hoje(calcularRota: FuncaoDeRota):
    # documenta o comportamento atual: normalizarCriterio (grafo.py) não remove
    # acentos, então "Distância" é recusado. Quem chama deve enviar "distancia".
    grafo = montarGrafoComPesoUnico([("A", "B", 1.0)])
    assert calcularRota(grafo, "A", "B", "Distância").situacao == SITUACAO_INVALIDA


# ---------------------------------------------------------------------------
# nosExpandidos: definições diferentes nos dois algoritmos
# ---------------------------------------------------------------------------


def test_dijkstra_conta_vertices_maduros_e_para_no_destino():
    grafo = montarGrafoComPesoUnico(ARESTAS_DOS_SLIDES)
    # ordem de amadurecimento: c, e, b, d, f, a
    assert calcularRotaDijkstra(grafo, "c", "e", CRITERIO_DISTANCIA).nosExpandidos == 2
    assert calcularRotaDijkstra(grafo, "c", "a", CRITERIO_DISTANCIA).nosExpandidos == 6


def test_dijkstra_inalcancavel_amadurece_todos_os_alcancaveis():
    grafo = montarGrafoComPesoUnico(ARESTAS_DOS_SLIDES)
    grafo.adicionarVertice(criarVertice("z"))
    assert calcularRotaDijkstra(grafo, "c", "z", CRITERIO_DISTANCIA).nosExpandidos == 6


def test_bellman_ford_soma_vertices_examinados_por_iteracao():
    # iteração 1 examina os 6 vértices e muda dist; iteração 2 examina os 6 e
    # não muda nada (término antecipado): 6 + 6 = 12, qualquer que seja o destino
    grafo = montarGrafoComPesoUnico(ARESTAS_DOS_SLIDES)
    for destino in ("e", "a"):
        assert calcularRotaBellmanFord(grafo, "c", destino, CRITERIO_DISTANCIA).nosExpandidos == 12


# ---------------------------------------------------------------------------
# Validação cruzada: Dijkstra e Bellman-Ford dão o mesmo custo
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("arestas", [ARESTAS_DOS_SLIDES], ids=["slides"])
def test_validacao_cruzada_grafo_dos_slides(arestas):
    grafo = montarGrafoComPesoUnico(arestas)
    compararAlgoritmos(grafo, todosOsPares(grafo))


def test_validacao_cruzada_grafo_tres_criterios():
    grafo = montarGrafo(ARESTAS_TRES_CRITERIOS)
    compararAlgoritmos(grafo, todosOsPares(grafo))


@pytest.mark.parametrize("semente", SEMENTES)
def test_validacao_cruzada_grafos_aleatorios(semente):
    grafo = gerarGrafoAleatorio(semente)
    compararAlgoritmos(grafo, todosOsPares(grafo))


def test_validacao_cruzada_mapa_real():
    # lê o arquivo local do projeto (sem rede) e compara todos os pares
    grafo = construir_grafo(carregar_mapa(ARQUIVO_MAPA))
    compararAlgoritmos(grafo, todosOsPares(grafo))


# ---------------------------------------------------------------------------
# Pesos negativos (grafo falso): só o Bellman-Ford é correto
# ---------------------------------------------------------------------------


def test_exemplo_do_papel_dijkstra_erra_e_bellman_ford_acerta():
    # s -> a (2), s -> b (3), b -> a (-2): o correto é dist[a] = 1 por s -> b -> a.
    # O Dijkstra declara a maduro com 2 antes de examinar b e devolve o valor errado.
    grafo = GrafoFalso([("s", "a", 2.0), ("s", "b", 3.0), ("b", "a", -2.0)])
    resultadoDijkstra = calcularRotaDijkstra(grafo, "s", "a", CRITERIO_DISTANCIA)
    resultadoBellmanFord = calcularRotaBellmanFord(grafo, "s", "a", CRITERIO_DISTANCIA)
    assert resultadoDijkstra.distanciaTotalMetros == 2.0
    assert resultadoBellmanFord.distanciaTotalMetros == 1.0
    assert idsDoCaminho(resultadoBellmanFord) == ["s", "b", "a"]


def test_bellman_ford_com_peso_negativo_que_exige_varias_iteracoes():
    # ordem dos vértices: s, a, c, b. Na 1ª iteração c é pulado (dist infinita) e
    # só depois b alcança c; c -> a (-3) só é examinada na 2ª iteração
    grafo = GrafoFalso([("s", "a", 5.0), ("c", "a", -3.0), ("b", "c", 1.0), ("s", "b", 4.0)])
    resultado = calcularRotaBellmanFord(grafo, "s", "a", CRITERIO_DISTANCIA)
    assert idsDoCaminho(resultado) == ["s", "b", "c", "a"]
    assert resultado.distanciaTotalMetros == 2.0


def test_bellman_ford_detecta_ciclo_negativo_alcancavel():
    # a -> b -> a custa 1 + (-2) = -1: dá para baixar o custo para sempre
    grafo = GrafoFalso([("s", "a", 1.0), ("a", "b", -2.0), ("b", "a", 1.0), ("b", "t", 1.0)])
    resultado = calcularRotaBellmanFord(grafo, "s", "t", CRITERIO_DISTANCIA)
    assert resultado.situacao == SITUACAO_INVALIDA


def test_bellman_ford_ignora_ciclo_negativo_nao_alcancavel():
    # o ciclo x <-> y é negativo, mas não é alcançável a partir de s
    grafo = GrafoFalso([("s", "t", 1.0), ("x", "y", -2.0), ("y", "x", 1.0)])
    resultado = calcularRotaBellmanFord(grafo, "s", "t", CRITERIO_DISTANCIA)
    assert resultado.situacao == SITUACAO_ENCONTRADA
    assert resultado.distanciaTotalMetros == 1.0


# ---------------------------------------------------------------------------
# Contrato do módulo
# ---------------------------------------------------------------------------


def test_exemplos_das_docstrings_funcionam():
    falhas, _quantidadeDeExemplos = doctest.testmod(rotas)
    assert falhas == 0


def test_rotas_usa_somente_biblioteca_padrao_e_grafo():
    # nenhuma biblioteca externa executa a busca (critério de aceite da Issue 07)
    with open(rotas.__file__, encoding="utf-8") as arquivo:
        arvore = ast.parse(arquivo.read())
    modulosImportados = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            modulosImportados.update(apelido.name for apelido in no.names)
        elif isinstance(no, ast.ImportFrom):
            modulosImportados.add(no.module)
    assert modulosImportados == {"heapq", "typing", "grafo"}
