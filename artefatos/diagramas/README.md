# Diagramas do Projeto

Este diretório armazena as fontes editáveis em PlantUML (`.txt`) e as respectivas exportações em imagem (`.png`) da modelagem do sistema de rotas urbanas.

## Diagramas Modelados

### 1. Diagrama de Classes (`diagramadeclassev3.txt` / `diagramadeclassev3.png`)
Representa a estrutura de dados central em `grafo.py`, conforme a implementação atual:
- **`Vertice`**: Identificador e coordenadas geográficas (latitude/longitude) dos cruzamentos e nós viários. Coordenadas fora da faixa válida, NaN ou infinitas são rejeitadas.
- **`Aresta`**: Segmento de via dirigido conectando vértices, contendo distância (m), velocidade (km/h), tempo estimado (s) e custo financeiro estimado (R$). Os pesos são finitos e não negativos. Suporta o método `getPeso(criterio)` para os três critérios do enum `Criterio`: `"distancia"`, `"tempo"` e `"custo"`.
- **`Grafo`**: Estrutura de listas de adjacência próprias para buscas orientadas. O id de cada aresta é único, o que permite identificar arestas paralelas (`getArestasEntre`, `getAresta`).
- **`ResultadoRota`**: Estrutura de retorno com situação da busca (enum `Situacao`: `"encontrada"`, `"inalcancavel"` ou `"invalida"`), sequência ordenada e contínua de arestas, custos consolidados (distância total em metros/km, tempo total em segundos/minutos, custo total em R$) e total de nós expandidos/maduros. Os construtores `aPartirDoCaminho`, `inalcancavel` e `invalida` garantem totais coerentes com o caminho.

A versão anterior (`diagramadeclassev2.txt` / `diagramadeclassev2.png`) é mantida como histórico.

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
