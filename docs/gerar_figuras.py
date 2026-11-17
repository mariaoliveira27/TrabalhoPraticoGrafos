"""
Gera as figuras passo a passo de docs/roteiro_rotas.md (só para a documentação).

Reproduz, no grafo dos slides (raiz c), cada passo do Dijkstra e cada iteração
do Bellman-Ford com as mesmas regras de codigo/rotas.py (relaxação só com
"estritamente menor", fila com contador de desempate, vértices na ordem de
inserção), desenha um PNG por passo em docs/figuras/ e imprime os estados.

No fim confere o estado final contra calcularRotaDijkstra e
calcularRotaBellmanFord reais: se a reprodução divergir do código, o script
para com erro e as figuras não devem ser usadas.

Uso (na raiz do repositório):
    python docs/gerar_figuras.py
Requer matplotlib (não é dependência do sistema, só da documentação).
"""

import heapq
import math
import os
import sys
from typing import Dict, List, Optional, Set, Tuple

import matplotlib

matplotlib.use("Agg")  # gera arquivos sem abrir janela
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Patch  # noqa: E402

PASTA_DOCS = os.path.dirname(os.path.abspath(__file__))
PASTA_FIGURAS = os.path.join(PASTA_DOCS, "figuras")
sys.path.insert(0, os.path.join(os.path.dirname(PASTA_DOCS), "codigo"))

from grafo import Aresta, Grafo, Vertice  # noqa: E402
from rotas import calcularRotaBellmanFord, calcularRotaDijkstra  # noqa: E402

# Grafo dos slides "Caminho Mínimo (1)": (origem, destino, peso), raiz c.
ARESTAS_DO_EXEMPLO: List[Tuple[str, str, float]] = [
    ("c", "a", 5.0), ("c", "e", 1.0), ("a", "b", 6.0), ("e", "b", 1.0),
    ("e", "f", 8.0), ("b", "d", 1.0), ("d", "f", 1.0), ("f", "a", 2.0),
]
RAIZ = "c"
DESTINO_DO_DIJKSTRA = "a"  # o último a amadurecer: o passo a passo mostra a árvore inteira
DISTANCIA_INFINITA = float("inf")

# Posições dos vértices (x, y): ciclo externo c-a-f-e com b e d por dentro,
# um desenho sem nenhum cruzamento de arestas.
POSICOES: Dict[str, Tuple[float, float]] = {
    "c": (0.0, 1.0), "a": (2.4, 2.2), "e": (2.4, -0.2),
    "b": (2.4, 1.0), "d": (3.6, 1.0), "f": (4.8, 1.0),
}
# Onde fica o rótulo "dist = ..." de cada vértice: (deslocamento x, deslocamento y,
# alinhamento horizontal, alinhamento vertical), escolhido para não tocar arestas.
ROTULO_DA_DISTANCIA: Dict[str, Tuple[float, float, str, str]] = {
    "c": (0.0, 0.3, "center", "bottom"), "a": (0.0, 0.3, "center", "bottom"),
    "e": (0.0, -0.3, "center", "top"), "b": (-0.3, 0.0, "right", "center"),
    "d": (0.0, -0.3, "center", "top"), "f": (0.3, 0.0, "left", "center"),
}

# Cores: azul e laranja são os dois primeiros slots da paleta de referência
# (seguros para daltonismo); o corte também é tracejado, não só colorido.
COR_MADURO = "#2a78d6"
COR_CORTE = "#eb6834"
COR_ARESTA_COMUM = "#b0aea5"
COR_TEXTO = "#0b0b0b"
COR_TEXTO_SECUNDARIO = "#52514e"
COR_FUNDO = "#fcfcfb"
COR_ALCANCADO = "#d6e6f8"

ArestaDoExemplo = Tuple[str, str]


class Estado:
    """Fotografia de um passo: o que a figura e a tabela mostram."""

    def __init__(self, titulo: str, dist: Dict[str, float], pred: Dict[str, Optional[str]],
                 destaqueDeVertices: Set[str], arestasDestacadas: List[ArestaDoExemplo],
                 rodape: str) -> None:
        self.titulo = titulo
        self.dist = dict(dist)
        self.pred = dict(pred)
        self.destaqueDeVertices = set(destaqueDeVertices)
        self.arestasDestacadas = list(arestasDestacadas)
        self.rodape = rodape


def listarVerticesNaOrdemDeInsercao() -> List[str]:
    """Mesma ordem que Grafo.adicionarAresta produz: origem, depois destino."""
    ordem: List[str] = []
    for origem, destino, _peso in ARESTAS_DO_EXEMPLO:
        for vertice in (origem, destino):
            if vertice not in ordem:
                ordem.append(vertice)
    return ordem


def arestasQueSaemDe(vertice: str) -> List[Tuple[str, str, float]]:
    return [aresta for aresta in ARESTAS_DO_EXEMPLO if aresta[0] == vertice]


def formatarDistancia(valor: float) -> str:
    return "∞" if math.isinf(valor) else f"{valor:g}"


def formatarPred(pred: Dict[str, Optional[str]], vertice: str) -> str:
    return "-" if pred[vertice] is None else f"{pred[vertice]}→{vertice}"


def calcularCorte(maduros: Set[str]) -> List[ArestaDoExemplo]:
    """corte(S) = arestas (v, w) com v em S e w fora de S."""
    return [(origem, destino) for origem, destino, _peso in ARESTAS_DO_EXEMPLO
            if origem in maduros and destino not in maduros]


def tracarDijkstra() -> List[Estado]:
    """Reproduz o laço de rotas.calcularRotaDijkstra, guardando cada passo."""
    vertices = listarVerticesNaOrdemDeInsercao()
    dist = {vertice: DISTANCIA_INFINITA for vertice in vertices}
    pred: Dict[str, Optional[str]] = {vertice: None for vertice in vertices}
    dist[RAIZ] = 0.0
    maduros: Set[str] = set()
    fila: List[Tuple[float, int, str]] = [(0.0, 0, RAIZ)]
    contador = 1
    estados = [Estado("Dijkstra, passo 0: inicialização", dist, pred, set(), [],
                      "fila: " + descreverFila(fila))]
    while fila:
        distanciaDaEntrada, _desempate, vertice = heapq.heappop(fila)
        if vertice in maduros or distanciaDaEntrada > dist[vertice]:
            continue  # remoção preguiçosa
        maduros.add(vertice)
        relaxadas = []
        if vertice != DESTINO_DO_DIJKSTRA:
            for origem, destino, peso in arestasQueSaemDe(vertice):
                if dist[origem] + peso < dist[destino]:
                    dist[destino] = dist[origem] + peso
                    pred[destino] = origem
                    heapq.heappush(fila, (dist[destino], contador, destino))
                    contador += 1
                    relaxadas.append(f"{origem}→{destino}")
        numero = len(maduros)
        titulo = f"Dijkstra, passo {numero}: {vertice} declarado maduro (dist = {dist[vertice]:g})"
        rodape = ("relaxadas: " + (", ".join(relaxadas) or "nenhuma")
                  + "   |   fila: " + descreverFila(fila))
        estados.append(Estado(titulo, dist, pred, maduros, calcularCorte(maduros), rodape))
        if vertice == DESTINO_DO_DIJKSTRA:
            break
    return estados


def descreverFila(fila: List[Tuple[float, int, str]]) -> str:
    if not fila:
        return "vazia"
    return "  ".join(f"({distancia:g}, #{desempate}, {vertice})"
                     for distancia, desempate, vertice in sorted(fila))


def tracarBellmanFord() -> Tuple[List[Estado], List[str], int]:
    """Reproduz as iterações de rotas.calcularRotaBellmanFord (estados, registro, nosExpandidos)."""
    vertices = listarVerticesNaOrdemDeInsercao()
    dist = {vertice: DISTANCIA_INFINITA for vertice in vertices}
    pred: Dict[str, Optional[str]] = {vertice: None for vertice in vertices}
    dist[RAIZ] = 0.0
    estados = [Estado("Bellman-Ford, iteração 0: inicialização", dist, pred, {RAIZ}, [],
                      f"ordem dos vértices: {', '.join(vertices)}   |   |V| - 1 = {len(vertices) - 1}")]
    registro: List[str] = []
    nosExpandidos = 0
    for numeroDaIteracao in range(1, len(vertices)):
        relaxadas: List[ArestaDoExemplo] = []
        for vertice in vertices:
            if math.isinf(dist[vertice]):
                registro.append(f"it{numeroDaIteracao} {vertice}: dist infinita, pulado")
                continue
            nosExpandidos += 1
            for origem, destino, peso in arestasQueSaemDe(vertice):
                antes = dist[destino]
                if dist[origem] + peso < dist[destino]:
                    dist[destino] = dist[origem] + peso
                    pred[destino] = origem
                    relaxadas.append((origem, destino))
                    registro.append(f"it{numeroDaIteracao} {origem}→{destino}: "
                                    f"{formatarDistancia(antes)} -> {dist[destino]:g}")
        alcancados = {vertice for vertice in vertices if not math.isinf(dist[vertice])}
        parou = not relaxadas
        titulo = (f"Bellman-Ford, iteração {numeroDaIteracao}: "
                  + ("nada mudou, término antecipado" if parou
                     else f"{len(relaxadas)} relaxações"))
        rodape = (f"relaxadas: {', '.join(f'{o}→{d}' for o, d in relaxadas) or 'nenhuma'}"
                  f"   |   nosExpandidos acumulado: {nosExpandidos}")
        estados.append(Estado(titulo, dist, pred, alcancados, relaxadas, rodape))
        if parou:
            break
    return estados, registro, nosExpandidos


def desenharEstado(estado: Estado, caminhoDoArquivo: str, rotuloDestaqueVertice: str,
                   rotuloDestaqueAresta: str, rotuloCombinado: str) -> None:
    figura, eixo = plt.subplots(figsize=(8.6, 4.4), dpi=150)
    figura.patch.set_facecolor(COR_FUNDO)
    eixo.set_facecolor(COR_FUNDO)
    arestasDoPred = {(origem, destino) for destino, origem in estado.pred.items() if origem}
    for origem, destino, peso in ARESTAS_DO_EXEMPLO:
        desenharAresta(eixo, origem, destino, peso, (origem, destino) in arestasDoPred,
                       (origem, destino) in estado.arestasDestacadas)
    for vertice, (posicaoX, posicaoY) in POSICOES.items():
        destacado = vertice in estado.destaqueDeVertices
        alcancado = not math.isinf(estado.dist[vertice])
        preenchimento = COR_MADURO if destacado else (COR_ALCANCADO if alcancado else "white")
        eixo.scatter([posicaoX], [posicaoY], s=900, color=preenchimento, edgecolors=COR_MADURO,
                     linewidths=2, zorder=3)
        eixo.text(posicaoX, posicaoY, vertice, ha="center", va="center", fontsize=13,
                  fontweight="bold", color="white" if destacado else COR_TEXTO, zorder=4)
        deslocamentoX, deslocamentoY, alinhamentoH, alinhamentoV = ROTULO_DA_DISTANCIA[vertice]
        eixo.text(posicaoX + deslocamentoX, posicaoY + deslocamentoY,
                  f"dist = {formatarDistancia(estado.dist[vertice])}",
                  ha=alinhamentoH, va=alinhamentoV, fontsize=9, color=COR_TEXTO, zorder=4)
    eixo.set_title(estado.titulo, fontsize=11, color=COR_TEXTO, loc="left")
    figura.text(0.02, 0.03, estado.rodape, fontsize=8, color=COR_TEXTO_SECUNDARIO)
    legenda = [Patch(facecolor=COR_MADURO, edgecolor=COR_MADURO, label=rotuloDestaqueVertice)]
    if rotuloDestaqueVertice.startswith("maduro"):
        legenda.append(Patch(facecolor=COR_ALCANCADO, edgecolor=COR_MADURO,
                             label="imaturo, dist finita"))
    legenda += [
        Line2D([0], [0], color=COR_CORTE, lw=2, linestyle="--", label=rotuloDestaqueAresta),
        Line2D([0], [0], color=COR_MADURO, lw=3, label="pred[] (árvore)"),
        Line2D([0], [0], color=COR_MADURO, lw=3, linestyle="--",
               label=rotuloCombinado),
        Line2D([0], [0], color=COR_ARESTA_COMUM, lw=1.2, label="outras arestas"),
    ]
    eixo.legend(handles=legenda, loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=8,
                frameon=False)
    eixo.set_xlim(-0.5, 5.9)
    eixo.set_ylim(-0.75, 2.75)
    eixo.set_aspect("equal")
    eixo.axis("off")
    figura.subplots_adjust(left=0.02, right=0.70, top=0.9, bottom=0.1)
    figura.savefig(caminhoDoArquivo, facecolor=COR_FUNDO)
    plt.close(figura)


def desenharAresta(eixo, origem: str, destino: str, peso: float, estaNoPred: bool,
                   estaDestacada: bool) -> None:
    if estaNoPred:
        cor, espessura, estilo = COR_MADURO, 3.0, "-"
    elif estaDestacada:
        cor, espessura, estilo = COR_CORTE, 2.0, "--"
    else:
        cor, espessura, estilo = COR_ARESTA_COMUM, 1.2, "-"
    if estaNoPred and estaDestacada:
        estilo = "--"  # aresta do corte (ou relaxada) que também está em pred[]
    seta = FancyArrowPatch(POSICOES[origem], POSICOES[destino], arrowstyle="-|>",
                           mutation_scale=16, color=cor, lw=espessura, linestyle=estilo,
                           shrinkA=17, shrinkB=17, zorder=2)
    eixo.add_patch(seta)
    (origemX, origemY), (destinoX, destinoY) = POSICOES[origem], POSICOES[destino]
    meioX, meioY = (origemX + destinoX) / 2, (origemY + destinoY) / 2
    eixo.text(meioX, meioY, f"{peso:g}", ha="center", va="center", fontsize=9, color=COR_TEXTO,
              bbox={"boxstyle": "round,pad=0.15", "facecolor": COR_FUNDO, "edgecolor": "none"},
              zorder=3)


def conferirComRotas(estadoFinalDijkstra: Estado, estadoFinalBellmanFord: Estado,
                     nosExpandidosBellmanFord: int) -> None:
    """Para com erro se a reprodução divergir do rotas.py real."""
    grafo = Grafo()
    for origem, destino, peso in ARESTAS_DO_EXEMPLO:
        grafo.adicionarAresta(Aresta(origem + destino, Vertice(origem, 0.0, 0.0),
                                     Vertice(destino, 0.0, 0.0), peso, 30.0, peso, peso))
    for destino in POSICOES:
        for calcularRota, estado in ((calcularRotaDijkstra, estadoFinalDijkstra),
                                     (calcularRotaBellmanFord, estadoFinalBellmanFord)):
            resultado = calcularRota(grafo, RAIZ, destino, "distancia")
            assert resultado.distanciaTotalMetros == estado.dist[destino], (calcularRota, destino)
            predDoCaminho = {aresta.destino.id: aresta.origem.id for aresta in resultado.caminho}
            for vertice, anterior in predDoCaminho.items():
                assert estado.pred[vertice] == anterior, (calcularRota, destino, vertice)
    dijkstraAteODestino = calcularRotaDijkstra(grafo, RAIZ, DESTINO_DO_DIJKSTRA, "distancia")
    assert dijkstraAteODestino.nosExpandidos == len(estadoFinalDijkstra.destaqueDeVertices)
    bellmanFord = calcularRotaBellmanFord(grafo, RAIZ, DESTINO_DO_DIJKSTRA, "distancia")
    assert bellmanFord.nosExpandidos == nosExpandidosBellmanFord


def imprimirEstado(estado: Estado) -> None:
    ordem = sorted(POSICOES)
    print(estado.titulo)
    print("  dist:", "  ".join(f"{v}={formatarDistancia(estado.dist[v])}" for v in ordem))
    print("  pred:", "  ".join(f"{v}={formatarPred(estado.pred, v)}" for v in ordem))
    print("  destaque:", ", ".join(f"{o}→{d}" for o, d in estado.arestasDestacadas) or "-")
    print("  ", estado.rodape)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # o console do Windows não imprime "∞" em cp1252
    os.makedirs(PASTA_FIGURAS, exist_ok=True)
    estadosDijkstra = tracarDijkstra()
    for numero, estado in enumerate(estadosDijkstra):
        desenharEstado(estado, os.path.join(PASTA_FIGURAS, f"dijkstra_passo_{numero}.png"),
                       "maduro (S)", "corte(S)", "pred[] e corte(S)")
        imprimirEstado(estado)
    estadosBellmanFord, registro, nosExpandidosBellmanFord = tracarBellmanFord()
    for numero, estado in enumerate(estadosBellmanFord):
        desenharEstado(estado, os.path.join(PASTA_FIGURAS, f"bellman_ford_iteracao_{numero}.png"),
                       "dist finita", "relaxada nesta iteração", "pred[] e relaxada")
        imprimirEstado(estado)
    print("\n".join(registro))
    conferirComRotas(estadosDijkstra[-1], estadosBellmanFord[-1], nosExpandidosBellmanFord)
    print(f"\nOK: {len(estadosDijkstra) + len(estadosBellmanFord)} figuras em {PASTA_FIGURAS}; "
          "estado final confere com rotas.py")


if __name__ == "__main__":
    main()
