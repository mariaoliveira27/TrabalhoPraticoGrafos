# Divisão entre os seis integrantes

A divisão abaixo registra responsabilidades originais e o estado atual do código implementado.

| Integrante | Responsabilidade atribuída | Documentação e revisão |
| --- | --- | --- |
| 1 | `mapa.py`, coleta, validação dos dados viários e 10 pontos de interesse em `codigo/dados` | Origem e preparação dos dados; revisa o integrante 2 |
| 2 | Classes e cálculos de `grafo.py`; modelagem dos pesos (distância, tempo, custo) e apoio às regras viárias | Modelagem, pesos e UML; revisa o integrante 1 |
| 3 | Implementação de Dijkstra e Bellman-Ford em `rotas.py` (critérios: distância, tempo e custo) | Correção e complexidade dos algoritmos; recebe revisão do integrante 4 |
| 4 | Apoio à especificação e revisão da implementação em `rotas.py` | Revisão dos casos de teste e da explicação dos algoritmos; revisa o integrante 3 |
| 5 | `app.py` com **Streamlit + Folium** (`streamlit-folium`), mapa interativo e apresentação das métricas | Telas, slides e organização da gravação; revisa o integrante 6 |
| 6 | Organização da suíte em `codigo/tests`, testes de borda, integração e benchmarks de desempenho empírico | Resultados, montagem do relatório e pacote final; revisa o integrante 5 |

## Como trabalhar nos arquivos compartilhados

Os integrantes 3 e 4 compartilham implementação e revisão dos dois algoritmos de busca. A interface permite selecionar Dijkstra ou Bellman-Ford. Combinar alterações antes de editar simultaneamente e revisar pelo Git.

Cada autor fornecerá testes da própria contribuição. O integrante 6 organizará esses casos em `codigo/tests` e coordenará os testes de integração. A medição de desempenho será planejada separadamente dos testes de correção.

## Responsabilidades de todos

- Fazer commits individuais e escrever a seção do relatório relacionada à própria contribuição.
- Definir juntos os parâmetros das buscas e os campos de `ResultadoRota`.
- Corrigir os problemas da própria área e participar da integração.
- Entender o fluxo completo, participar das revisões e ensaiar a explicação do código.
- Participar do vídeo (12 a 18 minutos) e da apresentação presencial (10 minutos).
- Conferir o pacote e realizar a própria submissão no Canvas.

## Sequência de implementação e validação

1. Modelo e resultados de busca implementados para distância, tempo e custo financeiro.
2. Ler um recorte viário do Coração Eucarístico e montar o grafo próprio.
3. Dijkstra e Bellman-Ford implementados; fluxo Streamlit + Folium integrado aos módulos.
4. POIs associados ao grafo; testes comparam os dois algoritmos nos três critérios.
5. Executar testes e medições de benchmark, registrando apenas resultados realmente produzidos.
6. Revisar código, relatório oficial SBC e demonstrações, ensaiando a explicação linha a linha.

O prazo deve ser confirmado no Canvas antes de fechar um cronograma datado.
