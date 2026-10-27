# Dados do mapa

Esta pasta está vazia de dados reais. Não foram criados mapas ou cadastros de exemplo.

## Arquivos futuros

| Arquivo | Conteúdo |
| --- | --- |
| `mapa.json` | Snapshot original obtido do OpenStreetMap/Overpass |
| `pontos_interesse.json` | Dez pontos reais com identificador, nome, coordenadas e nó viário associado |

Os arquivos ficarão diretamente aqui, sem subpastas de originais, processados ou pontos de interesse. O mapa original deverá ser preservado, sem sobrescrita durante a execução; o grafo será montado em memória.

Ao realizar a coleta, atualizar este documento com a origem, a consulta, a data, os limites do recorte, o hash e a atribuição/licença. Conferir os acessos dos pontos de interesse aos nós viários.

O modelo será para carros, com distância em metros e tempo em segundos. Velocidades ausentes ou inválidas serão assumidas como 30 km/h e identificadas como hipótese. O tempo será apresentado como estimado sem trânsito.

**Responsável:** integrante 1, com apoio do integrante 2 nas regras viárias e nos pesos.
