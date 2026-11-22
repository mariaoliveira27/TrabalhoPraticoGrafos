# Resultados de benchmark

O benchmark comparativo foi executado em 22/11/2026 sobre o snapshot local `codigo/dados/mapa.json`. A rotina está em `codigo/benchmark_rotas.py` e pode ser reproduzida a partir da raiz com `python codigo/benchmark_rotas.py`.

## Experimento medido

O grafo contém 34 vértices e 68 arestas direcionadas. Foram avaliados todos os 1.122 pares ordenados distintos, nos critérios distância, tempo e custo, com uma execução de aquecimento por algoritmo/consulta e 20 repetições cronometradas. Isso resulta em 22.440 buscas por algoritmo e critério. A ordem dos pares usa a semente 20261118; a ordem de execução dos algoritmos alterna deterministicamente. `time.perf_counter` mede apenas a chamada do algoritmo, incluindo a reconstrução do caminho. Leitura do JSON e montagem do grafo ficam fora da medição.

Ambos os algoritmos devolveram custos idênticos em todos os pares e critérios. Todos os pares têm rota (o grafo é fortemente conexo), então o custo médio abaixo considera as 1.122 rotas de cada critério. A mediana e o desvio padrão são calculados sobre as 22.440 medições individuais por algoritmo/critério. O desvio padrão reflete, entre outros fatores, a escala muito curta das buscas e a variabilidade do ambiente compartilhado; não generalize estes tempos para grafos maiores.

| Critério | Algoritmo | Mediana (ms/busca) | Desvio padrão (ms) | Nós expandidos, mediana | Custo médio das rotas encontradas |
| --- | --- | ---: | ---: | ---: | ---: |
| Distância | Dijkstra | 0,03010 | 0,01399 | 18 | 915,823 m |
| Distância | Bellman-Ford | 0,13190 | 0,02676 | 153,5 | 915,823 m |
| Tempo | Dijkstra | 0,03060 | 0,04784 | 18 | 87,053 s |
| Tempo | Bellman-Ford | 0,13760 | 0,02423 | 153,5 | 87,053 s |
| Custo | Dijkstra | 0,03070 | 0,01345 | 18 | R$ 0,5312 |
| Custo | Bellman-Ford | 0,13880 | 0,02293 | 153,5 | R$ 0,5312 |

`nos_expandidos` segue definições diferentes na implementação: Dijkstra conta vértices amadurecidos; Bellman-Ford soma os vértices examinados nas passadas. Os números estão registrados como métricas brutas e não equivalem a uma contagem idêntica de operações.

## Arquivos

- `tabelas/benchmark_buscas_brutas.csv`: cada busca cronometrada, com algoritmo, critério, par, repetição, situação, custo, tempo e nós expandidos.
- `tabelas/benchmark_resumo.csv`: estatísticas agregadas e tamanho do grafo.
- `tabelas/benchmark_metadados.json`: snapshot, método, versão do Python, sistema, processador e condições registradas. A memória RAM não foi coletada.
- `figuras/benchmark_tempo_mediano.png`: comparação das medianas em milissegundos.

A medição foi feita em Windows 11, Python 3.12.10, CPU AMD64 Family 25 Model 80, com 12 CPUs lógicas. A máquina não estava isolada de outras tarefas e a RAM não foi registrada. Não foram medidos grafos sintéticos; esta comparação descreve somente o snapshot local.
