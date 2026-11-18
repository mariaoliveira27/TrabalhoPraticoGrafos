# Resultados de benchmark

O benchmark comparativo foi executado em 18/11/2026 sobre o snapshot local `codigo/dados/mapa.json`. A rotina está em `codigo/benchmark_rotas.py` e pode ser reproduzida a partir da raiz com `python codigo/benchmark_rotas.py`.

## Experimento medido

O grafo contém 14 vértices e 26 arestas direcionadas. Foram avaliados todos os 182 pares ordenados distintos, nos critérios distância, tempo e custo, com uma execução de aquecimento por algoritmo/consulta e 20 repetições cronometradas. Isso resulta em 3.640 buscas por algoritmo e critério. A ordem dos pares usa a semente 20261118; a ordem de execução dos algoritmos alterna deterministicamente. `time.perf_counter` mede apenas a chamada do algoritmo, incluindo a reconstrução do caminho. Leitura do JSON e montagem do grafo ficam fora da medição.

Ambos os algoritmos devolveram custos idênticos em todos os pares e critérios. Há pares inalcançáveis: o custo médio abaixo considera somente rotas encontradas. A mediana e o desvio padrão são calculados sobre as 3.640 medições individuais por algoritmo/critério. O desvio padrão elevado em relação à mediana reflete, entre outros fatores, a escala muito curta das buscas e a variabilidade do ambiente compartilhado; não generalize estes tempos para grafos maiores.

| Critério | Algoritmo | Mediana (ms/busca) | Desvio padrão (ms) | Nós expandidos, mediana | Custo médio das rotas encontradas |
| --- | --- | ---: | ---: | ---: | ---: |
| Distância | Dijkstra | 0,04170 | 0,08737 | 5 | 624,460 m |
| Distância | Bellman-Ford | 0,11870 | 0,11406 | 27 | 624,460 m |
| Tempo | Dijkstra | 0,03595 | 0,04031 | 5 | 60,983 s |
| Tempo | Bellman-Ford | 0,07710 | 0,07903 | 27 | 60,983 s |
| Custo | Dijkstra | 0,03340 | 0,04475 | 5 | R$ 0,3622 |
| Custo | Bellman-Ford | 0,06630 | 0,07350 | 27 | R$ 0,3622 |

`nos_expandidos` segue definições diferentes na implementação: Dijkstra conta vértices amadurecidos; Bellman-Ford soma os vértices examinados nas passadas. Os números estão registrados como métricas brutas e não equivalem a uma contagem idêntica de operações.

## Arquivos

- `tabelas/benchmark_buscas_brutas.csv`: cada busca cronometrada, com algoritmo, critério, par, repetição, situação, custo, tempo e nós expandidos.
- `tabelas/benchmark_resumo.csv`: estatísticas agregadas e tamanho do grafo.
- `tabelas/benchmark_metadados.json`: snapshot, método, versão do Python, sistema, processador e condições registradas. A memória RAM não foi coletada.
- `figuras/benchmark_tempo_mediano.png`: comparação das medianas em milissegundos.

A medição foi feita em Windows 11, Python 3.12.6, CPU Intel64 Family 6 Model 142, com 4 CPUs lógicas. A máquina não estava isolada de outras tarefas e a RAM não foi registrada. Não foram medidos grafos sintéticos; esta comparação descreve somente o snapshot local.
