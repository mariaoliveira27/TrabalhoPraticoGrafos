# Dados do mapa

Esta pasta armazenará os arquivos de dados locais da aplicação. Nesta etapa inicial, ainda não há dados reais baixados.

## Arquivos futuros

| Arquivo | Conteúdo | Responsável |
| --- | --- | --- |
| `mapa.json` | Snapshot das vias do Coração Eucarístico (nós, vias, sentidos e limites de velocidade) obtido via OpenStreetMap / Overpass API | Integrante 1 |
| `pontos_interesse.json` | Catálogo de pelo menos 10 pontos de interesse (POIs) com ID, nome, coordenadas e nó viário navegável correspondente | Integrante 1 |

Os arquivos ficarão diretamente nesta pasta. O arquivo `mapa.json` será somente para leitura (preservado como fonte estática); o grafo será construído em memória durante a inicialização da aplicação.

## Especificação dos Dados e Hipóteses

- **Modo de transporte:** Exclusivamente automóveis particulares (carros).
- **Métricas:**
  - **Distância:** em metros ($m$).
  - **Tempo:** em segundos ($s$), estimado com base no comprimento da via e velocidade máxima permitida. Velocidades ausentes ou não informadas no OSM serão padronizadas em 30 km/h (hipótese documentada).
  - **Custo financeiro:** em Reais (R$), calculado a partir de consumo veicular médio de 10 km/l e preço de referência da gasolina a R$ 5,80/l:
    $$\text{custo\_reais} = \left(\frac{\text{distancia\_m}}{1000.0 \times 10.0}\right) \times 5.80$$
- **Pontos de Interesse (POIs):** Devem abranger locais de destaque no Coração Eucarístico (ex.: Campus PUC Minas - Prédios centrais, Praça do Coração Eucarístico, Estação de Metrô Gameleira, restaurantes, farmácias, agências bancárias e supermercados).

Ao realizar a extração, o Integrante 1 registrará neste documento a query Overpass executada, as coordenadas do Bounding Box, data/hora da coleta e a atribuição de licença do OpenStreetMap (ODbL).
