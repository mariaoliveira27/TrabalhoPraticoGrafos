# Validação e avaliação de desempenho

Este documento reúne as orientações antes separadas nas pastas de testes e experimentos. Nenhum teste ou experimento foi executado nesta etapa.

## Testes de correção

O arquivo futuro `codigo/test_rotas.py` reunirá testes do grafo, da leitura e montagem do mapa, dos algoritmos e da integração. Cada integrante fornecerá testes da própria contribuição; o integrante 6 organizará a execução. `pytest` permanece como ferramenta prevista.

Cenários necessários:

- Grafo pequeno com ótimo conhecido manualmente.
- Critérios distância e tempo escolhendo caminhos diferentes.
- Mão única, direção invertida e rotatória.
- Origem igual ao destino e destino inalcançável.
- Empates e arestas paralelas.
- JSON inválido, referência a nó ausente e ponto de interesse sem associação válida.
- Pesos negativos ou não finitos e velocidade não positiva.
- Integração entre leitura, construção e busca sem iniciar a interface.

Cada aresta devolvida deverá existir, respeitar a direção e somar o custo informado. Dijkstra e A* deverão concordar no custo ótimo com tolerância numérica, mesmo quando retornarem caminhos diferentes em empates.

## Desempenho

Manter a avaliação separada dos testes de correção. A duração total do pytest não será usada como tempo de busca.

Protocolo planejado:

- Usar o mesmo snapshot e 100 pares origem–destino selecionados de forma reproduzível.
- Comparar os dois algoritmos com os mesmos pares, critérios e pesos.
- Fazer um aquecimento e 20 repetições por consulta.
- Cronometrar somente a busca e a reconstrução, fora da leitura, da rede e da interface.
- Registrar tamanho do grafo, custo, nós expandidos, mediana, dispersão e configuração da máquina.
- Complementar com malhas sintéticas de 100, 500 e 1.000 vértices, com coordenadas e pesos consistentes.

Quando houver implementação, a avaliação poderá ser executada por uma função própria de avaliação em `test_rotas.py`, acionada explicitamente e separada dos casos descobertos pelo pytest. Essa função ficará fora do fluxo normal do aplicativo e não criará uma nova camada de diretórios.

As medições e figuras efetivamente produzidas ficarão em `artefatos/resultados/tabelas` e `artefatos/resultados/figuras`. Registrar os dados, parâmetros e versão do projeto utilizados. Não pressupor vantagem de A* ou diferença entre os critérios.
