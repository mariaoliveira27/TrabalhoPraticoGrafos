# Validação e avaliação de desempenho

Este documento separa correção funcional de experimentos de desempenho. Os testes abaixo existem em `codigo/tests`. O primeiro benchmark comparativo do snapshot local foi executado; seus arquivos e limites de interpretação estão em `artefatos/resultados/README.md`.

## Cobertura automatizada existente

A suíte `codigo/tests/test_rotas_dijkstra_bellman_ford.py` executa Dijkstra e Bellman-Ford em grafos sintéticos e no snapshot local. Ela cobre os três critérios (distância, tempo e custo), critérios e vértices inválidos, origem igual ao destino, destino inalcançável, arestas paralelas, empates, pesos zero e negativos, ciclos negativos no Bellman-Ford e validação cruzada de custos. Para cada caminho encontrado, verifica arestas dirigidas pertencentes ao grafo e soma dos pesos nos três critérios. `test_mapa.py` cobre leitura dos dados, montagem do grafo, mão única, coordenadas e parâmetros inválidos.

A interface liga os POIs aos vértices associados no snapshot e permite selecionar o algoritmo e critério. Testes automatizados de interface ponta a ponta ainda não constam na suíte. Há dois detalhes de interpretação: `nosExpandidos` conta vértices amadurecidos no Dijkstra e vértices examinados por passada no Bellman-Ford; os números não são diretamente equivalentes. Além disso, o benchmark deve usar os mesmos IDs de origem/destino já associados para os dois algoritmos.

`codigo/test_rotas.py` reúne testes independentes de modelo, importação e busca com grafos pequenos e respostas ótimas conhecidas (inclusive por força bruta): três critérios com rotas diferentes, mão única, arestas paralelas, empates, origem = destino, destino inalcançável, arquivos/referências/pesos inválidos e soma dos pesos igual ao custo informado. Uma fixture bloqueia qualquer acesso à rede durante esses testes.

Execute a suíte completa com `python -m pytest codigo -v` a partir da raiz do repositório, ou apenas esses testes com `python -m pytest codigo/test_rotas.py -v`. O tempo total do pytest não é métrica de busca.

## Protocolo e resultado do benchmark no snapshot local

A rotina `codigo/benchmark_rotas.py` executou todos os 182 pares ordenados distintos de um grafo com 14 vértices e 26 arestas direcionadas, nos três critérios. Foram feitas 20 repetições por algoritmo/par/critério, além de aquecimento. Os custos coincidiram em todas as comparações. As medianas medidas foram: distância — Dijkstra 0,04170 ms, Bellman-Ford 0,11870 ms; tempo — 0,03595 ms e 0,07710 ms; custo — 0,03340 ms e 0,06630 ms, respectivamente. São tempos deste snapshot pequeno e ambiente não isolado, sem conclusão de desempenho geral. Consulte os CSVs e metadados em `artefatos/resultados`.



Para reproduzir ou ampliar o experimento, compare os dois algoritmos no mesmo snapshot fixo e nos mesmos pares ordenados origem–destino, para cada um dos três critérios. Registre o custo encontrado e confirme que as rotas têm o mesmo custo ótimo antes de interpretar tempos. Use seleção determinística e publique a lista/semente dos pares para reprodução. Inclua também grafos sintéticos em grid de 100, 500 e 1.000 vértices, garantindo que cada comparação use o mesmo grafo, origem, destino e critério.

Para cada combinação de grafo, par e critério:

1. Faça uma execução de aquecimento de cada algoritmo.
2. Faça 20 repetições por algoritmo, alternando ou randomizando de forma determinística a ordem de execução para reduzir viés térmico.
3. Cronometre somente a chamada de busca, incluindo reconstrução do caminho (`time.perf_counter`); exclua leitura de arquivo, associação de POI, renderização Folium e Streamlit.
4. Registre algoritmo, critério, origem, destino, situação, custo ótimo, tempo de cada repetição, mediana e desvio padrão, `nosExpandidos`, |V| e |E|.
5. Registre versão/commit do código, Python, sistema operacional, processador, memória, política de energia e condições relevantes da máquina.

Dijkstra e Bellman-Ford contam nós expandidos de maneiras diferentes, conforme definido pela implementação; preserve a métrica bruta e explique essa diferença. Não apresente esses totais como operações equivalentes. Os resultados e gráficos existentes estão guardados em `artefatos/resultados/tabelas` e `artefatos/resultados/figuras`, com unidades, parâmetros e versão do código. Registre somente dados efetivamente medidos.
