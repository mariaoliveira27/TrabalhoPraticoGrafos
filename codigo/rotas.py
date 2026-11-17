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

Exemplo:
    >>> from grafo import Aresta, Grafo, Vertice
    >>> praca = Vertice("praca", -19.9240, -43.9930)
    >>> puc = Vertice("puc", -19.9230, -43.9920)
    >>> grafo = Grafo()
    >>> grafo.adicionarAresta(Aresta("rua1", praca, puc, 150.0, 30.0, 18.0, 0.087))
    >>> calcularRotaDijkstra(grafo, "praca", "puc", "distancia").distanciaTotalMetros
    150.0
    >>> calcularRotaBellmanFord(grafo, "puc", "praca", "distancia").situacao
    'inalcancavel'
    >>> calcularRotaDijkstra(grafo, "praca", "puc", "velocidade").situacao
    'invalida'
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


# ---------------------------------------------------------------------------
# Método de Dijkstra (slides "Caminho Mínimo (1)")
# ---------------------------------------------------------------------------


def calcularRotaDijkstra(
    grafo: Grafo,
    origem: str,
    destino: str,
    criterio: str,
) -> ResultadoRota:
    """
    Calcula a rota de menor custo de origem até destino pelo Método de Dijkstra.

    Exige pesos não negativos, o que a classe Aresta já garante. A busca para
    assim que o destino é declarado maduro.

    Parâmetros:
        grafo: grafo dirigido já montado (por exemplo, por mapa.construir_grafo).
        origem: id do vértice de partida.
        destino: id do vértice de chegada.
        criterio: 'distancia' (m), 'tempo' (s) ou 'custo' (R$). Aceita maiúsculas
            e espaços extras, mas não acentos ('Distância' é inválido).

    Retorna:
        ResultadoRota com situação 'encontrada' (caminho e totais),
        'inalcancavel' ou 'invalida'. nosExpandidos = vértices declarados maduros.

    Exemplo:
        >>> from grafo import Aresta, Grafo, Vertice
        >>> praca = Vertice("praca", -19.9240, -43.9930)
        >>> puc = Vertice("puc", -19.9230, -43.9920)
        >>> grafo = Grafo()
        >>> grafo.adicionarAresta(Aresta("rua1", praca, puc, 150.0, 30.0, 18.0, 0.087))
        >>> resultado = calcularRotaDijkstra(grafo, "praca", "puc", "tempo")
        >>> resultado.tempoTotalSegundos, resultado.nosExpandidos
        (18.0, 2)
    """
    # 1) valida o pedido; inválido ou origem = destino já sai aqui
    criterioNormalizado = _tentarNormalizarCriterio(criterio)
    resultadoAntecipado = _verificarSolicitacao(grafo, origem, destino, criterioNormalizado)
    if resultadoAntecipado is not None:
        return resultadoAntecipado
    # 2) dist[] infinito (origem = 0) e pred[] indefinido
    distanciaAteOVertice, predecessorDoVertice = _inicializarEstimativas(
        _listarIdsDosVertices(grafo), origem
    )
    # 3) laço principal dos slides: seleciona o imaturo, relaxa, declara maduro
    nosExpandidos = _executarLacoDeDijkstra(
        grafo, origem, destino, criterioNormalizado, distanciaAteOVertice, predecessorDoVertice
    )
    # 4) reconstrói o caminho por pred[] e monta o ResultadoRota
    return _montarResultado(
        distanciaAteOVertice, predecessorDoVertice, origem, destino, nosExpandidos
    )


def _executarLacoDeDijkstra(
    grafo: Grafo,
    origem: str,
    destino: str,
    criterio: str,
    distanciaAteOVertice: DistanciasPorVertice,
    predecessorDoVertice: PredecessoresPorVertice,
) -> int:
    """
    Laço principal do Dijkstra; atualiza dist[] e pred[] no próprio dicionário.

    Devolve nosExpandidos: quantos vértices foram declarados maduros.
    """
    # maduros: vértices cuja distância já é definitiva; a fila guarda candidatos
    verticesMaduros: Set[str] = set()
    filaDePrioridade = _FilaDePrioridade()
    # no início só a origem tem estimativa finita, então só ela entra na fila
    filaDePrioridade.inserir(distanciaAteOVertice[origem], origem)
    # repete enquanto houver candidato; fila vazia = nada mais é alcançável
    while not filaDePrioridade.estaVazia():
        # seleciona o imaturo v que minimiza dist (a menor entrada da fila);
        # entradas velhas, deixadas pela remoção preguiçosa, são puladas
        distanciaDaEntrada, verticeAtual = filaDePrioridade.retirarMenor()
        if _entradaEstaDesatualizada(
            distanciaDaEntrada, verticeAtual, verticesMaduros, distanciaAteOVertice
        ):
            continue
        # v é declarado maduro. Nos slides isso vem depois de examinar as arestas
        # de v; fazer antes dá no mesmo com pesos não negativos (nenhuma aresta de
        # v melhora dist[v]) e permite parar no destino sem examinar as dele
        verticesMaduros.add(verticeAtual)
        # o destino amadureceu: seu caminho mínimo já é conhecido, pode parar
        if verticeAtual == destino:
            break
        # examina cada aresta (v, w); se estava tensa e foi relaxada, w entra
        # (de novo) na fila com a nova estimativa
        for arestaDeSaida in grafo.getAdjacencias(verticeAtual):
            if _tentarRelaxarAresta(
                arestaDeSaida, criterio, distanciaAteOVertice, predecessorDoVertice
            ):
                verticeVizinho = arestaDeSaida.destino.id
                filaDePrioridade.inserir(distanciaAteOVertice[verticeVizinho], verticeVizinho)
    return len(verticesMaduros)


def _entradaEstaDesatualizada(
    distanciaDaEntrada: float,
    verticeAtual: str,
    verticesMaduros: Set[str],
    distanciaAteOVertice: DistanciasPorVertice,
) -> bool:
    """Indica se uma entrada retirada da fila deve ser ignorada (remoção preguiçosa)."""
    # remoção preguiçosa: o heapq não sabe "diminuir a chave" de uma entrada.
    # Quando dist[w] melhora, w é inserido de novo e a entrada antiga continua
    # na fila. Ela é ignorada ao sair se o vértice já está maduro...
    if verticeAtual in verticesMaduros:
        return True
    # ...ou se a distância da entrada é maior que dist atual (estimativa velha)
    return distanciaDaEntrada > distanciaAteOVertice[verticeAtual]


class _FilaDePrioridade:
    """
    Fila de prioridade mínima (heap) dos vértices candidatos a maduro.

    Cada entrada é (distância estimada, contador de desempate, id do vértice).
    O contador cresce a cada inserção: com distâncias iguais sai primeiro quem
    entrou primeiro, e o heapq nunca precisa comparar os ids entre si.
    """

    def __init__(self) -> None:
        # lista organizada como heap pelo heapq; menor entrada na posição 0
        self._entradas: List[EntradaDaFila] = []
        self._proximoContadorDeDesempate: int = 0

    def inserir(self, distanciaEstimada: float, idDoVertice: str) -> None:
        """Coloca o vértice na fila com a distância estimada atual."""
        # heappush mantém a propriedade de heap em O(log n); depois avança o
        # contador para a próxima inserção ter desempate maior
        entrada: EntradaDaFila = (distanciaEstimada, self._proximoContadorDeDesempate, idDoVertice)
        heapq.heappush(self._entradas, entrada)
        self._proximoContadorDeDesempate += 1

    def retirarMenor(self) -> Tuple[float, str]:
        """Remove a entrada de menor distância e devolve (distância, id do vértice)."""
        # heappop tira a menor entrada em O(log n); o contador só servia para ordenar
        distanciaDaEntrada, _contadorDeDesempate, idDoVertice = heapq.heappop(self._entradas)
        return distanciaDaEntrada, idDoVertice

    def estaVazia(self) -> bool:
        """Indica se não há mais entradas na fila."""
        # lista vazia: nenhum candidato restante
        return len(self._entradas) == 0


# ---------------------------------------------------------------------------
# Algoritmo de Bellman-Ford (slides "Caminho Mínimo (2)")
# ---------------------------------------------------------------------------


def calcularRotaBellmanFord(
    grafo: Grafo,
    origem: str,
    destino: str,
    criterio: str,
) -> ResultadoRota:
    """
    Calcula a rota de menor custo de origem até destino pelo algoritmo de Bellman-Ford.

    Faz até |V| - 1 iterações relaxando todas as arestas tensas, com término
    antecipado quando uma iteração não muda nada. Funciona também com pesos
    negativos e detecta ciclo de custo negativo alcançável (nesse caso devolve
    'invalida'). Com o Grafo real isso nunca ocorre, pois a classe Aresta rejeita
    peso negativo; a detecção existe porque faz parte do algoritmo.

    Parâmetros:
        grafo: grafo dirigido já montado (por exemplo, por mapa.construir_grafo).
        origem: id do vértice de partida.
        destino: id do vértice de chegada.
        criterio: 'distancia' (m), 'tempo' (s) ou 'custo' (R$). Aceita maiúsculas
            e espaços extras, mas não acentos ('Distância' é inválido).

    Retorna:
        ResultadoRota com situação 'encontrada' (caminho e totais),
        'inalcancavel' ou 'invalida'. nosExpandidos = soma, nas iterações, dos
        vértices alcançados cujas arestas de saída foram examinadas.

    Exemplo:
        >>> from grafo import Aresta, Grafo, Vertice
        >>> praca = Vertice("praca", -19.9240, -43.9930)
        >>> puc = Vertice("puc", -19.9230, -43.9920)
        >>> grafo = Grafo()
        >>> grafo.adicionarAresta(Aresta("rua1", praca, puc, 150.0, 30.0, 18.0, 0.087))
        >>> resultado = calcularRotaBellmanFord(grafo, "praca", "puc", "tempo")
        >>> resultado.tempoTotalSegundos, resultado.nosExpandidos
        (18.0, 2)
    """
    # 1) mesma validação do Dijkstra; inválido ou origem = destino já sai aqui
    criterioNormalizado = _tentarNormalizarCriterio(criterio)
    resultadoAntecipado = _verificarSolicitacao(grafo, origem, destino, criterioNormalizado)
    if resultadoAntecipado is not None:
        return resultadoAntecipado
    # 2) mesma inicialização; a lista de ids é montada uma vez e reaproveitada
    #    em todas as iterações
    idsDosVertices = _listarIdsDosVertices(grafo)
    distanciaAteOVertice, predecessorDoVertice = _inicializarEstimativas(idsDosVertices, origem)
    # 3) até |V| - 1 iterações relaxando as arestas tensas
    nosExpandidos, ultimaIteracaoRelaxou = _executarIteracoesDeBellmanFord(
        grafo, idsDosVertices, criterioNormalizado, distanciaAteOVertice, predecessorDoVertice
    )
    # 4) se parou antes do limite, nenhuma aresta está tensa e não há ciclo
    #    negativo; se rodou as |V| - 1 e a última ainda relaxou, passada extra
    if ultimaIteracaoRelaxou:
        # aresta ainda tensa = ciclo de custo negativo alcançável: não existe
        # caminho mínimo, então o pedido é inválido (invalida() não aceita mensagem)
        if _existeArestaTensa(grafo, idsDosVertices, criterioNormalizado, distanciaAteOVertice):
            return ResultadoRota.invalida()
    # 5) igual ao Dijkstra: reconstrói o caminho por pred[] e monta o ResultadoRota
    return _montarResultado(
        distanciaAteOVertice, predecessorDoVertice, origem, destino, nosExpandidos
    )


def _executarIteracoesDeBellmanFord(
    grafo: Grafo,
    idsDosVertices: List[str],
    criterio: str,
    distanciaAteOVertice: DistanciasPorVertice,
    predecessorDoVertice: PredecessoresPorVertice,
) -> Tuple[int, bool]:
    """
    Repete até |V| - 1 iterações, parando antes se uma iteração não relaxar nada.

    Devolve (nosExpandidos somados em todas as iterações, se a última iteração
    executada ainda relaxou alguma aresta).
    """
    # um caminho mínimo sem ciclo tem no máximo |V| - 1 arestas, e ao fim da
    # iteração k os caminhos mínimos de até k arestas já estão em dist[]
    quantidadeMaximaDeIteracoes = len(idsDosVertices) - 1
    # contadores: nós expandidos somados e se a iteração mais recente relaxou algo
    nosExpandidos = 0
    houveRelaxacao = False
    for _numeroDaIteracao in range(quantidadeMaximaDeIteracoes):
        # uma iteração = examinar todas as arestas e relaxar as tensas
        verticesExaminados, houveRelaxacao = _executarUmaIteracaoDeBellmanFord(
            grafo, idsDosVertices, criterio, distanciaAteOVertice, predecessorDoVertice
        )
        nosExpandidos += verticesExaminados
        # término antecipado: iteração sem relaxação deixa dist[] igual, e as
        # próximas repetiriam a mesma passada sem mudar nada
        if not houveRelaxacao:
            break
    return nosExpandidos, houveRelaxacao


def _executarUmaIteracaoDeBellmanFord(
    grafo: Grafo,
    idsDosVertices: List[str],
    criterio: str,
    distanciaAteOVertice: DistanciasPorVertice,
    predecessorDoVertice: PredecessoresPorVertice,
) -> Tuple[int, bool]:
    """
    Examina as arestas de saída de cada vértice alcançado e relaxa as tensas.

    Devolve (vértices examinados nesta iteração, se alguma aresta foi relaxada).
    """
    # contadores desta iteração
    verticesExaminados = 0
    houveRelaxacao = False
    # percorre os vértices na ordem de inserção; uma melhora feita nesta
    # iteração já vale para os vértices que vêm depois na lista
    for verticeAtual in idsDosVertices:
        # dist infinita: infinito + peso continua infinito e não torna nenhuma
        # aresta tensa, então o vértice é pulado (e não conta como expandido)
        if not _verticeFoiAlcancado(distanciaAteOVertice, verticeAtual):
            continue
        verticesExaminados += 1
        # examina cada aresta de saída e relaxa as tensas, como no Dijkstra
        for arestaDeSaida in grafo.getAdjacencias(verticeAtual):
            if _tentarRelaxarAresta(
                arestaDeSaida, criterio, distanciaAteOVertice, predecessorDoVertice
            ):
                houveRelaxacao = True
    return verticesExaminados, houveRelaxacao


def _existeArestaTensa(
    grafo: Grafo,
    idsDosVertices: List[str],
    criterio: str,
    distanciaAteOVertice: DistanciasPorVertice,
) -> bool:
    """Passada extra do Bellman-Ford: procura uma aresta ainda tensa, sem relaxar nada."""
    # mesma varredura de uma iteração, mas só pergunta se a aresta está tensa
    for verticeAtual in idsDosVertices:
        # vértice não alcançado não tem aresta tensa (mesmo motivo da iteração)
        if not _verticeFoiAlcancado(distanciaAteOVertice, verticeAtual):
            continue
        # basta uma aresta tensa para provar que existe ciclo negativo alcançável
        for arestaDeSaida in grafo.getAdjacencias(verticeAtual):
            if _arestaEstaTensa(arestaDeSaida, criterio, distanciaAteOVertice):
                return True
    return False
