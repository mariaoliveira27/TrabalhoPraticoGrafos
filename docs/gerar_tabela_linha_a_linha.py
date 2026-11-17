"""
Gera as tabelas de docs/roteiro_rotas.md que citam linhas de codigo/rotas.py.

    - seção 2 (tabela linha a linha): uma linha da tabela por linha de código; comentários
      seguidos e docstrings viram intervalos. A explicação de cada linha de código vem do
      dicionário EXPLICACOES abaixo, pela chave (função, código);
    - seção 1.3: atualiza a coluna "linhas" da tabela de funções;
    - seção 1.4: refaz a tabela dos critérios de aceite da Issue 07 a partir de ÂNCORAS
      (trechos de código), para os números de linha nunca ficarem velhos.

Uso (na raiz do repositório), depois de qualquer mudança em rotas.py:
    python docs/gerar_tabela_linha_a_linha.py
    python docs/conferir_roteiro.py
Se faltar explicação para alguma linha de código, sobrar explicação sem linha ou uma
âncora não for encontrada, o script lista os problemas, sai com código 1 e NÃO altera o
roteiro. Nesse caso, edite EXPLICACOES ou CRITERIOS_DA_ISSUE_07 e rode de novo.
"""

import ast
import glob
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

PASTA_DOCS = os.path.dirname(os.path.abspath(__file__))
PASTA_CODIGO = os.path.join(os.path.dirname(PASTA_DOCS), "codigo")
CAMINHO_ROTEIRO = os.path.join(PASTA_DOCS, "roteiro_rotas.md")
CAMINHO_ROTAS = os.path.join(PASTA_CODIGO, "rotas.py")
MARCADORES_DA_TABELA = ("<!-- tabela-linha-a-linha:inicio -->", "<!-- tabela-linha-a-linha:fim -->")
MARCADORES_DE_FUNCOES = ("<!-- funcoes:inicio -->", "<!-- funcoes:fim -->")
MARCADORES_DE_CRITERIOS = ("<!-- criterios-issue-07:inicio -->", "<!-- criterios-issue-07:fim -->")
LINHA_DA_TABELA_DE_FUNCOES = re.compile(r"^(\| \d+ \| `(\w+)` \| )\d+–\d+( \|.*)$")
MODULO = ""  # "função" das linhas que ficam fora de qualquer def

# Explicação de cada linha de código, pela chave (função, código sem a indentação).
# Uma chave vale para todas as linhas iguais dentro da mesma função.
EXPLICACOES: Dict[Tuple[str, str], str] = {
    # módulo
    (MODULO, "import heapq"):
        "Importa o `heapq`, da biblioteca padrão: funções que tratam uma lista comum como "
        "heap mínimo (fila de prioridade). Só o Dijkstra usa.",
    (MODULO, "from typing import Dict, List, Optional, Set, Tuple"):
        "Tipos das anotações: `Dict`, `List`, `Optional` (valor ou `None`), `Set` e `Tuple`. "
        "Anotações não mudam a execução; documentam o que entra e sai.",
    (MODULO, "from grafo import Aresta, Grafo, ResultadoRota, normalizarCriterio"):
        "Reaproveita o grafo.py: `Aresta` e `Grafo` (anotações e leitura), `ResultadoRota` "
        "(o que devolvemos) e `normalizarCriterio` (valida o critério).",
    (MODULO, 'DISTANCIA_INFINITA: float = float("inf")'):
        "O infinito do Python. Qualquer número finito é menor que ele, então serve como "
        "estimativa inicial de \"nenhum caminho conhecido\".",
    (MODULO, "DistanciasPorVertice = Dict[str, float]"):
        "Apelido de tipo para dist[]: dicionário id (texto) -> custo (float). Só encurta as "
        "assinaturas.",
    (MODULO, "PredecessoresPorVertice = Dict[str, Optional[Aresta]]"):
        "Apelido de tipo para pred[]: id -> `Aresta` ou `None`. Guarda a aresta, e não o "
        "vértice, para distinguir arestas paralelas.",
    # _verificarSolicitacao
    ("_verificarSolicitacao", "def _verificarSolicitacao("):
        "Define a função que resolve os pedidos que não precisam de busca. O `_` no início "
        "indica uso interno do módulo.",
    ("_verificarSolicitacao", "grafo: Grafo, origem: str, destino: str, criterio: str"):
        "Parâmetros: o grafo, os ids (texto) da origem e do destino e o critério como foi "
        "digitado.",
    ("_verificarSolicitacao", ") -> Optional[ResultadoRota]:"):
        "Devolve um `ResultadoRota` pronto ou `None` (\"pode buscar\").",
    ("_verificarSolicitacao", "try:"):
        "Abre um bloco protegido: se a linha seguinte lançar `ValueError`, a execução pula "
        "para o `except`.",
    ("_verificarSolicitacao", "normalizarCriterio(criterio)"):
        "Só valida: tira espaços, passa para minúsculas e confere se é 'distancia', 'tempo' "
        "ou 'custo'. O valor limpo não precisa ser guardado, porque `getPeso` normaliza o "
        "critério sozinho.",
    ("_verificarSolicitacao", "except ValueError:"):
        "Captura só `ValueError` (critério desconhecido, vazio, `None` ou número).",
    ("_verificarSolicitacao", "return ResultadoRota.invalida()"):
        "Pedido inválido: resultado 'invalida', sem caminho e sem totais.",
    ("_verificarSolicitacao",
     "if not grafo.existeVertice(origem) or not grafo.existeVertice(destino):"):
        "Basta um dos dois não existir. Sem esta checagem, `getAdjacencias` devolveria lista "
        "vazia e o pedido sairia, errado, como 'inalcancavel'.",
    ("_verificarSolicitacao", "if origem == destino:"):
        "Caso trivial: partida e chegada são o mesmo vértice.",
    ("_verificarSolicitacao", "return ResultadoRota.aPartirDoCaminho([], nosExpandidos=0)"):
        "Rota 'encontrada' com caminho vazio: soma de zero arestas, então distância, tempo e "
        "custo valem 0, e nosExpandidos = 0.",
    ("_verificarSolicitacao", "return None"):
        "Nenhum caso especial: quem chamou segue para a busca.",
    # _inicializarEstimativas
    ("_inicializarEstimativas", "def _inicializarEstimativas("):
        "Define a inicialização de dist[] e pred[], igual nos dois algoritmos.",
    ("_inicializarEstimativas", "grafo: Grafo, origem: str"):
        "Parâmetros: o grafo (de onde saem os ids) e a origem, raiz da busca.",
    ("_inicializarEstimativas", ") -> Tuple[DistanciasPorVertice, PredecessoresPorVertice]:"):
        "Devolve as duas estruturas juntas numa tupla (dist, pred).",
    ("_inicializarEstimativas",
     "distanciaAteOVertice: DistanciasPorVertice = dict.fromkeys(grafo.vertices, DISTANCIA_INFINITA)"):
        "`dict.fromkeys` cria um dicionário com uma chave por id de `grafo.vertices` (na "
        "ordem de inserção) e o mesmo valor em todas: infinito. Custo O(V).",
    ("_inicializarEstimativas",
     "predecessorDoVertice: PredecessoresPorVertice = dict.fromkeys(grafo.vertices, None)"):
        "Mesma coisa para pred[]: todo predecessor começa indefinido (`None`).",
    ("_inicializarEstimativas", "distanciaAteOVertice[origem] = 0.0"):
        "Sobrescreve a origem: chegar nela custa zero.",
    ("_inicializarEstimativas", "return distanciaAteOVertice, predecessorDoVertice"):
        "Devolve a tupla; quem chama desempacota em duas variáveis.",
    # _relaxarSeTensa
    ("_relaxarSeTensa", "def _relaxarSeTensa("):
        "Define a relaxação dos slides, usada pelos dois algoritmos.",
    ("_relaxarSeTensa", "arestaDeSaida: Aresta, criterio: str,"):
        "Parâmetros: a aresta (v, w) examinada e o critério, que decide qual peso dela vale.",
    ("_relaxarSeTensa",
     "distanciaAteOVertice: DistanciasPorVertice, predecessorDoVertice: PredecessoresPorVertice,"):
        "Parâmetros: dist[] e pred[]. Os dois dicionários são alterados aqui dentro (o Python "
        "passa a referência do objeto, não uma cópia).",
    ("_relaxarSeTensa", ") -> bool:"):
        "Devolve se houve relaxação. O Dijkstra usa isso para inserir w no heap; o "
        "Bellman-Ford, para saber se a iteração mudou algo.",
    ("_relaxarSeTensa",
     "novaDistancia = distanciaAteOVertice[arestaDeSaida.origem.id] + arestaDeSaida.getPeso(criterio)"):
        "dist[v] + d(v, w), calculado uma única vez. `arestaDeSaida.origem.id` é o id de v; "
        "`getPeso` devolve metros, segundos ou reais conforme o critério.",
    ("_relaxarSeTensa", "verticeVizinho = arestaDeSaida.destino.id"):
        "O id de w, o destino da aresta, que é a chave usada três vezes a seguir.",
    ("_relaxarSeTensa", "if novaDistancia < distanciaAteOVertice[verticeVizinho]:"):
        "Definição de aresta tensa dos slides: dist[v] + d(v, w) < dist[w]. O `<` estrito é a "
        "regra de empate: custo igual não conta como melhora. Isso também impede que arestas "
        "de peso zero formem ciclos em pred[].",
    ("_relaxarSeTensa", "distanciaAteOVertice[verticeVizinho] = novaDistancia"):
        "Relaxação, parte 1: dist[w] recebe a nova estimativa (o mesmo valor já calculado).",
    ("_relaxarSeTensa", "predecessorDoVertice[verticeVizinho] = arestaDeSaida"):
        "Relaxação, parte 2: pred[w] recebe a própria aresta usada. Com arestas paralelas, é "
        "isso que diz qual delas foi escolhida.",
    ("_relaxarSeTensa", "return True"):
        "Informa que dist[w] e pred[w] mudaram.",
    ("_relaxarSeTensa", "return False"):
        "Aresta não tensa: nada mudou.",
    # _reconstruirCaminho
    ("_reconstruirCaminho", "def _reconstruirCaminho("):
        "Define a reconstrução do caminho a partir de pred[].",
    ("_reconstruirCaminho",
     "predecessorDoVertice: PredecessoresPorVertice, origem: str, destino: str"):
        "Parâmetros: pred[] final, a origem (onde a caminhada termina) e o destino (onde ela "
        "começa).",
    ("_reconstruirCaminho", ") -> List[Aresta]:"):
        "Devolve a lista de arestas na ordem do percurso.",
    ("_reconstruirCaminho", "caminho: List[Aresta] = []"):
        "Lista onde as arestas são coletadas, de trás para frente.",
    ("_reconstruirCaminho", "verticeDoCaminho = destino"):
        "A caminhada começa no destino.",
    ("_reconstruirCaminho", "while verticeDoCaminho != origem:"):
        "Repete até chegar à origem (a origem não tem predecessor).",
    ("_reconstruirCaminho", "arestaUsada = predecessorDoVertice[verticeDoCaminho]"):
        "Lê em pred[] a aresta usada para chegar neste vértice.",
    ("_reconstruirCaminho", "caminho.append(arestaUsada)"):
        "Guarda a aresta na lista.",
    ("_reconstruirCaminho", "verticeDoCaminho = arestaUsada.origem.id"):
        "Volta um passo: o próximo vértice é a origem dessa aresta.",
    ("_reconstruirCaminho", "caminho.reverse()"):
        "Inverte a lista no lugar: agora ela vai da origem ao destino.",
    ("_reconstruirCaminho", "return caminho"):
        "Devolve o caminho pronto.",
    # _montarResultado
    ("_montarResultado", "def _montarResultado("):
        "Define a montagem do resultado final, igual nos dois algoritmos.",
    ("_montarResultado",
     "distanciaAteOVertice: DistanciasPorVertice, predecessorDoVertice: PredecessoresPorVertice,"):
        "Parâmetros: dist[] e pred[] finais da busca.",
    ("_montarResultado", "origem: str, destino: str, nosExpandidos: int,"):
        "Parâmetros: origem, destino e o contador de nós expandidos (cada algoritmo tem a "
        "sua definição).",
    ("_montarResultado", ") -> ResultadoRota:"):
        "Devolve o `ResultadoRota`.",
    ("_montarResultado", "if distanciaAteOVertice[destino] == DISTANCIA_INFINITA:"):
        "dist[destino] ainda infinita: a busca terminou sem chegar ao destino.",
    ("_montarResultado", "return ResultadoRota.inalcancavel(nosExpandidos)"):
        "Estado próprio 'inalcancavel': pedido válido, sem caminho. Guarda quantos nós foram "
        "expandidos até desistir.",
    ("_montarResultado", "caminho = _reconstruirCaminho(predecessorDoVertice, origem, destino)"):
        "Destino alcançado: reconstrói o caminho por pred[].",
    ("_montarResultado", "return ResultadoRota.aPartirDoCaminho(caminho, nosExpandidos)"):
        "Resultado 'encontrada'. Os totais (m, s, R$) são somados com `math.fsum` a partir "
        "das arestas do caminho, e o `ResultadoRota` ainda confere que o caminho é contínuo.",
    # calcularRotaDijkstra
    ("calcularRotaDijkstra", "def calcularRotaDijkstra("):
        "Função pública do Dijkstra (sem `_`): é a que app.py e os testes chamam.",
    ("calcularRotaDijkstra", "grafo: Grafo, origem: str, destino: str, criterio: str"):
        "Parâmetros: o grafo dirigido, os ids da origem e do destino e o critério "
        "('distancia', 'tempo' ou 'custo').",
    ("calcularRotaDijkstra", ") -> ResultadoRota:"):
        "Devolve um `ResultadoRota`.",
    ("calcularRotaDijkstra",
     "resultadoAntecipado = _verificarSolicitacao(grafo, origem, destino, criterio)"):
        "Passo 1: confere critério, existência dos vértices e origem = destino.",
    ("calcularRotaDijkstra", "if resultadoAntecipado is not None:"):
        "Se já existe uma resposta...",
    ("calcularRotaDijkstra", "return resultadoAntecipado"):
        "...devolve sem rodar a busca.",
    ("calcularRotaDijkstra",
     "distanciaAteOVertice, predecessorDoVertice = _inicializarEstimativas(grafo, origem)"):
        "Passo 2: cria dist[] e pred[] e desempacota a tupla em duas variáveis.",
    ("calcularRotaDijkstra", "verticesMaduros: Set[str] = set()"):
        "Passo 3: conjunto S dos slides (vértices maduros), começa vazio. Um `set` responde "
        "\"está em S?\" em tempo constante.",
    ("calcularRotaDijkstra", "filaDePrioridade: List[Tuple[float, int, str]] = [(0.0, 0, origem)]"):
        "O heap é uma lista comum de tuplas (distância, desempate, id). Começa só com a "
        "origem: distância 0 e desempate 0. Uma lista de um elemento já é um heap válido.",
    ("calcularRotaDijkstra", "proximoDesempate: int = 1"):
        "Próximo número de desempate. Ele cresce a cada inserção: o Python compara tuplas "
        "elemento a elemento, então com distâncias iguais sai primeiro quem entrou antes, e "
        "os ids nunca chegam a ser comparados.",
    ("calcularRotaDijkstra", "while filaDePrioridade:"):
        "Laço principal: repete enquanto houver candidato. Lista vazia é falsa em Python; "
        "fila vazia = nada mais é alcançável.",
    ("calcularRotaDijkstra",
     "distanciaDaEntrada, _desempateDaEntrada, verticeAtual = heapq.heappop(filaDePrioridade)"):
        "`heappop` remove e devolve a menor tupla em O(log n): o imaturo v de menor dist. O "
        "`_` no nome do desempate indica que ele não é usado depois.",
    ("calcularRotaDijkstra", "if (verticeAtual in verticesMaduros"):
        "Remoção preguiçosa: a entrada é velha se v já está maduro...",
    ("calcularRotaDijkstra", "or distanciaDaEntrada > distanciaAteOVertice[verticeAtual]):"):
        "...ou se a distância gravada nela é maior que dist[v] atual (houve melhora depois "
        "que ela entrou). O `heapq` não sabe diminuir a chave de uma entrada, então a velha "
        "fica na fila e é ignorada aqui.",
    ("calcularRotaDijkstra", "continue"):
        "Descarta a entrada velha e volta ao início do `while`.",
    ("calcularRotaDijkstra", "verticesMaduros.add(verticeAtual)"):
        "Declara v maduro: dist[v] é definitiva. É isso que nosExpandidos conta.",
    ("calcularRotaDijkstra", "if verticeAtual == destino:"):
        "Se quem amadureceu é o destino...",
    ("calcularRotaDijkstra", "break"):
        "...sai do `while`: o caminho mínimo até ele já está em pred[].",
    ("calcularRotaDijkstra", "for arestaDeSaida in grafo.getAdjacencias(verticeAtual):"):
        "Percorre as arestas que SAEM de v. A mão única é respeitada porque só existe aresta "
        "no sentido permitido.",
    ("calcularRotaDijkstra",
     "if _relaxarSeTensa(arestaDeSaida, criterio, distanciaAteOVertice, predecessorDoVertice):"):
        "Relaxa a aresta (v, w) se ela estiver tensa; dist[] e pred[] são alterados lá dentro.",
    ("calcularRotaDijkstra", "verticeVizinho = arestaDeSaida.destino.id"):
        "Relaxou: pega o id de w...",
    ("calcularRotaDijkstra",
     "entrada = (distanciaAteOVertice[verticeVizinho], proximoDesempate, verticeVizinho)"):
        "...monta a entrada (nova dist[w], desempate, id de w)...",
    ("calcularRotaDijkstra", "heapq.heappush(filaDePrioridade, entrada)"):
        "...e insere no heap em O(log n). Uma entrada antiga de w pode continuar na fila; "
        "ela será descartada quando sair.",
    ("calcularRotaDijkstra", "proximoDesempate += 1"):
        "Avança o desempate para a próxima inserção.",
    ("calcularRotaDijkstra", "return _montarResultado("):
        "Passo 4: transforma dist[] e pred[] no `ResultadoRota`...",
    ("calcularRotaDijkstra",
     "distanciaAteOVertice, predecessorDoVertice, origem, destino, len(verticesMaduros)"):
        "...com nosExpandidos = quantidade de vértices maduros (`len` do conjunto S).",
    ("calcularRotaDijkstra", ")"):
        "Fecha os parênteses da chamada aberta nas linhas anteriores.",
    # calcularRotaBellmanFord
    ("calcularRotaBellmanFord", "def calcularRotaBellmanFord("):
        "Função pública do Bellman-Ford, com a mesma assinatura do Dijkstra.",
    ("calcularRotaBellmanFord", "grafo: Grafo, origem: str, destino: str, criterio: str"):
        "Mesmos parâmetros do Dijkstra.",
    ("calcularRotaBellmanFord", ") -> ResultadoRota:"):
        "Devolve um `ResultadoRota`.",
    ("calcularRotaBellmanFord",
     "resultadoAntecipado = _verificarSolicitacao(grafo, origem, destino, criterio)"):
        "Passo 1: a mesma validação do Dijkstra.",
    ("calcularRotaBellmanFord", "if resultadoAntecipado is not None:"):
        "Se já existe uma resposta...",
    ("calcularRotaBellmanFord", "return resultadoAntecipado"):
        "...devolve sem rodar a busca.",
    ("calcularRotaBellmanFord",
     "distanciaAteOVertice, predecessorDoVertice = _inicializarEstimativas(grafo, origem)"):
        "Passo 2: a mesma inicialização do Dijkstra.",
    ("calcularRotaBellmanFord", "nosExpandidos: int = 0"):
        "Passo 3: soma dos vértices examinados em todas as iterações.",
    ("calcularRotaBellmanFord", "houveRelaxacao: bool = False"):
        "Se a iteração mais recente relaxou alguma aresta; cada iteração sobrescreve.",
    ("calcularRotaBellmanFord", "for _numeroDaIteracao in range(len(grafo.vertices) - 1):"):
        "Repete no máximo \\|V\\| - 1 vezes, o limite dos slides. O número da iteração não é "
        "usado (por isso o `_`).",
    ("calcularRotaBellmanFord",
     "verticesExaminados, houveRelaxacao = _executarIteracaoDeBellmanFord("):
        "Executa uma iteração completa e desempacota (vértices examinados, se relaxou algo)...",
    ("calcularRotaBellmanFord", "grafo, criterio, distanciaAteOVertice, predecessorDoVertice"):
        "Argumentos da iteração: grafo, critério, dist[] e pred[].",
    ("calcularRotaBellmanFord", ")"):
        "Fecha os parênteses da chamada aberta nas linhas anteriores.",
    ("calcularRotaBellmanFord", "nosExpandidos += verticesExaminados"):
        "Acumula os vértices examinados nesta iteração.",
    ("calcularRotaBellmanFord", "if not houveRelaxacao:"):
        "Se a iteração não relaxou nenhuma aresta...",
    ("calcularRotaBellmanFord", "break"):
        "...término antecipado: sai do `for`.",
    ("calcularRotaBellmanFord", "if houveRelaxacao:"):
        "Passo 4: só é `True` se rodaram as \\|V\\| - 1 iterações e a última ainda relaxou; só "
        "nesse caso pode haver ciclo negativo.",
    ("calcularRotaBellmanFord",
     "_verticesDaPassadaExtra, aindaHaArestaTensa = _executarIteracaoDeBellmanFord("):
        "Passada extra: mais uma iteração. Se ela ainda relaxar, alguma aresta continua tensa "
        "depois de \\|V\\| - 1 iterações. Os vértices dela não entram em nosExpandidos (`_`).",
    ("calcularRotaBellmanFord", "if aindaHaArestaTensa:"):
        "Ainda havia aresta tensa...",
    ("calcularRotaBellmanFord", "return ResultadoRota.invalida()"):
        "...ciclo de custo negativo alcançável: não existe caminho mínimo, o pedido é "
        "'invalida'.",
    ("calcularRotaBellmanFord", "return _montarResultado("):
        "Passo 5: igual ao Dijkstra...",
    ("calcularRotaBellmanFord",
     "distanciaAteOVertice, predecessorDoVertice, origem, destino, nosExpandidos"):
        "...com o nosExpandidos somado nas iterações.",
    # _executarIteracaoDeBellmanFord
    ("_executarIteracaoDeBellmanFord", "def _executarIteracaoDeBellmanFord("):
        "Define uma iteração do Bellman-Ford, usada no laço e na passada extra.",
    ("_executarIteracaoDeBellmanFord", "grafo: Grafo, criterio: str,"):
        "Parâmetros: o grafo e o critério.",
    ("_executarIteracaoDeBellmanFord",
     "distanciaAteOVertice: DistanciasPorVertice, predecessorDoVertice: PredecessoresPorVertice,"):
        "Parâmetros: dist[] e pred[], alterados pela relaxação.",
    ("_executarIteracaoDeBellmanFord", ") -> Tuple[int, bool]:"):
        "Devolve a tupla (vértices examinados, se alguma aresta foi relaxada).",
    ("_executarIteracaoDeBellmanFord", "verticesExaminados: int = 0"):
        "Contador de vértices examinados nesta iteração.",
    ("_executarIteracaoDeBellmanFord", "houveRelaxacao: bool = False"):
        "Vira `True` se alguma aresta for relaxada.",
    ("_executarIteracaoDeBellmanFord", "for verticeAtual in grafo.vertices:"):
        "Percorre os ids de todos os vértices na ordem de inserção (percorrer um dicionário "
        "dá as chaves).",
    ("_executarIteracaoDeBellmanFord",
     "if distanciaAteOVertice[verticeAtual] == DISTANCIA_INFINITA:"):
        "Vértice ainda não alcançado: infinito + peso continua infinito e não deixa nenhuma "
        "aresta tensa...",
    ("_executarIteracaoDeBellmanFord", "continue"):
        "...então é pulado e não conta como expandido.",
    ("_executarIteracaoDeBellmanFord", "verticesExaminados += 1"):
        "Conta este vértice como expandido nesta iteração.",
    ("_executarIteracaoDeBellmanFord", "for arestaDeSaida in grafo.getAdjacencias(verticeAtual):"):
        "Percorre as arestas de saída de v.",
    ("_executarIteracaoDeBellmanFord",
     "if _relaxarSeTensa(arestaDeSaida, criterio, distanciaAteOVertice, predecessorDoVertice):"):
        "Relaxa a aresta se ela estiver tensa (a mesma função do Dijkstra)...",
    ("_executarIteracaoDeBellmanFord", "houveRelaxacao = True"):
        "...e registra que a iteração mudou dist[].",
    ("_executarIteracaoDeBellmanFord", "return verticesExaminados, houveRelaxacao"):
        "Devolve os dois resultados da iteração.",
}

# Critérios de aceite da Issue 07 (artefatos/planejamento/issues_github.md). Cada trecho é
# (rótulo, função, código da primeira linha, código da última linha ou None = só uma linha);
# o código da primeira linha None significa a função inteira. Os testes são conferidos
# nos arquivos test_*.py de codigo/.
CRITERIOS_DA_ISSUE_07: List[Tuple[str, List[Tuple[str, str, Optional[str], Optional[str]]],
                                  List[str]]] = [
    ("Busca retorna caminho mínimo para cada critério com pesos não negativos.", [
        ("laço do Dijkstra", "calcularRotaDijkstra", "while filaDePrioridade:",
         "proximoDesempate += 1"),
        ("iterações do Bellman-Ford", "calcularRotaBellmanFord",
         "for _numeroDaIteracao in range(len(grafo.vertices) - 1):", "break"),
        ("relaxação com o peso do critério (`getPeso`)", "_relaxarSeTensa",
         "novaDistancia = distanciaAteOVertice[arestaDeSaida.origem.id] + "
         "arestaDeSaida.getPeso(criterio)", "return False"),
    ], ["test_cada_criterio_escolhe_sua_rota", "test_grafo_dos_slides",
        "test_validacao_cruzada_mapa_real"]),
    ("Caminho respeita direção e arestas reais; custos consolidados conferem.", [
        ("só arestas que saem de v (Dijkstra)", "calcularRotaDijkstra",
         "for arestaDeSaida in grafo.getAdjacencias(verticeAtual):", None),
        ("só arestas que saem de v (Bellman-Ford)", "_executarIteracaoDeBellmanFord",
         "for arestaDeSaida in grafo.getAdjacencias(verticeAtual):", None),
        ("pred[] guarda a própria aresta", "_relaxarSeTensa",
         "predecessorDoVertice[verticeVizinho] = arestaDeSaida", None),
        ("reconstrução por pred[]", "_reconstruirCaminho", None, None),
        ("totais somados das arestas do caminho", "_montarResultado",
         "return ResultadoRota.aPartirDoCaminho(caminho, nosExpandidos)", None),
    ], ["test_mao_unica_nao_pode_ser_percorrida_ao_contrario",
        "test_aresta_paralela_mais_barata_e_escolhida"]),
    ("Origem=destino retorna custo zero; destino inalcançável tem estado próprio.", [
        ("origem = destino", "_verificarSolicitacao", "if origem == destino:",
         "return ResultadoRota.aPartirDoCaminho([], nosExpandidos=0)"),
        ("inalcançável", "_montarResultado",
         "if distanciaAteOVertice[destino] == DISTANCIA_INFINITA:",
         "return ResultadoRota.inalcancavel(nosExpandidos)"),
    ], ["test_origem_igual_ao_destino_tem_custo_zero",
        "test_destino_inalcancavel_tem_estado_proprio"]),
    ("Solicitação/critério inválido é diferenciado de falta de caminho.", [
        ("critério inválido", "_verificarSolicitacao", "try:",
         "return ResultadoRota.invalida()"),
        ("vértice inexistente", "_verificarSolicitacao",
         "if not grafo.existeVertice(origem) or not grafo.existeVertice(destino):",
         "return ResultadoRota.invalida()"),
        ("ciclo negativo (Bellman-Ford)", "calcularRotaBellmanFord", "if aindaHaArestaTensa:",
         "return ResultadoRota.invalida()"),
    ], ["test_vertice_inexistente_e_pedido_invalido", "test_criterio_invalido_e_pedido_invalido",
        "test_bellman_ford_detecta_ciclo_negativo_alcancavel"]),
    ("Resultado tem os campos acordados, incluindo nós processados.", [
        ("nosExpandidos do Dijkstra (vértices maduros)", "calcularRotaDijkstra",
         "distanciaAteOVertice, predecessorDoVertice, origem, destino, len(verticesMaduros)",
         None),
        ("nosExpandidos do Bellman-Ford (soma por iteração)", "calcularRotaBellmanFord",
         "nosExpandidos += verticesExaminados", None),
        ("vértices examinados numa iteração", "_executarIteracaoDeBellmanFord",
         "verticesExaminados += 1", None),
        ("construtores do `ResultadoRota`", "_montarResultado",
         "return ResultadoRota.inalcancavel(nosExpandidos)",
         "return ResultadoRota.aPartirDoCaminho(caminho, nosExpandidos)"),
    ], ["test_dijkstra_conta_vertices_maduros_e_para_no_destino",
        "test_bellman_ford_soma_vertices_examinados_por_iteracao"]),
    ("Nenhuma biblioteca externa é usada para executar a busca.", [
        ("imports (só `heapq`, `typing` e `grafo`)", MODULO, "import heapq",
         "from grafo import Aresta, Grafo, ResultadoRota, normalizarCriterio"),
    ], ["test_rotas_usa_somente_biblioteca_padrao_e_grafo"]),
]


class ArquivoAnalisado:
    """As linhas de rotas.py classificadas: docstring, comentário, branco ou código."""

    def __init__(self, fonte: str) -> None:
        self.linhas = [linha.strip() for linha in fonte.splitlines()]
        self.docstrings: Dict[int, Tuple[int, str]] = {}  # linha inicial -> (final, nome)
        self.intervalosDasFuncoes: Dict[str, Tuple[int, int]] = {}
        arvore = ast.parse(fonte)
        for no in ast.walk(arvore):  # inclui o próprio módulo
            if isinstance(no, (ast.FunctionDef, ast.ClassDef)):
                self.intervalosDasFuncoes[no.name] = (no.lineno, no.end_lineno)
            if not isinstance(no, (ast.Module, ast.FunctionDef, ast.ClassDef)) or not no.body:
                continue
            primeiro = no.body[0]
            if (isinstance(primeiro, ast.Expr) and isinstance(primeiro.value, ast.Constant)
                    and isinstance(primeiro.value.value, str)):
                nome = MODULO if isinstance(no, ast.Module) else no.name
                self.docstrings[primeiro.lineno] = (primeiro.end_lineno, nome)

    def funcaoDaLinha(self, numero: int) -> str:
        """A função mais interna que contém a linha (MODULO se nenhuma)."""
        candidatas = [(fim - inicio, nome) for nome, (inicio, fim)
                      in self.intervalosDasFuncoes.items() if inicio <= numero <= fim]
        return min(candidatas)[1] if candidatas else MODULO

    def acharLinha(self, funcao: str, codigo: str) -> Optional[int]:
        for numero, texto in enumerate(self.linhas, start=1):
            if texto == codigo and self.funcaoDaLinha(numero) == funcao:
                return numero
        return None


def escaparCelula(texto: str) -> str:
    if "`" in texto:
        raise ValueError(f"crase no código não cabe na tabela: {texto}")
    return texto.replace("|", "\\|")


def primeiraFraseDaDocstring(arquivo: ArquivoAnalisado, inicio: int, fim: int) -> str:
    for texto in arquivo.linhas[inicio - 1:fim]:
        frase = texto.strip('"').strip()
        if frase:
            return frase
    return ""


def gerarTabelaLinhaALinha(arquivo: ArquivoAnalisado) -> Tuple[List[str], List[str]]:
    """Devolve (linhas da tabela em Markdown, problemas encontrados)."""
    tabela = ["| linha | código | o que faz |", "| --- | --- | --- |"]
    problemas: List[str] = []
    usadas: Set[Tuple[str, str]] = set()
    total = len(arquivo.linhas)
    numero = 1
    while numero <= total:
        texto = arquivo.linhas[numero - 1]
        if not texto:
            numero += 1
            continue
        if numero in arquivo.docstrings:
            fim, nome = arquivo.docstrings[numero]
            dono = "do módulo" if nome == MODULO else f"de `{nome}`"
            frase = primeiraFraseDaDocstring(arquivo, numero, fim)
            tabela.append(f"| {formatarIntervalo(numero, fim)} | `{escaparCelula(texto)}` | "
                          f"Docstring {dono} (documentação, não executa): "
                          f"\"{escaparCelula(frase)}\" |")
            numero = fim + 1
            continue
        if texto.startswith("#"):
            fim = numero
            while fim < total and arquivo.linhas[fim].startswith("#"):
                fim += 1
            bloco = arquivo.linhas[numero - 1:fim]
            titulos = [linha for linha in bloco if not linha.startswith("# ---")]
            if len(titulos) < len(bloco):
                tabela.append(f"| {formatarIntervalo(numero, fim)} | `{escaparCelula(titulos[0])}` "
                              f"| Título de seção (comentário, não executa). |")
            else:
                proxima = proximaLinhaDeCodigo(arquivo, fim)
                definicao = re.match(r"def (\w+)\(", arquivo.linhas[proxima - 1])
                descricao = (f"Frase que resume a função `{definicao.group(1)}`" if definicao
                             else f"Comentário sobre a linha {proxima}")
                tabela.append(f"| {formatarIntervalo(numero, fim)} | `{escaparCelula(texto)}` | "
                              f"{descricao} (não executa). |")
            numero = fim + 1
            continue
        chave = (arquivo.funcaoDaLinha(numero), texto)
        explicacao = EXPLICACOES.get(chave)
        if explicacao is None:
            problemas.append(f"linha {numero} sem explicação: chave {chave!r}")
            explicacao = "?"
        usadas.add(chave)
        tabela.append(f"| {numero} | `{escaparCelula(texto)}` | {explicacao} |")
        numero += 1
    for chave in EXPLICACOES:
        if chave not in usadas:
            problemas.append(f"explicação sem linha correspondente: chave {chave!r}")
    return tabela, problemas


def formatarIntervalo(inicio: int, fim: int) -> str:
    return str(inicio) if inicio == fim else f"{inicio}–{fim}"


def proximaLinhaDeCodigo(arquivo: ArquivoAnalisado, depoisDe: int) -> int:
    for numero in range(depoisDe + 1, len(arquivo.linhas) + 1):
        if arquivo.linhas[numero - 1]:
            return numero
    return depoisDe


def atualizarTabelaDeFuncoes(arquivo: ArquivoAnalisado, trecho: str) -> Tuple[str, List[str]]:
    """Troca a coluna "linhas" da seção 1.3 pelo intervalo real de cada função."""
    problemas: List[str] = []
    citadas: Set[str] = set()
    novasLinhas = []
    for linha in trecho.split("\n"):
        encontrada = LINHA_DA_TABELA_DE_FUNCOES.match(linha)
        if encontrada:
            nome = encontrada.group(2)
            citadas.add(nome)
            if nome not in arquivo.intervalosDasFuncoes:
                problemas.append(f"seção 1.3 cita `{nome}`, que não existe em rotas.py")
            else:
                inicio, fim = arquivo.intervalosDasFuncoes[nome]
                linha = f"{encontrada.group(1)}{inicio}–{fim}{encontrada.group(3)}"
        novasLinhas.append(linha)
    for nome in arquivo.intervalosDasFuncoes:
        if nome not in citadas:
            problemas.append(f"seção 1.3 não tem linha para a função `{nome}`")
    return "\n".join(novasLinhas), problemas


def gerarTabelaDeCriterios(arquivo: ArquivoAnalisado) -> Tuple[List[str], List[str]]:
    problemas: List[str] = []
    textoDosTestes = ""
    for caminho in glob.glob(os.path.join(PASTA_CODIGO, "**", "test_*.py"), recursive=True):
        with open(caminho, encoding="utf-8") as arquivoDeTeste:
            textoDosTestes += arquivoDeTeste.read()
    tabela = ["| critério de aceite | onde está em `codigo/rotas.py` | testes que conferem |",
              "| --- | --- | --- |"]
    for criterio, trechos, testes in CRITERIOS_DA_ISSUE_07:
        partes = []
        for rotulo, funcao, codigoInicial, codigoFinal in trechos:
            if codigoInicial is None:
                inicio, fim = arquivo.intervalosDasFuncoes.get(funcao, (None, None))
            else:
                inicio = arquivo.acharLinha(funcao, codigoInicial)
                fim = inicio if codigoFinal is None else acharDepois(arquivo, funcao,
                                                                      codigoFinal, inicio)
            if inicio is None or fim is None:
                problemas.append(f"critério {criterio!r}: trecho {rotulo!r} não encontrado")
                continue
            palavra = "linha" if inicio == fim else "linhas"
            partes.append(f"{rotulo}: {palavra} {formatarIntervalo(inicio, fim)}")
        for teste in testes:
            if f"def {teste}(" not in textoDosTestes:
                problemas.append(f"critério {criterio!r}: teste {teste} não encontrado")
        celulaDeTestes = ", ".join(f"`{teste}`" for teste in testes)
        tabela.append(f"| {criterio} | {'; '.join(partes)} | {celulaDeTestes} |")
    return tabela, problemas


def acharDepois(arquivo: ArquivoAnalisado, funcao: str, codigo: str,
                inicio: Optional[int]) -> Optional[int]:
    """Primeira linha igual a `codigo`, na mesma função, a partir de `inicio`."""
    if inicio is None:
        return None
    for numero in range(inicio, len(arquivo.linhas) + 1):
        if arquivo.linhas[numero - 1] == codigo and arquivo.funcaoDaLinha(numero) == funcao:
            return numero
    return None


def substituirEntreMarcadores(texto: str, marcadores: Tuple[str, str], miolo: str) -> str:
    inicio, fim = marcadores
    if texto.count(inicio) != 1 or texto.count(fim) != 1:
        raise SystemExit(f"o roteiro precisa ter exatamente um {inicio} e um {fim}")
    antes, resto = texto.split(inicio)
    _antigo, depois = resto.split(fim)
    return f"{antes}{inicio}\n{miolo}\n{fim}{depois}"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    with open(CAMINHO_ROTAS, encoding="utf-8") as arquivoFonte:
        arquivo = ArquivoAnalisado(arquivoFonte.read())
    with open(CAMINHO_ROTEIRO, encoding="utf-8") as arquivoRoteiro:
        roteiro = arquivoRoteiro.read()
    tabela, problemas = gerarTabelaLinhaALinha(arquivo)
    criterios, problemasDosCriterios = gerarTabelaDeCriterios(arquivo)
    trechoDeFuncoes = roteiro.split(MARCADORES_DE_FUNCOES[0])[1].split(MARCADORES_DE_FUNCOES[1])[0]
    novoTrechoDeFuncoes, problemasDasFuncoes = atualizarTabelaDeFuncoes(arquivo, trechoDeFuncoes)
    problemas += problemasDosCriterios + problemasDasFuncoes
    if problemas:
        print("Roteiro NÃO alterado. Corrija EXPLICACOES / CRITERIOS_DA_ISSUE_07 / seção 1.3:")
        for problema in problemas:
            print("  -", problema)
        sys.exit(1)
    roteiro = substituirEntreMarcadores(roteiro, MARCADORES_DA_TABELA, "\n".join(tabela))
    roteiro = substituirEntreMarcadores(roteiro, MARCADORES_DE_CRITERIOS, "\n".join(criterios))
    roteiro = roteiro.replace(trechoDeFuncoes, novoTrechoDeFuncoes)
    with open(CAMINHO_ROTEIRO, "w", encoding="utf-8", newline="\n") as arquivoRoteiro:
        arquivoRoteiro.write(roteiro)
    print(f"OK: seção 2 com {len(tabela) - 2} linhas, seção 1.3 e seção 1.4 atualizadas "
          f"em {CAMINHO_ROTEIRO}")


if __name__ == "__main__":
    main()
