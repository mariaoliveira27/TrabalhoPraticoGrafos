# Divisão entre os seis integrantes

A organização foi simplificada para cinco arquivos futuros. Nesta etapa existem somente pastas e documentação.

| Integrante | Responsabilidade futura | Documentação e revisão |
| --- | --- | --- |
| 1 | `mapa.py`, coleta, validação dos dados e pontos de interesse em `codigo/dados` | Origem e preparação dos dados; revisa o integrante 2 |
| 2 | Classes e cálculos de `grafo.py`; apoio às regras viárias da montagem em `mapa.py` | Modelagem, pesos e UML; revisa o integrante 1 |
| 3 | Função Dijkstra e reconstrução do caminho em `rotas.py` | Correção, complexidade e testes de Dijkstra; revisa o integrante 4 |
| 4 | Função A* e suas heurísticas em `rotas.py` | Correção, complexidade e testes de A*; revisa o integrante 3 |
| 5 | `app.py`, controles, mapa e apresentação das métricas | Telas, slides e organização da gravação; revisa o integrante 6 |
| 6 | Organização de `test_rotas.py`, integração e avaliação de desempenho | Resultados, montagem do relatório e pacote final; revisa o integrante 5 |

## Como trabalhar nos arquivos compartilhados

Os integrantes 3 e 4 serão responsáveis por funções diferentes de `rotas.py`. Integrar primeiro Dijkstra e seu contrato de resultado; depois acrescentar A*. Combinar os trechos antes de editar simultaneamente e revisar as alterações pelo Git.

Cada autor fornecerá testes da própria contribuição. O integrante 6 organizará esses casos em `test_rotas.py` e coordenará os testes de integração. A medição de desempenho será planejada separadamente dos testes de correção.

## Responsabilidades de todos

- Fazer commits individuais e escrever a seção do relatório relacionada à própria contribuição.
- Definir juntos os parâmetros das buscas e os campos de `ResultadoRota`.
- Corrigir os problemas da própria área e participar da integração.
- Entender o fluxo completo, participar das revisões e ensaiar a explicação do código.
- Participar do vídeo e da apresentação presencial.
- Conferir o pacote e realizar a própria submissão no Canvas.

## Ordem de implementação futura

1. Definir o modelo e o resultado das buscas.
2. Ler um mapa pequeno e montar o grafo próprio.
3. Implementar Dijkstra e ligar o fluxo à primeira tela.
4. Acrescentar A*, pontos reais e comparação dos critérios.
5. Executar testes e medições, registrando apenas resultados realmente produzidos.
6. Revisar código, relatório e demonstrações e ensaiar a explicação linha a linha.

O prazo deve ser confirmado no Canvas antes de fechar um cronograma datado.
