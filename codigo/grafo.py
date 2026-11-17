"""
Modelo do grafo viário usado no sistema de otimização de rotas.

Contém as classes Vertice, Aresta, Grafo e ResultadoRota (diagrama de classes v2).
Este módulo não lê arquivos, não acessa a internet e não conhece a interface:
os pesos de cada aresta (distância, tempo e custo) são calculados em mapa.py e
aqui apenas armazenados, validados e consultados por critério.

Unidades dos pesos:
    - distancia: metros (m)
    - tempo: segundos (s)
    - custo: Reais (R$), gasto estimado com combustível

Exemplo de uso:
    >>> a = Vertice("A", -19.9220, -43.9930)
    >>> b = Vertice("B", -19.9230, -43.9920)
    >>> grafo = Grafo()
    >>> grafo.adicionarAresta(Aresta("e1", a, b, 150.0, 30.0, 18.0, 0.087))
    >>> grafo.getAdjacencias("A")[0].getPeso(CRITERIO_TEMPO)
    18.0
    >>> resultado = ResultadoRota.aPartirDoCaminho(grafo.getAdjacencias("A"), nosExpandidos=2)
    >>> resultado.situacao, resultado.distanciaTotalMetros
    ('encontrada', 150.0)
"""

import math
from typing import Dict, List, Optional

# Critérios de otimização aceitos por Aresta.getPeso
CRITERIO_DISTANCIA = "distancia"
CRITERIO_TEMPO = "tempo"
CRITERIO_CUSTO = "custo"
CRITERIOS_VALIDOS = (CRITERIO_DISTANCIA, CRITERIO_TEMPO, CRITERIO_CUSTO)

# Situações possíveis de uma busca (ResultadoRota.situacao)
SITUACAO_ENCONTRADA = "encontrada"      # existe caminho; custos preenchidos
SITUACAO_INALCANCAVEL = "inalcancavel"  # pedido válido, mas não há caminho
SITUACAO_INVALIDA = "invalida"          # pedido inválido (vértice ou critério inexistente)
SITUACOES_VALIDAS = (SITUACAO_ENCONTRADA, SITUACAO_INALCANCAVEL, SITUACAO_INVALIDA)


def _validarNumeroFinito(valor: float, nome: str) -> float:
    """Converte o valor para float e garante que não é NaN nem infinito."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{nome} deve ser numérico, recebido: {valor!r}") from None
    if not math.isfinite(numero):
        raise ValueError(f"{nome} deve ser um número finito, recebido: {valor!r}")
    return numero


def _validarId(identificador: str, nome: str) -> str:
    """Garante que o identificador não é vazio."""
    texto = str(identificador).strip() if identificador is not None else ""
    if not texto:
        raise ValueError(f"{nome} não pode ser vazio")
    return texto


def normalizarCriterio(criterio: str) -> str:
    """
    Normaliza e valida o nome de um critério de otimização.

    Aceita maiúsculas e espaços extras ('  Tempo ' -> 'tempo').
    Lança ValueError se o critério não for 'distancia', 'tempo' ou 'custo'.
    """
    if not isinstance(criterio, str):
        raise ValueError(f"Critério deve ser texto, recebido: {criterio!r}")
    criterio_limpo = criterio.strip().lower()
    if criterio_limpo not in CRITERIOS_VALIDOS:
        raise ValueError(
            f"Critério '{criterio}' inválido. Utilize 'distancia', 'tempo' ou 'custo'."
        )
    return criterio_limpo


class Vertice:
    """
    Vértice do grafo: um cruzamento ou ponto georreferenciado da malha viária.

    Atributos:
        id: identificador único no grafo.
        latitude, longitude: coordenadas em graus decimais (WGS84).
        nome: descrição opcional (ex.: nome do cruzamento).
    """

    def __init__(
        self,
        id_vertice: str,
        latitude: float,
        longitude: float,
        nome: Optional[str] = None
    ) -> None:
        latitude = _validarNumeroFinito(latitude, "latitude")
        longitude = _validarNumeroFinito(longitude, "longitude")
        if not (-90.0 <= latitude <= 90.0):
            raise ValueError(f"Latitude inválida: {latitude}")
        if not (-180.0 <= longitude <= 180.0):
            raise ValueError(f"Longitude inválida: {longitude}")

        self._id = _validarId(id_vertice, "id do vértice")
        self._latitude = latitude
        self._longitude = longitude
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

    def mesmaPosicao(self, outro: "Vertice") -> bool:
        """Indica se outro vértice tem as mesmas coordenadas deste."""
        return self._latitude == outro.latitude and self._longitude == outro.longitude

    def __repr__(self) -> str:
        return f"Vertice(id='{self._id}', lat={self._latitude:.6f}, lon={self._longitude:.6f}, nome='{self._nome}')"


class Aresta:
    """
    Aresta dirigida (segmento de via percorrido no sentido origem -> destino).

    Uma rua de mão dupla é representada por duas arestas, uma em cada sentido.
    Duas arestas com mesma origem e destino (arestas paralelas) são permitidas
    e diferenciadas pelo id, que deve ser único no grafo.

    Pesos (todos finitos e não negativos):
        distanciaMetros: comprimento do segmento (m).
        velocidadeKmH: velocidade considerada na via (km/h), estritamente positiva.
        tempoSegundos: tempo para percorrer o segmento (s).
        custoReais: custo estimado de combustível no segmento (R$).
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
        if not isinstance(origem, Vertice) or not isinstance(destino, Vertice):
            raise TypeError("origem e destino da aresta devem ser instâncias de Vertice")

        distanciaMetros = _validarNumeroFinito(distanciaMetros, "distanciaMetros")
        velocidadeKmH = _validarNumeroFinito(velocidadeKmH, "velocidadeKmH")
        tempoSegundos = _validarNumeroFinito(tempoSegundos, "tempoSegundos")
        custoReais = _validarNumeroFinito(custoReais, "custoReais")

        if distanciaMetros < 0:
            raise ValueError("distanciaMetros não pode ser negativa")
        if velocidadeKmH <= 0:
            raise ValueError("velocidadeKmH deve ser estritamente positiva")
        if tempoSegundos < 0:
            raise ValueError("tempoSegundos não pode ser negativo")
        if custoReais < 0:
            raise ValueError("custoReais não pode ser negativo")

        self._id = _validarId(id_aresta, "id da aresta")
        self._origem = origem
        self._destino = destino
        self._distanciaMetros = distanciaMetros
        self._velocidadeKmH = velocidadeKmH
        self._tempoSegundos = tempoSegundos
        self._custoReais = custoReais

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
        Retorna o peso da aresta para o critério de otimização informado:
        - 'distancia': distância em metros
        - 'tempo': tempo estimado em segundos
        - 'custo': custo estimado em Reais (combustível)

        O peso nunca é negativo, condição exigida pelo algoritmo de Dijkstra.
        Lança ValueError para critério desconhecido.
        """
        criterio_limpo = normalizarCriterio(criterio)
        if criterio_limpo == CRITERIO_DISTANCIA:
            return self._distanciaMetros
        if criterio_limpo == CRITERIO_TEMPO:
            return self._tempoSegundos
        return self._custoReais

    def __repr__(self) -> str:
        return (
            f"Aresta(id='{self._id}', {self._origem.id} -> {self._destino.id}, "
            f"dist={self._distanciaMetros:.1f}m, tempo={self._tempoSegundos:.1f}s, "
            f"custo=R${self._custoReais:.2f})"
        )


class Grafo:
    """
    Grafo dirigido próprio (sem NetworkX) representado por listas de adjacência.

    vertices: id do vértice -> Vertice
    adjacencias: id do vértice -> lista de arestas que SAEM dele
    """

    def __init__(self) -> None:
        self._vertices: Dict[str, Vertice] = {}
        self._adjacencias: Dict[str, List[Aresta]] = {}
        self._arestas: Dict[str, Aresta] = {}

    @property
    def vertices(self) -> Dict[str, Vertice]:
        return self._vertices

    @property
    def adjacencias(self) -> Dict[str, List[Aresta]]:
        return self._adjacencias

    def adicionarVertice(self, vertice: Vertice) -> None:
        """
        Adiciona um vértice ao grafo.

        Adicionar de novo o mesmo vértice (mesmo id e mesmas coordenadas) não tem efeito.
        Lança ValueError se já existir outro vértice com o mesmo id e coordenadas diferentes.
        """
        if not isinstance(vertice, Vertice):
            raise TypeError("Somente instâncias de Vertice podem ser adicionadas ao grafo")

        existente = self._vertices.get(vertice.id)
        if existente is None:
            self._vertices[vertice.id] = vertice
            self._adjacencias[vertice.id] = []
        elif not existente.mesmaPosicao(vertice):
            raise ValueError(
                f"Vértice '{vertice.id}' já existe com coordenadas diferentes "
                f"({existente.latitude}, {existente.longitude})"
            )

    def adicionarAresta(self, aresta: Aresta) -> None:
        """
        Adiciona uma aresta dirigida ao grafo, incluindo origem e destino se ainda não existirem.

        Lança ValueError se já existir uma aresta com o mesmo id (arestas paralelas
        devem ter ids distintos).
        """
        if not isinstance(aresta, Aresta):
            raise TypeError("Somente instâncias de Aresta podem ser adicionadas ao grafo")
        if aresta.id in self._arestas:
            raise ValueError(f"Já existe uma aresta com id '{aresta.id}' no grafo")

        self.adicionarVertice(aresta.origem)
        self.adicionarVertice(aresta.destino)
        self._adjacencias[aresta.origem.id].append(aresta)
        self._arestas[aresta.id] = aresta

    def getVertice(self, id_vertice: str) -> Optional[Vertice]:
        """Retorna o vértice com o id informado, ou None se não existir."""
        return self._vertices.get(id_vertice)

    def existeVertice(self, id_vertice: str) -> bool:
        """Indica se há um vértice com o id informado."""
        return id_vertice in self._vertices

    def getAdjacencias(self, id_vertice: str) -> List[Aresta]:
        """Retorna as arestas que partem do vértice informado (lista vazia se não existir)."""
        return self._adjacencias.get(id_vertice, [])

    def getAresta(self, id_aresta: str) -> Optional[Aresta]:
        """Retorna a aresta com o id informado, ou None se não existir."""
        return self._arestas.get(id_aresta)

    def getArestasEntre(self, id_origem: str, id_destino: str) -> List[Aresta]:
        """Retorna todas as arestas origem -> destino (mais de uma quando há arestas paralelas)."""
        return [a for a in self.getAdjacencias(id_origem) if a.destino.id == id_destino]

    def getArestas(self) -> List[Aresta]:
        """Retorna todas as arestas do grafo, na ordem de inserção."""
        return list(self._arestas.values())

    def quantidade_vertices(self) -> int:
        return len(self._vertices)

    def quantidade_arestas(self) -> int:
        return len(self._arestas)

    def __repr__(self) -> str:
        return f"Grafo(|V|={self.quantidade_vertices()}, |E|={self.quantidade_arestas()})"


class ResultadoRota:
    """
    Resultado de uma busca de menor caminho (Dijkstra, em rotas.py).

    situacao:
        - 'encontrada': caminho existe; totais preenchidos (zero quando origem = destino).
        - 'inalcancavel': pedido válido, mas o destino não é alcançável; caminho vazio e totais None.
        - 'invalida': pedido inválido (vértice ou critério inexistente); caminho vazio e totais None.
    caminho: arestas na ordem do percurso; o destino de cada uma é a origem da seguinte.
    nosExpandidos: quantidade de vértices retirados da fila e declarados maduros.

    Prefira os construtores aPartirDoCaminho, inalcancavel e invalida, que garantem
    totais coerentes com o caminho.
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
        if situacao not in SITUACOES_VALIDAS:
            raise ValueError(
                f"Situação '{situacao}' inválida. Utilize uma de {SITUACOES_VALIDAS}."
            )
        caminho = list(caminho)
        totais = (distanciaTotalMetros, tempoTotalSegundos, custoTotalReais)

        if situacao == SITUACAO_ENCONTRADA:
            if any(total is None for total in totais):
                raise ValueError("Rota encontrada precisa ter distância, tempo e custo totais")
            for total, nome in zip(totais, ("distanciaTotalMetros", "tempoTotalSegundos", "custoTotalReais")):
                if _validarNumeroFinito(total, nome) < 0:
                    raise ValueError(f"{nome} não pode ser negativo")
            for anterior, seguinte in zip(caminho, caminho[1:]):
                if anterior.destino.id != seguinte.origem.id:
                    raise ValueError(
                        f"Caminho descontínuo: aresta '{anterior.id}' termina em "
                        f"'{anterior.destino.id}', mas '{seguinte.id}' começa em '{seguinte.origem.id}'"
                    )
        else:
            if caminho:
                raise ValueError(f"Resultado '{situacao}' não pode ter caminho")
            if any(total is not None for total in totais):
                raise ValueError(f"Resultado '{situacao}' não pode ter totais")

        if int(nosExpandidos) < 0:
            raise ValueError("nosExpandidos não pode ser negativo")

        self._situacao = situacao
        self._caminho = caminho
        self._distanciaTotalMetros = None if distanciaTotalMetros is None else float(distanciaTotalMetros)
        self._tempoTotalSegundos = None if tempoTotalSegundos is None else float(tempoTotalSegundos)
        self._custoTotalReais = None if custoTotalReais is None else float(custoTotalReais)
        self._nosExpandidos = int(nosExpandidos)

    @classmethod
    def aPartirDoCaminho(cls, caminho: List[Aresta], nosExpandidos: int = 0) -> "ResultadoRota":
        """
        Cria um resultado 'encontrada' somando os pesos das arestas do caminho.

        Caminho vazio representa origem igual ao destino (todos os totais zero).
        """
        caminho = list(caminho)
        return cls(
            situacao=SITUACAO_ENCONTRADA,
            caminho=caminho,
            distanciaTotalMetros=math.fsum(a.distanciaMetros for a in caminho),
            tempoTotalSegundos=math.fsum(a.tempoSegundos for a in caminho),
            custoTotalReais=math.fsum(a.custoReais for a in caminho),
            nosExpandidos=nosExpandidos,
        )

    @classmethod
    def inalcancavel(cls, nosExpandidos: int = 0) -> "ResultadoRota":
        """Cria um resultado para destino que não pode ser alcançado a partir da origem."""
        return cls(SITUACAO_INALCANCAVEL, [], nosExpandidos=nosExpandidos)

    @classmethod
    def invalida(cls) -> "ResultadoRota":
        """Cria um resultado para pedido inválido (vértice ou critério inexistente)."""
        return cls(SITUACAO_INVALIDA, [])

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

    def foiEncontrada(self) -> bool:
        """Indica se a busca encontrou um caminho."""
        return self._situacao == SITUACAO_ENCONTRADA

    def getTotal(self, criterio: str) -> Optional[float]:
        """Retorna o total da rota no critério informado (None se não houver rota)."""
        criterio_limpo = normalizarCriterio(criterio)
        if criterio_limpo == CRITERIO_DISTANCIA:
            return self._distanciaTotalMetros
        if criterio_limpo == CRITERIO_TEMPO:
            return self._tempoTotalSegundos
        return self._custoTotalReais

    def getVerticesCaminho(self) -> List[Vertice]:
        """
        Retorna os vértices percorridos, na ordem (útil para desenhar a rota no mapa).

        Lista vazia quando não há caminho ou quando origem = destino (caminho sem arestas).
        """
        if not self._caminho:
            return []
        return [self._caminho[0].origem] + [a.destino for a in self._caminho]

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
            f"custo=R${self._custoTotalReais}, "
            f"nosExpandidos={self._nosExpandidos})"
        )
