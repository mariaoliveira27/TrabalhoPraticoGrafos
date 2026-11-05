# Plano de issues para GitHub Projects

Este plano parte do estado atual: tema, arquitetura inicial e diagramas UML estão documentados; ainda não há implementação Python, dados locais, resultados experimentais, artigo ou apresentação final. Os títulos e descrições abaixo estão prontos para copiar para o GitHub. Os responsáveis permanecem como **Integrante 1–6** até que cada pessoa escolha sua atribuição.

## Configuração sugerida do Project

- Status: Backlog → Pronta → Em andamento → Em revisão → Concluída.
- Prioridade: P0 bloqueia o protótipo ou entrega; P1 necessário à entrega final; P2 melhoria pós-requisitos.
- Tamanho: P/M/G (estimativa relativa).
- Labels: `fase: planejamento`, `fase: dados`, `fase: implementação`, `fase: validação`, `fase: entrega`; `tipo: código`, `tipo: documentação`, `tipo: revisão`.
- Cada issue tem responsável e revisor. O revisor confirma os critérios de aceite antes de fechar.
- Cada pessoa registra commits próprios e escreve a seção do relatório ligada à sua contribuição.

Para publicar as 15 issues no repositório remoto, instale e autentique o GitHub CLI (`gh auth login`), depois use o script `criar_issues.ps1` na raiz do projeto. Sem parâmetros, ele mostra uma prévia; com `-Create`, cria as issues ainda não existentes com esses títulos. A associação ao GitHub Project pode ser feita depois no próprio Project.

## Distribuição equilibrada

| Papel | Frente principal | Revisão cruzada |
| --- | --- | --- |
| Integrante 1 | Dados viários, POIs e leitura do mapa | Revisa o modelo do Integrante 2 |
| Integrante 2 | Contratos, classes do grafo e UML | Revisa dados/importação do Integrante 1 |
| Integrante 3 | Dijkstra e reconstrução do caminho | Revisa os testes do Integrante 4 |
| Integrante 4 | Testes independentes e avaliação experimental | Revisa Dijkstra do Integrante 3 |
| Integrante 5 | Interface Streamlit + Folium e coordenação dos slides | Revisa a integração do Integrante 6 |
| Integrante 6 | Integração do aplicativo, montagem do artigo e checklist final | Revisa a interface do Integrante 5 |

Cada integrante redige sua parte do artigo. O Integrante 6 monta e padroniza o documento com revisão de todos. Todos participam da apresentação e do vídeo.

---

## Fase 0 — Fechar o planejamento

### Issue 01 — Confirmar requisitos, contratos e critérios de aceite

**Responsável:** Integrante 2 · **Revisor:** Integrante 1 · **Tamanho:** M · **Prioridade:** P0 · **Labels:** `fase: planejamento`, `tipo: documentação`

**Descrição:** Consolidar as decisões em `arquitetura.md`, `validacao.md` e nos diagramas antes de iniciar código. Confirmar entradas/saídas dos módulos, unidades, direção e acesso para carros, tratamento de casos de borda e hipóteses de velocidade/combustível. Registrar dúvidas que dependam do enunciado ou do professor.

**Critérios de aceite**
- [ ] Contratos de `grafo.py`, `mapa.py`, `rotas.py` e `app.py` estão escritos e compatíveis.
- [ ] Dijkstra é o único algoritmo previsto; pesos negativos são proibidos.
- [ ] Fórmulas, unidades e hipóteses dos três critérios estão documentadas.
- [ ] Escopo de dados, testes, benchmarks, artigo e apresentação foi revisado pelos seis.

### Issue 02 — Preparar o repositório e o fluxo de contribuição

**Responsável:** Integrante 6 · **Revisor:** Integrante 5 · **Tamanho:** P · **Prioridade:** P0 · **Labels:** `fase: planejamento`, `tipo: documentação`

**Descrição:** Preparar convenções de issues, branches, revisões e commits individuais; deixar instruções de instalação e execução planejadas para o README.

**Critérios de aceite**
- [ ] Cada integrante escolheu e confirmou seu papel Integrante 1–6.
- [ ] Convenção de branches/commits e revisão cruzada foi acordada.
- [ ] Issues têm responsável, revisor, prioridade, tamanho e dependências.
- [ ] Comandos de instalação, testes e execução estão definidos para documentação.

---

## Fase 1 — Dados e modelo

### Issue 03 — Coletar e documentar a malha viária e os pontos de interesse

**Responsável:** Integrante 1 · **Revisor:** Integrante 2 · **Tamanho:** G · **Prioridade:** P0 · **Labels:** `fase: dados`, `tipo: código`

**Descrição:** Obter um recorte reproduzível da malha viária do Coração Eucarístico e preparar dados locais de ruas e dez POIs. Documentar fonte, data, cobertura, licença/atribuição e limitações. A aplicação não deverá depender de acesso à rede para carregar os dados.

**Critérios de aceite**
- [ ] Snapshot viário e cadastro de dez POIs estão em `codigo/dados` em formato acordado.
- [ ] Cada POI tem identificador, nome, coordenadas e associação válida a nó viário.
- [ ] Mão única e filtros básicos de acesso para carros são preservados quando disponíveis.
- [ ] Fonte, data, área coberta, licença e limitações estão documentadas.
- [ ] Arquivos foram verificados quanto a coordenadas inválidas e referências ausentes.

### Issue 04 — Implementar o modelo do grafo e os pesos

**Responsável:** Integrante 2 · **Revisor:** Integrante 1 · **Tamanho:** G · **Prioridade:** P0 · **Labels:** `fase: implementação`, `tipo: código`

**Descrição:** Implementar em `codigo/grafo.py` as classes `Vertice`, `Aresta`, `Grafo` e `ResultadoRota`, listas de adjacência próprias e pesos para distância, tempo e custo.

**Critérios de aceite**
- [ ] Modelo corresponde ao contrato aprovado e ao diagrama de classes.
- [ ] Grafo dirigido suporta sentidos de circulação e arestas paralelas identificáveis.
- [ ] Pesos retornam distância (m), tempo (s) ou custo estimado (R$), com conversões documentadas.
- [ ] Dados inválidos, pesos negativos/não finitos e velocidades inválidas são tratados pelo contrato.
- [ ] Operações públicas têm docstrings e exemplo pequeno de uso.

### Issue 05 — Implementar leitura e validação dos dados do mapa

**Responsável:** Integrante 1 · **Revisor:** Integrante 2 · **Tamanho:** G · **Prioridade:** P0 · **Labels:** `fase: implementação`, `tipo: código`

**Descrição:** Implementar em `codigo/mapa.py` o carregamento dos arquivos locais, validação e conversão para `Grafo`, separando leitura, validação e montagem.

**Critérios de aceite**
- [ ] Carregamento funciona com os arquivos locais documentados.
- [ ] JSON inválido, referências a nós ausentes e POIs sem associação geram mensagens úteis.
- [ ] Direção das vias, nós compartilhados e filtros de acesso acordados são preservados.
- [ ] Execução normal não consulta a internet.
- [ ] Exemplo documenta como montar o grafo a partir dos dados do projeto.

### Issue 06 — Atualizar diagramas e arquitetura após fechar os contratos

**Responsável:** Integrante 2 · **Revisor:** Integrante 6 · **Tamanho:** P · **Prioridade:** P1 · **Labels:** `fase: planejamento`, `tipo: documentação`

**Descrição:** Conferir fontes PlantUML, imagens exportadas e documentação para refletirem os contratos aprovados e o fluxo implementado.

**Critérios de aceite**
- [ ] Diagramas de classe e sequência correspondem às assinaturas, campos e fluxo reais.
- [ ] Fontes PlantUML e imagens atualizadas estão versionadas.
- [ ] Material mantém Dijkstra como algoritmo único e não oferece seletor de algoritmo.
- [ ] README e arquitetura apontam para arquivos e comandos atuais.

---

## Fase 2 — Algoritmo e protótipo

### Issue 07 — Implementar Dijkstra e reconstrução de rotas

**Responsável:** Integrante 3 · **Revisor:** Integrante 4 · **Tamanho:** G · **Prioridade:** P0 · **Labels:** `fase: implementação`, `tipo: código`

**Descrição:** Implementar em `codigo/rotas.py` Dijkstra usando fila de prioridade, relaxamento, predecessores e reconstrução do caminho, aceitando os três critérios.

**Critérios de aceite**
- [ ] Busca retorna caminho mínimo para cada critério com pesos não negativos.
- [ ] Caminho respeita direção e arestas reais; custos consolidados conferem.
- [ ] Origem=destino retorna custo zero; destino inalcançável tem estado próprio.
- [ ] Solicitação/critério inválido é diferenciado de falta de caminho.
- [ ] Resultado tem os campos acordados, incluindo nós processados.
- [ ] Nenhuma biblioteca externa é usada para executar a busca.

### Issue 08 — Criar testes do modelo, dados e Dijkstra

**Responsável:** Integrante 4 · **Revisor:** Integrante 3 · **Tamanho:** G · **Prioridade:** P0 · **Labels:** `fase: validação`, `tipo: código`

**Descrição:** Criar em `codigo/test_rotas.py` testes independentes para modelo, importação e busca, com grafos pequenos e respostas ótimas conhecidas.

**Critérios de aceite**
- [ ] Testes cobrem os três critérios, inclusive rotas diferentes para critérios diferentes.
- [ ] Casos cobrem mão única, arestas paralelas, empates, origem=destino e destino inalcançável.
- [ ] Casos cobrem arquivos/referências/pesos inválidos.
- [ ] Soma dos pesos das arestas retornadas confere com o custo informado.
- [ ] Testes executam por comando documentado sem interface ou rede.

### Issue 09 — Criar interface com Streamlit e Folium

**Responsável:** Integrante 5 · **Revisor:** Integrante 6 · **Tamanho:** G · **Prioridade:** P0 · **Labels:** `fase: implementação`, `tipo: código`

**Descrição:** Implementar `codigo/app.py` para exibir o mapa, selecionar origem, destino e critério, solicitar rota e mostrar traçado e métricas.

**Critérios de aceite**
- [ ] App inicia pelo comando documentado e carrega dados pelo módulo `mapa.py`.
- [ ] Usuário seleciona POIs e um dos três critérios; a busca usa Dijkstra.
- [ ] Rota aparece no mapa e painel mostra distância, tempo, custo e estado.
- [ ] Entrada inválida e destino inalcançável têm mensagens compreensíveis.
- [ ] Interface não duplica lógica de grafo ou algoritmo.

### Issue 10 — Integrar os módulos e demonstrar o fluxo ponta a ponta

**Responsável:** Integrante 6 · **Revisor:** Integrante 5 · **Tamanho:** M · **Prioridade:** P0 · **Labels:** `fase: validação`, `tipo: revisão`

**Descrição:** Integrar modelo, dados, Dijkstra e interface, resolver incompatibilidades e preparar demonstração reproduzível.

**Critérios de aceite**
- [ ] Fluxo de dados locais → seleção → busca → mapa funciona.
- [ ] Os três critérios foram demonstrados em consultas válidas.
- [ ] Casos sem caminho e entrada inválida foram demonstrados quando aplicáveis.
- [ ] README descreve instalação, execução e estrutura atual.
- [ ] Revisores dos módulos confirmam preservação dos contratos.

---

## Fase 3 — Validação e resultados

### Issue 11 — Executar integração e corrigir falhas

**Responsável:** Integrante 4 · **Revisor:** Integrante 6 · **Tamanho:** M · **Prioridade:** P0 · **Labels:** `fase: validação`, `tipo: revisão`

**Descrição:** Rodar a suíte completa no ambiente documentado, completar casos ponta a ponta e acompanhar correções até o fluxo estar estável.

**Critérios de aceite**
- [ ] Testes unitários e de integração terminam com sucesso.
- [ ] Leitura, montagem e busca são testadas sem renderizar a interface.
- [ ] Falhas encontradas foram corrigidas com commits/issues rastreáveis.
- [ ] Comando, versão do código e resultado da execução foram registrados.

### Issue 12 — Executar benchmarks e documentar resultados

**Responsável:** Integrante 4 · **Apoio:** Integrante 6 · **Revisor:** Integrante 3 · **Tamanho:** G · **Prioridade:** P1 · **Labels:** `fase: validação`, `tipo: código`

**Descrição:** Executar protocolo reproduzível no snapshot viário e em grafos sintéticos, para os três critérios, com aquecimento e repetições. Cronometrar somente busca e reconstrução; respeitar as comparações permitidas pelo enunciado.

**Critérios de aceite**
- [ ] Consultas e grafos sintéticos são determinísticos e documentados.
- [ ] Resultados incluem tamanho do grafo, custo, nós expandidos, mediana, dispersão e hardware.
- [ ] Tabelas e figuras estão nas pastas planejadas de `artefatos/resultados`.
- [ ] Unidades, parâmetros e versão do código aparecem nas figuras/tabelas.
- [ ] Análise usa somente medições reais e descreve limitações.

---

## Fase 4 — Relatório e apresentação

### Issue 13 — Redigir e compilar artigo no template SBC

**Montagem:** Integrante 6 · **Revisão:** todos · **Tamanho:** G · **Prioridade:** P1 · **Labels:** `fase: entrega`, `tipo: documentação`

**Descrição:** Produzir o artigo em LaTeX no template SBC. Cada integrante escreve a seção da própria contribuição; Integrante 6 integra e padroniza.

**Critérios de aceite**
- [ ] Artigo aborda problema, dados, modelagem/UML, Dijkstra, correção, complexidade, testes, resultados e limitações.
- [ ] Resultados e telas correspondem à versão final do projeto.
- [ ] Referências, fonte dos dados e contribuições individuais estão registradas.
- [ ] PDF compila no template SBC, tem 12–15 páginas conforme plano atual e foi revisado por todos.
- [ ] Fontes, bibliografia, figuras e PDF estão versionados em `Relatorio`.

### Issue 14 — Preparar slides, demonstração e vídeo

**Coordenação:** Integrante 5 · **Participantes:** todos · **Revisor:** Integrante 6 · **Tamanho:** G · **Prioridade:** P1 · **Labels:** `fase: entrega`, `tipo: documentação`

**Descrição:** Preparar apresentação presencial de 10 minutos e vídeo de 12–18 minutos segundo o plano atual. Distribuir fala e demonstração entre os seis.

**Critérios de aceite**
- [ ] Slides cobrem problema, grafo, Dijkstra, interface, validação, resultados e limitações.
- [ ] Demonstração ensaiada usa a versão final e tem plano alternativo.
- [ ] Todos os integrantes têm fala e participação definidas.
- [ ] Vídeo está dentro da duração e explica funcionalidades/contribuições individuais.
- [ ] Materiais finais e roteiro ficam em `artefatos/apresentacao`.

---

## Fase 5 — Revisão e entrega

### Issue 15 — Revisar repositório e fechar o pacote de entrega

**Responsável:** Integrante 6 · **Apoio:** todos · **Tamanho:** M · **Prioridade:** P0 · **Labels:** `fase: entrega`, `tipo: revisão`

**Descrição:** Conferir código, dados e atribuições, documentação, resultados, artigo e apresentação; conferir histórico de commits e canal de submissão da disciplina.

**Critérios de aceite**
- [ ] README informa instalação, execução, testes e estrutura final.
- [ ] Testes finais foram executados e o aplicativo foi iniciado/demonstrado.
- [ ] Artigo, slides e vídeo correspondem ao código e aos resultados entregues.
- [ ] Contribuições dos seis são rastreáveis e confirmadas.
- [ ] Equipe confirmou prazo, formato e canal de submissão no Canvas.
- [ ] Pacote foi revisado por todos antes da submissão.

## Dependências sugeridas

```text
01 → 03, 04, 07, 08, 09
02 → issues de implementação
03 → 05 → 10
04 → 05, 07
07 → 08 → 11
09 → 10 → 11
11 → 12 → 13
10 e 12 → 14
13 e 14 → 15
```

Documentação e preparação podem avançar em paralelo quando contratos e resultados estiverem disponíveis. Ajustar prioridade e sequência se o enunciado completo ou o calendário oficial pedir outra ordem.

