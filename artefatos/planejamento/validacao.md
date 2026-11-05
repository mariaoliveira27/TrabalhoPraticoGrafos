# Validação e avaliação de desempenho

Este documento reúne as orientações para testes de software e experimentos empíricos. Nenhum teste ou experimento foi executado nesta etapa inicial.

## Testes de correção

O arquivo futuro `codigo/test_rotas.py` reunirá testes unitários do grafo, da leitura e montagem do mapa, dos algoritmos e da integração com a interface. Cada integrante fornecerá testes da própria contribuição; o integrante 6 organizará a execução automatizada. O framework `pytest` é a ferramenta padrão definida.

Cenários de teste necessários:

- Grafo pequeno com caminho ótimo conhecido manualmente.
- Critérios de otimização (distância, tempo e custo financeiro) escolhendo caminhos diferentes conforme o perfil das vias (vias arteriais mais rápidas vs vias locais mais curtas).
- Mão única, direção invertida proibida e rotatórias.
- Origem igual ao destino (custo zero) e destino inalcançável (situação de erro tratada).
- Empates de custo e arestas paralelas identificadas.
- Validação de dados: JSON corrompido, referência a nó ausente e ponto de interesse sem associação viária válida.
- Pesos negativos ou não finitos e velocidade não positiva (devem disparar exceções).
- Integração ponta a ponta: leitura, construção do grafo e busca sem acionar a interface visual.

Cada aresta devolvida no caminho deverá existir, respeitar a direção de tráfego e somar exatamente o custo informado. Dijkstra e A* deverão concordar no custo ótimo com tolerância numérica de ponto flutuante, mesmo quando retornarem caminhos alternativos em empates.

## Avaliação de Desempenho (Benchmarks)

Manter a avaliação experimental separada dos testes unitários de correção. O tempo global de execução do `pytest` não será usado como métrica de busca dos algoritmos.

Protocolo planejado:

- Usar o snapshot fixo da malha viária do Coração Eucarístico e 100 pares origem–destino selecionados de forma determinística e reproduzível.
- Comparar Dijkstra vs A* com os mesmos pares, sob os 3 critérios (distância, tempo e custo).
- Executar aquecimento de cache e 20 repetições para cada consulta.
- Cronometrar unicamente o tempo de busca e reconstrução da rota (`time.perf_counter`), isolado de leitura de disco, renderização do mapa ou renderização no Streamlit.
- Métricas registradas: tamanho do grafo (|V| e |E|), custo total obtido, quantidade de nós expandidos/visitados, tempo mediano, desvio padrão e especificações do hardware de teste.
- Complementar com grafos sintéticos em malha (grid) de 100, 500 e 1.000 nós para avaliar o comportamento assintótico.

Quando a implementação estiver concluída, a bateria de benchmarks será acionada por um comando específico em `codigo/test_rotas.py` ou script auxiliar de medição.

As tabelas de medições e figuras geradas ficarão respectivamente em `artefatos/resultados/tabelas` e `artefatos/resultados/figuras`. Todas as figuras deverão indicar unidades, parâmetros do experimento e a versão correspondente do código.
