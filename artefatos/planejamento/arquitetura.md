# Arquitetura simples

A organização foi reduzida para facilitar a implementação e a explicação linha a linha. Não há código Python nesta etapa. Os arquivos abaixo serão criados quando a implementação começar.

## Cinco arquivos futuros

| Arquivo | Responsabilidade | Stack / Bibliotecas |
| --- | --- | --- |
| `codigo/grafo.py` | Estrutura do grafo próprio (sem NetworkX), entidades (`Vertice`, `Aresta`, `Grafo`, `ResultadoRota`), pesos por critério e cálculos geográficos puros (Haversine) | Python padrão (`math`, `typing`) |
| `codigo/mapa.py` | Leitura, validação e montagem do grafo a partir do snapshot OSM e POIs | Python padrão (`json`, `typing`) |
| `codigo/rotas.py` | Implementação do Método de Dijkstra (relaxamento de arcos tensos, controle de predecessores e reconstrução de caminhos mínimos) | Python padrão (`heapq`, `typing`) |
| `codigo/app.py` | Interface gráfica interativa: renderização do mapa, seleção de parâmetros e exibição das métricas | **Streamlit + Folium** (`streamlit`, `folium`, `streamlit-folium`) |
| `codigo/test_rotas.py` | Testes unitários de borda, testes de integração e benchmarks de desempenho empírico | `pytest`, `time` |

Os arquivos ficam diretamente em `codigo`, sem `src`, pacote interno ou camadas adicionais. O único subdiretório será `dados`, contendo futuramente o mapa e o cadastro dos pontos de interesse.

## Quatro classes do modelo

| Classe futura, em `grafo.py` | Responsabilidade |
| --- | --- |
| `Vertice` | Identificador e coordenadas geográficas (latitude e longitude) de um cruzamento ou nó viário |
| `Aresta` | Identidade, origem, destino, distância (m), velocidade (km/h), tempo estimado (s) e custo financeiro estimado (R$) de um segmento viário |
| `Grafo` | Vértices, arestas e listas de adjacência próprias indexadas |
| `ResultadoRota` | Situação da busca, sequência ordenada de arestas, custos consolidados (distância, tempo e financeiro) e quantidade de nós expandidos/maduros |

Os pontos de interesse serão registros simples com identificador, nome, coordenadas e nó viário associado. Não precisarão de uma classe própria.

Leitura e construção serão funções em `mapa.py`. A busca pelo menor caminho será executada pelo algoritmo de Dijkstra em `rotas.py`. A interface (`app.py`) fará a coordenação entre a entrada do usuário, as buscas e a renderização no mapa interativo com Folium. Não haverá hierarquia pesada de herança ou um arquivo separado para cada entidade.

## Dependências e fluxo

1. `app.py` inicia e chama a leitura do mapa em `mapa.py`.
2. `mapa.py` valida os registros de `mapa.json` e `pontos_interesse.json` e monta a estrutura de `Grafo`.
3. `app.py` recebe a escolha do usuário: origem, destino e critério de otimização (tempo, distância ou custo).
4. `rotas.py` executa a busca (`calcularRotaDijkstra`) usando o grafo preparado e devolve uma instância de `ResultadoRota`.
5. `app.py` renderiza o traçado do caminho sobre o mapa Folium e apresenta as métricas consolidadas na barra lateral do Streamlit.

`grafo.py` não conhece arquivos ou interface. `rotas.py` utiliza o modelo e os cálculos geográficos, sem ler JSON, importar a interface ou consultar a internet. A duração de uma busca é cronometrada estritamente fora do algoritmo.

## Regras do problema e Critérios de Otimização

- Grafo próprio dirigido, com arestas paralelas identificadas.
- Proibida a utilização de bibliotecas prontas para criação e processamento do grafo (como NetworkX), salvo para comparação de performance (conforme especificado no enunciado do TP).
- Segmentos entre nós consecutivos, conectando vias somente por nós compartilhados.
- Sentidos únicos, rotatórias e filtros básicos de acesso para carros.
- **Três critérios de otimização suportados:**
  1. **Distância:** peso da aresta em metros ($m$).
  2. **Tempo:** peso da aresta em segundos ($s$), calculado por $\text{tempo} = \text{distancia} / \text{velocidade (m/s)}$. Velocidade ausente ou inválida assumida como 30 km/h (hipótese documentada).
  3. **Custo:** custo financeiro estimado em Reais (R$) para o percurso do segmento, calculado a partir de um consumo veicular médio (ex: 10 km/l) e preço médio do combustível (ex: R$ 5,80/l): $\text{custo} = (\text{distancia\_m} / 1000.0) / \text{consumo} \times \text{preco}$.
- Pontos de interesse associados a nós viários com acesso conferido.
- Caminho reconstruído por sequência de arestas a partir do vetor de predecessores `pred[]`; empates de custo podem gerar caminhos alternativos equivalentes.
- Destino inalcançável com situação própria e custos indisponíveis; origem igual ao destino com custo zero.
- Solicitação inválida diferenciada de ausência de caminho.

### Fundamentação Teórica: Método de Dijkstra (1959) e Condições de Minimalidade

Conforme abordado na disciplina (Prof. Leonardo Vilela Cardoso), o algoritmo se fundamenta em:
1. **Corte e Estimativas:**
   - Para um subconjunto de vértices explorados $S \subset V$, o corte é definido por $\text{corte}(S) = \{ (v, w) \in E \mid v \in S, w \notin S \}$.
   - O algoritmo seleciona iterativamente a aresta do corte que minimiza a estimativa de distância a partir da raiz: $\text{dist}[v] + d_{vw}$.
2. **Potencial e Arcos Tensos:**
   - O vetor de distâncias $\text{dist}[]$ atua como um potencial nos vértices.
   - Um arco $(v, w)$ de custo $c$ está:
     - **Tenso** se $\text{dist}[v] + c < \text{dist}[w]$;
     - **Relaxado** se $\text{dist}[v] + c \ge \text{dist}[w]$;
     - **Justo** se $\text{dist}[v] + c = \text{dist}[w]$.
   - Durante a iteração sobre o vértice imaturo selecionado $v$, relaxam-se todos os arcos tensos que partem de $v$:
     $$\text{dist}[w] \leftarrow \text{dist}[v] + c, \quad \text{pred}[w] \leftarrow v$$
   - Após examinar os arcos adjacentes, $v$ é declarado **maduro** (pertencente à árvore de caminhos mínimos).
3. **Eficiência:**
   - Implementado com fila de prioridade (`heapq`), atingindo complexidade assintótica $O((|V| + |E|) \log |V|)$.

## Limitações

O modelo será estático e acadêmico, para carros no Coração Eucarístico. Trânsito em tempo real, semáforos, barreiras temporárias, restrições complexas de conversão, GPS ao vivo e múltiplas paradas intermediárias ficam fora desta versão. Os caminhos serão ótimos conforme o grafo e os pesos modelados.
