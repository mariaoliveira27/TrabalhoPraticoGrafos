import heapq
from typing import Dict, List, Optional, Set, Tuple

from grafo import Aresta, Grafo, ResultadoRota, normalizarCriterio


#dist de quem ainda não foi alcançado
DISTANCIA_INFINITA: float = float("inf")


# dist: id do vértice -> melhor custo conhecido desde a origem
DistanciasPorVertice = Dict[str, float]

# pred: id do vértice -> aresta usada para chegar nele (None = indefinido)
PredecessoresPorVertice = Dict[str, Optional[Aresta]]



# Funções compartilhadas pelos dois algoritmos

# Responde sem buscar os pedidos inválidos e o de origem = destino; None = a busca deve rodar.
def _verificarSolicitacao(
    grafo: Grafo, origem: str, destino: str, criterio: str
) -> Optional[ResultadoRota]:
    try:
        normalizarCriterio(criterio)
    except ValueError:
        return ResultadoRota.invalida()
    if not grafo.existeVertice(origem) or not grafo.existeVertice(destino):
        return ResultadoRota.invalida()
    if origem == destino:
        return ResultadoRota.aPartirDoCaminho([], nosExpandidos=0)
    return None


# Cria dist e pred
def _inicializarEstimativas(
    grafo: Grafo, origem: str
) -> Tuple[DistanciasPorVertice, PredecessoresPorVertice]:
    distanciaAteOVertice: DistanciasPorVertice = dict.fromkeys(grafo.vertices, DISTANCIA_INFINITA)
    predecessorDoVertice: PredecessoresPorVertice = dict.fromkeys(grafo.vertices, None)
    distanciaAteOVertice[origem] = 0.0
    return distanciaAteOVertice, predecessorDoVertice


# Relaxa a aresta (v, w) se ela estiver tensa (dist[v] + d(v, w) < dist[w]); devolve se relaxou.
def _relaxarSeTensa(
    arestaDeSaida: Aresta, criterio: str,
    distanciaAteOVertice: DistanciasPorVertice, predecessorDoVertice: PredecessoresPorVertice,
) -> bool:
    novaDistancia = distanciaAteOVertice[arestaDeSaida.origem.id] + arestaDeSaida.getPeso(criterio)
    verticeVizinho = arestaDeSaida.destino.id
    if novaDistancia < distanciaAteOVertice[verticeVizinho]:
        distanciaAteOVertice[verticeVizinho] = novaDistancia
        predecessorDoVertice[verticeVizinho] = arestaDeSaida
        return True
    return False


# Segue o destino até a origem e devolve as arestas na ordem do percurso.
def _reconstruirCaminho(
    predecessorDoVertice: PredecessoresPorVertice, origem: str, destino: str
) -> List[Aresta]:
    caminho: List[Aresta] = []
    verticeDoCaminho = destino
    while verticeDoCaminho != origem:
        arestaUsada = predecessorDoVertice[verticeDoCaminho]
        caminho.append(arestaUsada)
        verticeDoCaminho = arestaUsada.origem.id
    caminho.reverse()
    return caminho


# Transforma dist e pred finais em ResultadoRota 'encontrada' ou 'inalcancavel'.
def _montarResultado(
    distanciaAteOVertice: DistanciasPorVertice, predecessorDoVertice: PredecessoresPorVertice,
    origem: str, destino: str, nosExpandidos: int,
) -> ResultadoRota:
    if distanciaAteOVertice[destino] == DISTANCIA_INFINITA:
        return ResultadoRota.inalcancavel(nosExpandidos)
    caminho = _reconstruirCaminho(predecessorDoVertice, origem, destino)
    return ResultadoRota.aPartirDoCaminho(caminho, nosExpandidos)


# Método de Dijkstra

# Dijkstra: amadurece os vértices em ordem de dist e para quando o destino amadurece.
def calcularRotaDijkstra(
    grafo: Grafo, origem: str, destino: str, criterio: str
) -> ResultadoRota:
    """
    Recebe os ids da origem e do destino e o critério; exige pesos não negativos.
    Devolve ResultadoRota com nosExpandidos = quantidade de vértices declarados maduros.

    >>> from grafo import Aresta, Grafo, Vertice
    >>> praca = Vertice("praca", -19.9240, -43.9930)
    >>> puc = Vertice("puc", -19.9230, -43.9920)
    >>> grafo = Grafo()
    >>> grafo.adicionarAresta(Aresta("rua1", praca, puc, 150.0, 30.0, 18.0, 0.087))
    >>> resultado = calcularRotaDijkstra(grafo, "praca", "puc", "tempo")
    >>> resultado.tempoTotalSegundos, resultado.nosExpandidos
    (18.0, 2)
    >>> calcularRotaDijkstra(grafo, "praca", "puc", "velocidade").situacao
    'invalida'
    """
    resultadoAntecipado = _verificarSolicitacao(grafo, origem, destino, criterio)
    if resultadoAntecipado is not None:
        return resultadoAntecipado
    distanciaAteOVertice, predecessorDoVertice = _inicializarEstimativas(grafo, origem)
    verticesMaduros: Set[str] = set()
    filaDePrioridade: List[Tuple[float, int, str]] = [(0.0, 0, origem)]
    proximoDesempate: int = 1
    while filaDePrioridade:
        distanciaDaEntrada, _desempateDaEntrada, verticeAtual = heapq.heappop(filaDePrioridade)
        if (verticeAtual in verticesMaduros
                or distanciaDaEntrada > distanciaAteOVertice[verticeAtual]):
            continue
        verticesMaduros.add(verticeAtual)
        if verticeAtual == destino:
            break
        for arestaDeSaida in grafo.getAdjacencias(verticeAtual):
            if _relaxarSeTensa(arestaDeSaida, criterio, distanciaAteOVertice, predecessorDoVertice):
                verticeVizinho = arestaDeSaida.destino.id
                entrada = (distanciaAteOVertice[verticeVizinho], proximoDesempate, verticeVizinho)
                heapq.heappush(filaDePrioridade, entrada)
                proximoDesempate += 1
    return _montarResultado(
        distanciaAteOVertice, predecessorDoVertice, origem, destino, len(verticesMaduros)
    )


# Algoritmo de Bellman-Ford

# Bellman-Ford: até |V| - 1 iterações de relaxação e uma passada extra que detecta ciclo negativo.
def calcularRotaBellmanFord(
    grafo: Grafo, origem: str, destino: str, criterio: str
) -> ResultadoRota:
    """
    Mesma entrada e saída do Dijkstra, mas aceita peso negativo e devolve 'invalida' se houver
    ciclo negativo alcançável. nosExpandidos = soma, por iteração, dos vértices examinados.

    >>> from grafo import Aresta, Grafo, Vertice
    >>> praca = Vertice("praca", -19.9240, -43.9930)
    >>> puc = Vertice("puc", -19.9230, -43.9920)
    >>> grafo = Grafo()
    >>> grafo.adicionarAresta(Aresta("rua1", praca, puc, 150.0, 30.0, 18.0, 0.087))
    >>> resultado = calcularRotaBellmanFord(grafo, "praca", "puc", "tempo")
    >>> resultado.tempoTotalSegundos, resultado.nosExpandidos
    (18.0, 2)
    >>> calcularRotaBellmanFord(grafo, "puc", "praca", "tempo").situacao
    'inalcancavel'
    """
    resultadoAntecipado = _verificarSolicitacao(grafo, origem, destino, criterio)
    if resultadoAntecipado is not None:
        return resultadoAntecipado
    distanciaAteOVertice, predecessorDoVertice = _inicializarEstimativas(grafo, origem)
    nosExpandidos: int = 0
    houveRelaxacao: bool = False
    for _numeroDaIteracao in range(len(grafo.vertices) - 1):
        verticesExaminados, houveRelaxacao = _executarIteracaoDeBellmanFord(
            grafo, criterio, distanciaAteOVertice, predecessorDoVertice
        )
        nosExpandidos += verticesExaminados
        if not houveRelaxacao:
            break
    if houveRelaxacao:
        _verticesDaPassadaExtra, aindaHaArestaTensa = _executarIteracaoDeBellmanFord(
            grafo, criterio, distanciaAteOVertice, predecessorDoVertice
        )
        if aindaHaArestaTensa:
            return ResultadoRota.invalida()
    return _montarResultado(
        distanciaAteOVertice, predecessorDoVertice, origem, destino, nosExpandidos
    )


# Relaxa as arestas que saem de cada vértice alcançado e devolve
def _executarIteracaoDeBellmanFord(
    grafo: Grafo, criterio: str,
    distanciaAteOVertice: DistanciasPorVertice, predecessorDoVertice: PredecessoresPorVertice,
) -> Tuple[int, bool]:
    verticesExaminados: int = 0
    houveRelaxacao: bool = False
    for verticeAtual in grafo.vertices:
        if distanciaAteOVertice[verticeAtual] == DISTANCIA_INFINITA:
            continue
        verticesExaminados += 1
        for arestaDeSaida in grafo.getAdjacencias(verticeAtual):
            if _relaxarSeTensa(arestaDeSaida, criterio, distanciaAteOVertice, predecessorDoVertice):
                houveRelaxacao = True
    return verticesExaminados, houveRelaxacao
