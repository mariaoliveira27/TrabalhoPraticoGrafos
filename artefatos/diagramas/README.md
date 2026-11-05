# Diagramas do Projeto

Este diretório armazena as fontes editáveis em PlantUML (`.txt`) e as respectivas exportações em imagem (`.png`) da modelagem do sistema de rotas urbanas.

## Diagramas Modelados

### 1. Diagrama de Classes (`diagramadeclassev2.txt` / `diagramadeclassev2.png`)
Representa a estrutura de dados central em `grafo.py`:
- **`Vertice`**: Identificador e coordenadas geográficas (latitude/longitude) dos cruzamentos e nós viários.
- **`Aresta`**: Segmentos de vias conectando vértices, contendo distância (m), velocidade (km/h), tempo estimado (s) e custo financeiro estimado (R$). Suporta o método `getPeso(criterio)` para os três critérios: `"distancia"`, `"tempo"` e `"custo"`.
- **`Grafo`**: Estrutura de listas de adjacência próprias para buscas orientadas.
- **`ResultadoRota`**: Estrutura de retorno com situação da busca, sequência ordenada de arestas, custos consolidados (distância total em metros/km, tempo total em segundos/minutos, custo total em R$) e total de nós expandidos/maduros.

### 2. Diagrama de Sequência (`diagramadesequencia.txt` / `diagramasequencia2.png`)
Representa a interação e o fluxo entre as camadas da ferramenta utilizando o **Método de Dijkstra**:
1. **Inicialização:** A `Interface` aciona o leitor `mapa.py`, que valida os dados de `mapa.json` e `pontos_interesse.json` e popula a instância de `Grafo`.
2. **Solicitação:** O `Usuário` seleciona ponto de partida, destino e o critério de otimização (distância, tempo ou custo financeiro).
3. **Cálculo da Rota:** A `Interface` invoca a função `calcularRotaDijkstra(...)` do módulo `rotas.py`.
4. **Execução:** O algoritmo executa o método clássico de Dijkstra baseado em cortes e relaxamento de arcos tensos:
   - Inicializa os potenciais de distância `dist[]` e o vetor de predecessores `pred[]`.
   - Seleciona iterativamente o vértice imaturo de menor distância no corte.
   - Avalia cada arco $(v, w)$ adjacente com `Aresta.getPeso(criterio)` e relaxa o arco se estiver tenso ($\text{dist}[v] + c < \text{dist}[w]$).
   - Declara o vértice $v$ como maduro e, ao alcançar o destino, reconstrói a sequência de arestas via `pred[]`.
5. **Apresentação:** A `Interface` (desenvolvida com Streamlit + Folium) renderiza o trajeto colorido sobre o mapa interativo do OpenStreetMap e exibe o resumo comparativo de métricas.

---

**Responsável principal pela manutenção dos diagramas:** Integrante 2, com revisão dos demais membros da equipe.
