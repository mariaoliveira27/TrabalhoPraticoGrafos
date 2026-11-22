# Código

## Estrutura simples

A implementação fica diretamente nesta pasta, com os módulos Python e a subpasta `dados`; os testes ficam em `tests`.

| Arquivo / pasta | Responsabilidade | Stack / Detalhes | Responsável |
| --- | --- | --- | --- |
| `grafo.py` | Classes `Vertice`, `Aresta`, `Grafo` e `ResultadoRota`; pesos para distância, tempo e custo financeiro; cálculos geográficos (Haversine) | Python padrão (`math`, `typing`) | Integrante 2 |
| `mapa.py` | Funções para ler, validar e converter o snapshot OSM e POIs em um grafo próprio; associação POI → vértice com a distância e limite da área do mapa (200 m) | Python padrão (`json`, `typing`) | Integrante 1, com apoio do 2 |
| `rotas.py` | Busca de caminho mínimo com Dijkstra e Bellman-Ford para distância, tempo ou custo | Python padrão (`heapq`, `typing`) | Integrante 3, com revisão do integrante 4 |
| `app.py` e `apoio_interface.py` | Interface gráfica interativa: mapa interativo, seleção de POIs, traçado da rota e métricas; `apoio_interface.py` concentra a lógica da tela (rótulos de critério, validação do pedido, formatação), testável sem Streamlit | **Streamlit + Folium** (`streamlit-folium`) | Integrante 5 |
| `tests/test_rotas_dijkstra_bellman_ford.py`, `tests/test_mapa.py` e `tests/test_apoio_interface.py` | Testes automatizados do grafo, importação, algoritmos, consistência de custo e benchmarks | `pytest`, `time` | Integrante 6, com testes de todos |
| `test_rotas.py` | Testes independentes de modelo, importação e busca (Dijkstra e Bellman-Ford) com grafos pequenos e respostas ótimas conhecidas, sem interface e sem rede. Rodar: `python -m pytest codigo/test_rotas.py -v` | `pytest` | Integrante 4 |
| `dados` | Arquivos `mapa.json` (OSM Coreu), `pontos_interesse.json` e documentação de origem | JSON / GeoJSON | Integrante 1 |

Os módulos mantêm uma arquitetura enxuta, sem camadas desnecessárias de serviços ou wrappers.

## Fluxo da ferramenta

1. O usuário abre o aplicativo via Streamlit (`streamlit run codigo/app.py`).
2. A interface aciona `mapa.py`, que carrega os dados locais e monta a estrutura em memória de `Grafo`.
3. O usuário seleciona origem e destino (entre os pontos de interesse a até 200 m de um vértice do grafo; os demais ficam de fora da seleção) e o critério de otimização (distância, tempo ou custo financeiro). O usuário escolhe Dijkstra ou Bellman-Ford.
4. `app.py` aciona a função de busca em `rotas.py`.
5. O algoritmo explora os nós, relaxa as arestas e devolve o `ResultadoRota`.
6. `app.py` recebe o resultado, plota o traçado colorido da rota sobre o mapa Folium e exibe na barra lateral o tempo de processamento, nós expandidos, distância em metros/km, tempo estimado e custo financeiro em Reais.

## Clean Code

- Nomes descritivos, tipos e unidades explícitas (`distancia_m`, `tempo_s`, `custo_reais`).
- Funções com responsabilidade única, sem duplicação de regras.
- Grafo e algoritmos implementados pelo grupo (sem bibliotecas externas para a busca em si).
- Todos os membros aptos a explicar linha a linha a implementação.

## Documentação de apoio

- [Arquitetura simples e classes](../artefatos/planejamento/arquitetura.md).
- [Critérios de Clean Code](../artefatos/planejamento/clean_code.md).
- [Divisão entre os seis integrantes](../artefatos/planejamento/equipe.md).
- [Testes e avaliação de desempenho](../artefatos/planejamento/validacao.md).
- [Dados do mapa](dados/README.md).
