"""
Caminho mínimo no grafo viário: Método de Dijkstra e algoritmo de Bellman-Ford.

Recebe um Grafo já montado (grafo.py e mapa.py), os ids da origem e do destino e
um critério ('distancia', 'tempo' ou 'custo') e devolve um ResultadoRota.
Este módulo não lê arquivos, não acessa a internet, não importa a interface e
não usa bibliotecas de grafos prontas: só heapq e typing, da biblioteca padrão.

Funções públicas (mesma entrada e mesma saída):
    calcularRotaDijkstra(grafo, origem, destino, criterio) -> ResultadoRota
    calcularRotaBellmanFord(grafo, origem, destino, criterio) -> ResultadoRota
Os vértices são sempre tratados pelo id (texto), como em Grafo.existeVertice.

Termos dos slides usados nos dois algoritmos:
    dist[] (distanciaAteOVertice): melhor custo conhecido da origem até cada
        vértice; começa infinito, exceto na origem, que começa em zero.
    pred[] (predecessorDoVertice): ARESTA usada para chegar ao vértice. Guardar
        a aresta, e não só o vértice anterior, diferencia as arestas paralelas.
    aresta (v, w) tensa: dist[v] + d(v, w) < dist[w].
    relaxação: dist[w] = dist[v] + d(v, w) e pred[w] = aresta (v, w).
    regra de empate: só relaxamos com "estritamente menor"; com custo igual a
        aresta não está tensa e a primeira estimativa encontrada é mantida.

Resultado (igual nos dois algoritmos):
    critério inválido, origem ou destino inexistente -> ResultadoRota.invalida()
    origem == destino -> 'encontrada', sem arestas, custo zero, 0 nós expandidos
    destino sem caminho -> ResultadoRota.inalcancavel(nosExpandidos)
    caso normal -> ResultadoRota.aPartirDoCaminho(caminho, nosExpandidos)
    só no Bellman-Ford: ciclo de custo negativo alcançável -> ResultadoRota.invalida()

nosExpandidos (os dois números NÃO são diretamente comparáveis):
    Dijkstra: quantidade de vértices declarados maduros.
    Bellman-Ford: soma, em todas as iterações, dos vértices com dist finita
        cujas arestas de saída foram examinadas (o mesmo vértice conta uma vez
        por iteração).

Complexidade (V = vértices, E = arestas):
    Dijkstra com heap e remoção preguiçosa: O((V + E) log E). Cada aresta gera
        no máximo uma inserção na fila, então a fila tem até E + 1 entradas.
        Equivale a O((V + E) log V) quando E <= V² (sem excesso de arestas
        paralelas), porque então log E <= 2 log V.
    Bellman-Ford: O(V · E) no pior caso (V - 1 iterações, cada uma examinando
        até E arestas); o término antecipado costuma parar bem antes.

"""

import heapq
from typing import Dict, List, Optional, Set, Tuple

from grafo import Aresta, Grafo, ResultadoRota, normalizarCriterio

# "Infinito" dos slides: valor inicial de dist[] para vértice ainda não alcançado.
DISTANCIA_INFINITA: float = float("inf")

# Custo para ir da origem até ela mesma; é o valor inicial de dist[origem].
DISTANCIA_DA_ORIGEM: float = 0.0

# Nós expandidos quando a busca nem precisa rodar (origem igual ao destino).
NENHUM_NO_EXPANDIDO: int = 0

# dist[]: id do vértice -> melhor custo conhecido desde a origem.
DistanciasPorVertice = Dict[str, float]

# pred[]: id do vértice -> aresta usada para chegar nele (None = indefinido).
PredecessoresPorVertice = Dict[str, Optional[Aresta]]

# Entrada da fila de prioridade: (distância estimada, contador de desempate, id).
EntradaDaFila = Tuple[float, int, str]


# ---------------------------------------------------------------------------
# Funções compartilhadas pelos dois algoritmos
# ---------------------------------------------------------------------------


def _tentarNormalizarCriterio(criterio: str) -> Optional[str]:
    """Devolve 'distancia', 'tempo' ou 'custo', ou None se o critério for inválido."""
    # normalizarCriterio (grafo.py) aceita maiúsculas e espaços extras e lança
    # ValueError para critério desconhecido; trocamos a exceção por None para o
    # pedido virar ResultadoRota 'invalida' em vez de quebrar quem chamou
    try:
        return normalizarCriterio(criterio)
    except ValueError:
        return None


def _verificarSolicitacao(
    grafo: Grafo,
    origem: str,
    destino: str,
    criterioNormalizado: Optional[str],
) -> Optional[ResultadoRota]:
    """
    Resolve os pedidos que não precisam de busca.

    Devolve um ResultadoRota pronto (inválido, ou de custo zero quando
    origem = destino) ou None quando a busca precisa rodar.
    """
    # critério inválido: _tentarNormalizarCriterio devolveu None
    if criterioNormalizado is None:
        return ResultadoRota.invalida()
    # vértice inexistente é pedido inválido, e não falta de caminho; checar aqui
    # é obrigatório, pois getAdjacencias devolve lista vazia para id inexistente
    if not grafo.existeVertice(origem) or not grafo.existeVertice(destino):
        return ResultadoRota.invalida()
    # origem igual ao destino: rota sem arestas, custo zero, ninguém expandido
    if origem == destino:
        return ResultadoRota.aPartirDoCaminho([], nosExpandidos=NENHUM_NO_EXPANDIDO)
    # pedido válido e não trivial: None avisa que a busca precisa rodar
    return None


def _listarIdsDosVertices(grafo: Grafo) -> List[str]:
    """Devolve os ids de todos os vértices do grafo, na ordem de inserção."""
    # o Grafo não tem método que liste os vértices; a propriedade grafo.vertices
    # é um dicionário id -> Vertice, então suas chaves são os ids. A lista é
    # montada uma vez por chamada de busca e depois reaproveitada
    return list(grafo.vertices.keys())


def _inicializarEstimativas(
    idsDosVertices: List[str],
    origem: str,
) -> Tuple[DistanciasPorVertice, PredecessoresPorVertice]:
    """Cria dist[] (infinito, exceto a origem = 0) e pred[] (todos indefinidos)."""
    # dist[] e pred[] dos slides, indexados pelo id do vértice
    distanciaAteOVertice: DistanciasPorVertice = {}
    predecessorDoVertice: PredecessoresPorVertice = {}
    # todo vértice começa sem caminho conhecido: distância infinita, sem predecessor
    for idDoVertice in idsDosVertices:
        distanciaAteOVertice[idDoVertice] = DISTANCIA_INFINITA
        predecessorDoVertice[idDoVertice] = None
    # a origem é a raiz da busca: chegar nela custa zero
    distanciaAteOVertice[origem] = DISTANCIA_DA_ORIGEM
    return distanciaAteOVertice, predecessorDoVertice


def _verticeFoiAlcancado(distanciaAteOVertice: DistanciasPorVertice, idDoVertice: str) -> bool:
    """Indica se já existe algum caminho conhecido da origem até o vértice."""
    # dist finita: algum caminho já chegou nele; dist infinita: ainda não
    return distanciaAteOVertice[idDoVertice] < DISTANCIA_INFINITA


def _calcularNovaDistanciaEstimada(
    arestaDeSaida: Aresta,
    criterio: str,
    distanciaAteOVertice: DistanciasPorVertice,
) -> float:
    """Calcula dist[v] + d(v, w) para a aresta (v, w) no critério escolhido."""
    # v é a origem da aresta; getPeso devolve metros, segundos ou reais,
    # conforme o critério (pesos negativos já são rejeitados pela classe Aresta)
    verticeAtual = arestaDeSaida.origem.id
    return distanciaAteOVertice[verticeAtual] + arestaDeSaida.getPeso(criterio)


def _arestaEstaTensa(
    arestaDeSaida: Aresta,
    criterio: str,
    distanciaAteOVertice: DistanciasPorVertice,
) -> bool:
    """Indica se a aresta (v, w) está tensa: dist[v] + d(v, w) < dist[w]."""
    # w é o destino da aresta; calcula quanto custaria chegar em w passando por v
    verticeVizinho = arestaDeSaida.destino.id
    novaDistanciaEstimada = _calcularNovaDistanciaEstimada(
        arestaDeSaida, criterio, distanciaAteOVertice
    )
    # regra de empate: comparação estritamente menor; com custo igual a aresta
    # é "justa", não tensa, e a estimativa que já estava em dist[w] é mantida
    return novaDistanciaEstimada < distanciaAteOVertice[verticeVizinho]


def _tentarRelaxarAresta(
    arestaDeSaida: Aresta,
    criterio: str,
    distanciaAteOVertice: DistanciasPorVertice,
    predecessorDoVertice: PredecessoresPorVertice,
) -> bool:
    """
    Relaxa a aresta (v, w) se ela estiver tensa.

    Devolve True quando dist[w] e pred[w] foram atualizados e False caso contrário.
    """
    # aresta não tensa: passar por ela não melhora dist[w], então nada muda
    if not _arestaEstaTensa(arestaDeSaida, criterio, distanciaAteOVertice):
        return False
    # relaxação: achamos caminho melhor até w, então atualiza dist[w] e guarda
    # em pred[w] a própria aresta usada (e não só v), por causa das paralelas
    verticeVizinho = arestaDeSaida.destino.id
    distanciaAteOVertice[verticeVizinho] = _calcularNovaDistanciaEstimada(
        arestaDeSaida, criterio, distanciaAteOVertice
    )
    predecessorDoVertice[verticeVizinho] = arestaDeSaida
    return True


def _reconstruirCaminho(
    predecessorDoVertice: PredecessoresPorVertice,
    origem: str,
    destino: str,
) -> List[Aresta]:
    """
    Monta a lista de arestas da origem até o destino seguindo pred[].

    Pré-condição: o destino foi alcançado, então a cadeia de predecessores
    termina na origem (pred[] forma uma árvore com raiz na origem).
    """
    # começa pelo destino, com a lista de arestas ainda vazia
    arestasDoDestinoAteAOrigem: List[Aresta] = []
    verticeDoCaminho = destino
    # anda para trás: pega a aresta usada para chegar no vértice e passa para a
    # origem dessa aresta, até voltar à raiz da busca
    while verticeDoCaminho != origem:
        arestaUsada = predecessorDoVertice[verticeDoCaminho]
        arestasDoDestinoAteAOrigem.append(arestaUsada)
        verticeDoCaminho = arestaUsada.origem.id
    # as arestas vieram do destino para a origem; inverte para a ordem do percurso
    caminhoNaOrdemDoPercurso = list(reversed(arestasDoDestinoAteAOrigem))
    return caminhoNaOrdemDoPercurso


def _montarResultado(
    distanciaAteOVertice: DistanciasPorVertice,
    predecessorDoVertice: PredecessoresPorVertice,
    origem: str,
    destino: str,
    nosExpandidos: int,
) -> ResultadoRota:
    """Transforma dist[] e pred[] finais em ResultadoRota (encontrada ou inalcançável)."""
    # dist[destino] continuou infinita: nenhum caminho chega ao destino
    if not _verticeFoiAlcancado(distanciaAteOVertice, destino):
        return ResultadoRota.inalcancavel(nosExpandidos)
    # caso normal: aPartirDoCaminho soma os pesos das próprias arestas do
    # caminho, então os totais informados batem com a soma das arestas
    caminho = _reconstruirCaminho(predecessorDoVertice, origem, destino)
    return ResultadoRota.aPartirDoCaminho(caminho, nosExpandidos)
