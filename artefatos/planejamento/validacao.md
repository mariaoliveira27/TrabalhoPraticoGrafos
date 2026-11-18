# Validação e avaliação de desempenho

Este documento separa correção funcional de experimentos de desempenho. Os testes abaixo existem em `codigo/tests`; benchmarks não foram executados e nenhum resultado experimental é reportado aqui.

## Cobertura automatizada existente

A suíte `codigo/tests/test_rotas_dijkstra_bellman_ford.py` executa Dijkstra e Bellman-Ford em grafos sintéticos e no snapshot local. Ela cobre os três critérios (distância, tempo e custo), critérios e vértices inválidos, origem igual ao destino, destino inalcançável, arestas paralelas, empates, pesos zero e negativos, ciclos negativos no Bellman-Ford e validação cruzada de custos. Para cada caminho encontrado, verifica arestas dirigidas pertencentes ao grafo e soma dos pesos nos três critérios. `test_mapa.py` cobre leitura dos dados, montagem do grafo, mão única, coordenadas e parâmetros inválidos.

A interface liga os POIs aos vértices associados no snapshot e permite selecionar o algoritmo e critério. Testes automatizados de interface ponta a ponta ainda não constam na suíte. Há dois detalhes de interpretação: `nosExpandidos` conta vértices amadurecidos no Dijkstra e vértices examinados por passada no Bellman-Ford; os números não são diretamente equivalentes. Além disso, o benchmark deve usar os mesmos IDs de origem/destino já associados para os dois algoritmos.

Execute a suíte com `python -m pytest codigo/tests -v` a partir da raiz do repositório. O tempo total do pytest não é métrica de busca.

## Protocolo de benchmark (a executar)

Compare os dois algoritmos no mesmo snapshot fixo e nos mesmos pares ordenados origem–destino, para cada um dos três critérios. Registre o custo encontrado e confirme que as rotas têm o mesmo custo ótimo antes de interpretar tempos. Use seleção determinística e publique a lista/semente dos pares para reprodução. Inclua também grafos sintéticos em grid de 100, 500 e 1.000 vértices, garantindo que cada comparação use o mesmo grafo, origem, destino e critério.

Para cada combinação de grafo, par e critério:

1. Faça uma execução de aquecimento de cada algoritmo.
2. Faça 20 repetições por algoritmo, alternando ou randomizando de forma determinística a ordem de execução para reduzir viés térmico.
3. Cronometre somente a chamada de busca, incluindo reconstrução do caminho (`time.perf_counter`); exclua leitura de arquivo, associação de POI, renderização Folium e Streamlit.
4. Registre algoritmo, critério, origem, destino, situação, custo ótimo, tempo de cada repetição, mediana e desvio padrão, `nosExpandidos`, |V| e |E|.
5. Registre versão/commit do código, Python, sistema operacional, processador, memória, política de energia e condições relevantes da máquina.

Dijkstra e Bellman-Ford contam nós expandidos de maneiras diferentes, conforme definido pela implementação; preserve a métrica bruta e explique essa diferença. Não apresente esses totais como operações equivalentes. Os resultados e gráficos devem ser guardados em `artefatos/resultados/tabelas` e `artefatos/resultados/figuras`, com unidades, parâmetros e versão do código. Registre somente dados efetivamente medidos.
