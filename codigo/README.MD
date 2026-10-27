# Codigo

## Estrutura simples

A implementação futura ficará diretamente nesta pasta, com apenas `dados` como subpasta. Nesta etapa há somente organização e documentação: nenhum arquivo Python foi criado.

| Arquivo futuro, ainda não criado | Responsabilidade | Responsável |
| --- | --- | --- |
| `grafo.py` | Classes `Vertice`, `Aresta`, `Grafo` e `ResultadoRota`; cálculos geográficos simples | Integrante 2 |
| `mapa.py` | Funções para ler, validar e converter o mapa em um grafo próprio | Integrante 1, com apoio do 2 nas regras viárias |
| `rotas.py` | Funções Dijkstra e A*, heurísticas e reconstrução do caminho | Integrantes 3 e 4 |
| `app.py` | Controles da interface, chamada das funções e apresentação do mapa e das métricas | Integrante 5 |
| `test_rotas.py` | Testes do grafo, da importação, dos algoritmos e da integração | Integrante 6, com testes fornecidos por todos |
| `dados` | Mapa original, pontos de interesse e informação da origem dos dados | Integrante 1 |

Os cinco arquivos são o ponto de partida, sem obrigação de criar um arquivo para cada classe. Novos arquivos só serão acrescentados se houver uma necessidade concreta.

## Fluxo da ferramenta

A interface chama as funções de leitura do mapa. Essas funções montam o grafo próprio. Depois, a interface chama Dijkstra ou A* e apresenta o resultado. As buscas não leem arquivos nem desenham mapas.

Não haverá camadas separadas de serviço, importador ou construtor. Leitura, validação e montagem continuarão separadas em funções pequenas dentro de `mapa.py`. Os algoritmos serão funções em `rotas.py`, sem classes que apenas envolvam sua execução.

## Clean Code

- Nomes descritivos, tipos e unidades explícitas.
- Funções com uma responsabilidade, sem duplicar regras.
- Comentários explicando decisões e os trechos difíceis.
- Grafo e algoritmos implementados pelo grupo.
- Todos devem conseguir explicar o fluxo completo e os algoritmos.

## Documentação de apoio

- [Arquitetura simples e classes](../artefatos/planejamento/arquitetura.md).
- [Clean Code](../artefatos/planejamento/clean_code.md).
- [Divisão entre os seis integrantes](../artefatos/planejamento/equipe.md).
- [Testes e avaliação de desempenho](../artefatos/planejamento/validacao.md).
- [Dados](dados/README.md).

As orientações de testes e experimentos ficam em `artefatos`, sem pastas adicionais em `codigo`. Ainda não há comandos de instalação ou execução.
