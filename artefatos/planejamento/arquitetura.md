# Arquitetura simples

A organização foi reduzida para facilitar a implementação e a explicação linha a linha. Não há código Python nesta etapa. Os arquivos abaixo serão criados quando a implementação começar.

## Cinco arquivos futuros

| Arquivo | Responsabilidade |
| --- | --- |
| `codigo/grafo.py` | Estrutura do grafo, entidades, resultado e cálculos geográficos puros |
| `codigo/mapa.py` | Leitura, validação e montagem do grafo em funções separadas |
| `codigo/rotas.py` | Dijkstra, A*, heurísticas e reconstrução do caminho |
| `codigo/app.py` | Interface, ligação entre as funções e apresentação dos resultados |
| `codigo/test_rotas.py` | Testes unitários e de integração do núcleo |

Os arquivos ficam diretamente em `codigo`, sem `src`, pacote interno ou camadas adicionais. O único subdiretório será `dados`, contendo futuramente o mapa e o cadastro dos pontos de interesse.

## Quatro classes do modelo

| Classe futura, em `grafo.py` | Responsabilidade |
| --- | --- |
| `Vertice` | Identificador e coordenadas de um nó viário |
| `Aresta` | Identidade, origem, destino, distância, velocidade e tempo de um segmento |
| `Grafo` | Vértices, arestas e listas de adjacência próprias |
| `ResultadoRota` | Situação da busca, sequência de arestas, custos e nós expandidos |

Os pontos de interesse serão registros simples com identificador, nome, coordenadas e nó viário associado. Não precisarão de uma classe própria.

Leitura e construção serão funções em `mapa.py`. Dijkstra e A* serão funções em `rotas.py`. A interface fará a coordenação, sem uma classe de serviço. Não haverá hierarquia de herança ou um arquivo separado para cada entidade.

## Dependências e fluxo

1. `app.py` chama a leitura do mapa em `mapa.py`.
2. `mapa.py` valida os registros e monta a estrutura de `grafo.py`.
3. `app.py` recebe a escolha de origem, destino, critério e algoritmo.
4. `rotas.py` executa a busca usando o grafo preparado e devolve `ResultadoRota`.
5. `app.py` apresenta o caminho e as métricas.

`grafo.py` não conhece arquivos ou interface. `rotas.py` utiliza o modelo e os cálculos geográficos, sem ler JSON, importar a interface ou consultar a internet. A duração de uma busca é medida fora dos algoritmos.

## Regras do problema que permanecem

- Grafo próprio dirigido, com arestas paralelas identificadas.
- Segmentos entre nós consecutivos, conectando vias somente por nós compartilhados.
- Sentidos únicos, rotatórias e filtros básicos de acesso para carros.
- Distância em metros, velocidade convertida para metros por segundo e tempo em segundos.
- Velocidade ausente ou inválida assumida como 30 km/h, registrando essa hipótese.
- Pontos de interesse associados a nós viários com acesso conferido.
- Dijkstra e A* com os mesmos parâmetros e o mesmo significado de resultado.
- Caminho reconstruído por arestas; empates podem gerar caminhos diferentes com o mesmo custo.
- Destino inalcançável com situação própria e custos indisponíveis; origem igual ao destino com custo zero.
- Solicitação inválida diferenciada de ausência de caminho.

Para A*, usar distância geográfica no critério distância e essa distância dividida pela maior velocidade atribuída ao grafo no critério tempo. A fila poderá usar `heapq`; a lógica dos algoritmos será do grupo.

## Limitações

O modelo será estático e acadêmico, para carros no Coração Eucarístico. Trânsito em tempo real, semáforos, barreiras, restrições de conversão, GPS e múltiplas paradas ficam fora desta versão. Os caminhos serão ótimos conforme o grafo e os pesos modelados.
