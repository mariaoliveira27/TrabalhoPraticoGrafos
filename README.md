# Trabalho Prático Grafos

Otimização de rotas urbanas com base em mapas: o sistema deve receber mapas com pontos de interesse e calcular rotas otimizadas com base em tempo, distância ou custo.

## Objetivo

Desenvolver uma ferramenta computacional para resolver um problema aplicado por meio da modelagem, implementação e análise de grafos. O projeto deverá contemplar a definição da estrutura do grafo, a implementação de algoritmos compatíveis com o problema escolhido, a construção de uma interface de interação com a ferramenta e a avaliação dos resultados obtidos. Os alunos deverão demonstrar a correção da solução, analisar sua complexidade e discutir suas limitações no contexto da aplicação.

## Etapas

### Etapa 1 – Modelagem e Planejamento da Solução
Escolha do tema, definição do problema, levantamento de dados e modelagem do grafo. A utilização de diagramas UML será avaliada na modelagem.
* **Entregável:** Documento com a descrição do problema, justificativa da modelagem e plano de desenvolvimento.

### Etapa 2 – Desenvolvimento da Ferramenta
Implementação da estrutura de grafos, aplicação dos algoritmos e construção de uma interface mínima de uso. Procure em sites como o Kaggle bases de dados para a execução do seu sistema e testes. Apresente uma interface gráfica com os resultados (sem limitação de framework para frontend).
* **Entregável:** Protótipo funcional com código versionado no Git.

### Etapa 3 – Apresentação e Relatório Final
Contextualização, modelagem, análise dos resultados obtidos, avaliação do desempenho, conclusões e apresentação da solução.
* **Entregáveis:** 
  * Relatório técnico em LaTeX usando o template oficial da SBC (obrigatório, disponível em: [Overleaf SBC Template](https://www.overleaf.com/latex/templates/sbc-conferences-template/blbxwjwzdngr)).
  * Apresentação oral com demonstração da ferramenta.
  * Repositório Git contendo o histórico de desenvolvimento (commits individuais serão avaliados).

---

## Requisitos de Apresentação (Vídeo e Presencial)
* Demonstrar os resultados.
* Todos os membros do grupo devem participar.
* Slides para a apresentação.
* **Duração da apresentação presencial:** 10 minutos.
* **Duração do vídeo:** Entre 12 e 18 minutos com foco apenas no funcionamento e na explicação das *features* produzidas por cada aluno do grupo.

## Organização simples do projeto

Projeto em Python para rotas de carro no Coração Eucarístico, desenvolvido por seis integrantes. A implementação atual inclui modelo de grafo, carregamento do mapa e dos POIs, Dijkstra e Bellman-Ford, testes automatizados e interface Streamlit/Folium. Os dados locais são carregados sem depender da rede. Não há resultados experimentais de desempenho publicados ainda.

```text
TrabalhoPraticoGrafos/
├── codigo/
│   ├── app.py, grafo.py, mapa.py, rotas.py
│   ├── tests/
│   └── dados/
├── artefatos/
│   ├── planejamento/
│   ├── diagramas/
│   ├── apresentacao/
│   └── resultados/
└── Relatorio/
```

O código fica diretamente em `codigo`: `grafo.py`, `mapa.py`, `rotas.py`, `app.py` (interface **Streamlit + Folium**) e os testes em `codigo/tests`. O modelo inclui quatro classes centrais (`Vertice`, `Aresta`, `Grafo` e `ResultadoRota`), com suporte a otimização por **tempo**, **distância** ou **custo financeiro**. A interface permite escolher Dijkstra ou Bellman-Ford para buscar caminhos por distância, tempo ou custo. Os pesos do snapshot atual são não negativos; Dijkstra é apropriado para esses dados, enquanto Bellman-Ford também é implementado e comparado nos testes.

- [Organização do código](codigo/README.MD).
- [Arquitetura e responsabilidades](artefatos/planejamento/arquitetura.md).
- [Clean Code e explicação do código](artefatos/planejamento/clean_code.md).
- [Divisão entre os seis integrantes](artefatos/planejamento/equipe.md).
- [Issues planejadas para GitHub Projects](artefatos/planejamento/issues_github.md).
- [Testes e desempenho](artefatos/planejamento/validacao.md).
- [Artefatos](artefatos/README.MD).
- [Relatório](Relatorio/README.MD).

## Executar

Instale as dependências de `requirements.txt`. Para iniciar a interface: `streamlit run codigo/app.py`. Para rodar todos os testes: `python -m pytest codigo -v`. Só os testes de modelo, importação e busca (sem interface e sem rede): `python -m pytest codigo/test_rotas.py -v`.
