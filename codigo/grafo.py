"""
Módulo de definição das classes do Grafo para o sistema de otimização de rotas.
Contempla Vertice, Aresta, Grafo e ResultadoRota conforme diagrama UML v2.
"""

from typing import Dict, List, Optional


class Vertice:
    """
    Representa um vértice (cruzamento ou ponto georreferenciado) no grafo viário.
    """

    def __init__(
        self,
        id_vertice: str,
        latitude: float,
        longitude: float,
        nome: Optional[str] = None
    ) -> None:
        if not (-90.0 <= latitude <= 90.0):
            raise ValueError(f"Latitude inválida: {latitude}")
        if not (-180.0 <= longitude <= 180.0):
            raise ValueError(f"Longitude inválida: {longitude}")

        self._id = str(id_vertice)
        self._latitude = float(latitude)
        self._longitude = float(longitude)
        self._nome = nome

    @property
    def id(self) -> str:
        return self._id

    @property
    def latitude(self) -> float:
        return self._latitude

    @property
    def longitude(self) -> float:
        return self._longitude

    @property
    def nome(self) -> Optional[str]:
        return self._nome

    def getId(self) -> str:
        return self._id

    def getNome(self) -> Optional[str]:
        return self._nome

    def getLatitude(self) -> float:
        return self._latitude

    def getLongitude(self) -> float:
        return self._longitude

    def __repr__(self) -> str:
        return f"Vertice(id='{self._id}', lat={self._latitude:.6f}, lon={self._longitude:.6f}, nome='{self._nome}')"


class Aresta:
    """
    Representa uma aresta dirigida (segmento de via) com pesos por múltiplos critérios.
    """

    def __init__(
        self,
        id_aresta: str,
        origem: Vertice,
        destino: Vertice,
        distanciaMetros: float,
        velocidadeKmH: float,
        tempoSegundos: float,
        custoReais: float
    ) -> None:
        if distanciaMetros < 0:
            raise ValueError("distanciaMetros não pode ser negativa")
        if velocidadeKmH <= 0:
            raise ValueError("velocidadeKmH deve ser estritamente positiva")
        if tempoSegundos < 0:
            raise ValueError("tempoSegundos não pode ser negativo")
        if custoReais < 0:
            raise ValueError("custoReais não pode ser negativo")

        self._id = str(id_aresta)
        self._origem = origem
        self._destino = destino
        self._distanciaMetros = float(distanciaMetros)
        self._velocidadeKmH = float(velocidadeKmH)
        self._tempoSegundos = float(tempoSegundos)
        self._custoReais = float(custoReais)

    @property
    def id(self) -> str:
        return self._id

    @property
    def origem(self) -> Vertice:
        return self._origem

    @property
    def destino(self) -> Vertice:
        return self._destino

    @property
    def distanciaMetros(self) -> float:
        return self._distanciaMetros

    @property
    def velocidadeKmH(self) -> float:
        return self._velocidadeKmH

    @property
    def tempoSegundos(self) -> float:
        return self._tempoSegundos

    @property
    def custoReais(self) -> float:
        return self._custoReais

    def getPeso(self, criterio: str) -> float:
        """
        Retorna o peso associado ao critério de otimização informado:
        - 'distancia': distância em metros
        - 'tempo': tempo estimado em segundos
        - 'custo': custo estimado em Reais (combustível)
        """
        criterio_limpo = criterio.strip().lower()
        if criterio_limpo == "distancia":
            return self._distanciaMetros
        elif criterio_limpo == "tempo":
            return self._tempoSegundos
        elif criterio_limpo == "custo":
            return self._custoReais
        else:
            raise ValueError(
                f"Critério '{criterio}' inválido. Utilize 'distancia', 'tempo' ou 'custo'."
            )

    def __repr__(self) -> str:
        return (
            f"Aresta(id='{self._id}', {self._origem.id} -> {self._destino.id}, "
            f"dist={self._distanciaMetros:.1f}m, tempo={self._tempoSegundos:.1f}s, "
            f"custo=R${self._custoReais:.2f})"
        )


class Grafo:
    """
    Grafo dirigido próprio para navegação urbana com suporte a pesos múltiplos.
    """

    def __init__(self) -> None:
        self._vertices: Dict[str, Vertice] = {}
        self._adjacencias: Dict[str, List[Aresta]] = {}

    @property
    def vertices(self) -> Dict[str, Vertice]:
        return self._vertices

    @property
    def adjacencias(self) -> Dict[str, List[Aresta]]:
        return self._adjacencias

    def adicionarVertice(self, vertice: Vertice) -> None:
        """Adiciona um vértice ao grafo caso ainda não exista."""
        if vertice.id not in self._vertices:
            self._vertices[vertice.id] = vertice
            self._adjacencias[vertice.id] = []

    def adicionarAresta(self, aresta: Aresta) -> None:
        """Adiciona uma aresta dirigida ao grafo, garantindo a existência dos vértices."""
        self.adicionarVertice(aresta.origem)
        self.adicionarVertice(aresta.destino)
        self._adjacencias[aresta.origem.id].append(aresta)

    def getVertice(self, id_vertice: str) -> Optional[Vertice]:
        """Recupera um vértice pelo identificador ou None se inexistente."""
        return self._vertices.get(id_vertice)

    def getAdjacencias(self, id_vertice: str) -> List[Aresta]:
        """Retorna a lista de arestas que partem do vértice informado."""
        return self._adjacencias.get(id_vertice, [])

    def quantidade_vertices(self) -> int:
        return len(self._vertices)

    def quantidade_arestas(self) -> int:
        return sum(len(arestas) for arestas in self._adjacencias.values())

    def __repr__(self) -> str:
        return f"Grafo(|V|={self.quantidade_vertices()}, |E|={self.quantidade_arestas()})"


class ResultadoRota:
    """
    Encapsula o resultado de uma busca de menor caminho (ex.: via Dijkstra).
    """

    def __init__(
        self,
        situacao: str,
        caminho: List[Aresta],
        distanciaTotalMetros: Optional[float] = None,
        tempoTotalSegundos: Optional[float] = None,
        custoTotalReais: Optional[float] = None,
        nosExpandidos: int = 0
    ) -> None:
        self._situacao = situacao
        self._caminho = list(caminho)
        self._distanciaTotalMetros = distanciaTotalMetros
        self._tempoTotalSegundos = tempoTotalSegundos
        self._custoTotalReais = custoTotalReais
        self._nosExpandidos = int(nosExpandidos)

    @property
    def situacao(self) -> str:
        return self._situacao

    @property
    def caminho(self) -> List[Aresta]:
        return self._caminho

    @property
    def distanciaTotalMetros(self) -> Optional[float]:
        return self._distanciaTotalMetros

    @property
    def tempoTotalSegundos(self) -> Optional[float]:
        return self._tempoTotalSegundos

    @property
    def custoTotalReais(self) -> Optional[float]:
        return self._custoTotalReais

    @property
    def nosExpandidos(self) -> int:
        return self._nosExpandidos

    def getDistanciaKm(self) -> Optional[float]:
        """Converte a distância total para quilômetros."""
        if self._distanciaTotalMetros is None:
            return None
        return self._distanciaTotalMetros / 1000.0

    def getTempoMinutos(self) -> Optional[float]:
        """Converte o tempo total estimado para minutos."""
        if self._tempoTotalSegundos is None:
            return None
        return self._tempoTotalSegundos / 60.0

    def __repr__(self) -> str:
        return (
            f"ResultadoRota(situacao='{self._situacao}', "
            f"dist={self._distanciaTotalMetros}m, "
            f"tempo={self._tempoTotalSegundos}s, "
            f"custo=R${self._custoReais if hasattr(self, '_custoReais') else self._custoTotalReais}, "
            f"nosExpandidos={self._nosExpandidos})"
        )
