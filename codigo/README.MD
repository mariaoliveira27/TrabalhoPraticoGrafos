# Código

## Estrutura simples

A implementação futura ficará diretamente nesta pasta, com apenas `dados` como subpasta. Nesta etapa inicial há somente organização e documentação: nenhum arquivo Python foi criado ainda.

| Arquivo futuro, ainda não criado | Responsabilidade | Stack / Detalhes | Responsável |
| --- | --- | --- | --- |
| `grafo.py` | Classes `Vertice`, `Aresta`, `Grafo` e `ResultadoRota`; pesos para distância, tempo e custo financeiro; cálculos geográficos (Haversine) | Python padrão (`math`, `typing`) | Integrante 2 |
| `mapa.py` | Funções para ler, validar e converter o snapshot OSM e POIs em um grafo próprio | Python padrão (`json`, `typing`) | Integrante 1, com apoio do 2 |
| `rotas.py` | Busca de caminho mínimo com Dijkstra para distância, tempo ou custo e reconstrução do caminho | Python padrão (`heapq`, `typing`) | Integrante 3, com revisão do integrante 4 |
| `app.py` | Interface gráfica interativa: mapa interativo, seleção de POIs, traçado da rota e métricas | **Streamlit + Folium** (`streamlit-folium`) | Integrante 5 |
| `test_rotas.py` | Testes automatizados do grafo, importação, algoritmos, consistência de custo e benchmarks | `pytest`, `time` | Integrante 6, com testes de todos |
| `dados` | Arquivos `mapa.json` (OSM Coreu), `pontos_interesse.json` e documentação de origem | JSON / GeoJSON | Integrante 1 |

Os cinco arquivos são o ponto de partida arquitetural enxuto, sem camadas desnecessárias de serviços ou wrappers.

## Fluxo da ferramenta

1. O usuário abre o aplicativo via Streamlit (`streamlit run codigo/app.py`).
2. A interface aciona `mapa.py`, que carrega os dados locais e monta a estrutura em memória de `Grafo`.
3. O usuário seleciona origem e destino (a partir dos 10 pontos de interesse ou nós do mapa) e o critério de otimização (distância, tempo ou custo financeiro). O cálculo será feito pelo algoritmo de Dijkstra.
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
