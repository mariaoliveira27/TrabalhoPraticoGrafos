# Clean Code e explicação do código

Clean Code será aplicado por meio de organização simples, responsabilidades claras e código compreensível. As regras abaixo orientam a implementação futura.

## Organização

- Começar pelos cinco arquivos definidos na arquitetura, diretamente em `codigo`.
- Manter as classes relacionadas ao grafo juntas em `grafo.py`.
- Usar funções pequenas para ler o mapa, validar os registros, montar o grafo e executar buscas.
- Criar classes ou arquivos adicionais apenas quando houver uma responsabilidade concreta que os justifique.
- Preservar a separação entre dados, cálculo e apresentação, mesmo sem camadas de pastas.

## Legibilidade

- Usar nomes descritivos em português, sem acentos nos identificadores.
- Indicar unidades, como `distancia_m` e `tempo_s`.
- Declarar tipos nas entradas, saídas e estruturas relevantes.
- Dar nomes às constantes e às hipóteses do modelo.
- Evitar repetição, estado global e dependências ocultas.
- Separar responsabilidades sem fragmentar o algoritmo em auxiliares que escondam seu raciocínio.
- Documentar objetivo, parâmetros, retorno e condições importantes.
- Comentar decisões, invariantes e trechos difíceis.
- Remover importações, variáveis e trechos sem uso.

## Validação

- Diferenciar arquivo inválido, solicitação inválida e destino inalcançável.
- Usar exceções específicas e mensagens compreensíveis.
- Manter o núcleo testável sem iniciar a interface ou acessar a internet.
- Manter a mesma definição de custos e nós expandidos nos dois algoritmos.
- Escrever testes pertinentes ao comportamento da própria contribuição.

## Preparação para explicar linha a linha

Todos percorrerão o fluxo completo. Cada autor e seu revisor deverão explicar as estruturas utilizadas, as entradas e saídas, as condições, o relaxamento das arestas, as operações da fila e a reconstrução do caminho.

As duplas serão 1 e 2, 3 e 4, 5 e 6. Os responsáveis pelos algoritmos também deverão justificar correção, complexidade e validade das heurísticas. Um ensaio coletivo usará trechos escolhidos pelos colegas.

Quando houver código, poderá ser produzido um material didático complementar com explicações dos blocos mais difíceis. O relatório não precisa transcrever todo o código.
