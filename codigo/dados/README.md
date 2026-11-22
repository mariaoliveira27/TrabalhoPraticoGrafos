# Dados do Mapa e Pontos de Interesse (POIs)

Esta pasta armazena os arquivos de dados locais e snapshots utilizados pela aplicação para execução determinística e offline.

## Arquivos de Dados

| Arquivo | Descrição | Formato | Status |
| :--- | :--- | :--- | :--- |
| `mapa.json` | Snapshot das vias e cruzamentos (nós, vias, sentidos de mão única e limites de velocidade), gerado por `gerar_mapa.py` | JSON | Concluído |
| `gerar_mapa.py` | Script que consulta o OpenStreetMap (Overpass API) e regera o `mapa.json` | Python | Concluído |
| `pontos_interesse.json` | Catálogo de pontos de interesse (POIs) estratégicos com ID, nome, coordenadas, endereço e associação ao nó viário | JSON | Concluído (12+ locais) |

---

## Proveniência dos Dados, Licença e Metadados

- **Fonte:** OpenStreetMap (OSM). O grafo viário vem da Overpass API, pelo script `gerar_mapa.py`; a busca e o cadastro de locais na interface usam o Nominatim.
- **Licença:** *Open Database License (ODbL)* © Colaboradores do OpenStreetMap.
- **Data da Extração:** base do OSM de 22/11/2026 (campo `data_extracao` dos metadados do `mapa.json`).
- **Área de Cobertura (Bounding Box):**
  - **Belo Horizonte Amplo:** Latitude `[-20.0600, -19.7500]`, Longitude `[-44.1000, -43.8500]`.
  - **Coração Eucarístico e arredores (vértices do snapshot viário):** Latitude `[-19.9273, -19.9188]`, Longitude `[-43.9960, -43.9877]`.

## Como o `mapa.json` é gerado

Na raiz do repositório, com internet: `python codigo/dados/gerar_mapa.py`.

- **Ruas e região:** `RUAS_DO_RECORTE` lista as ruas e `REGIAO` os retângulos que delimitam o recorte; o que fica fora deles é descartado. São duas partes:
  - a grade a sudeste do campus: Av. Dom José Gaspar, R. Dom Lúcio Antunes e R. Dom Joaquim Silvério, cruzadas por R. Padre João Crisóstomo, R. Padre Rossini Cândido, R. Padre Pedro Evangelista, R. Coração Eucarístico de Jesus, R. Padre Demerval Gomes e R. Dom Aristides Porto;
  - o lado oeste do campus até a Av. Itaú (Underground Black Pub): Av. Edgar da Mata Machado, cuja pista que sobe se chama Avenida 31 de Março no OSM, e as ruas entre ela e o campus (Padre Júlio Lombaerde, Madre Mazzarello, Madre Beatriz Frambach, Ivan Moraes de Andrade, Osvaldo Gattoni, São Pedro Julião e Edna Maria da Paixão).
- **Vértices (34):** cada cruzamento dessas ruas, inclusive as esquinas em que uma rua vira outra. Nós do OSM a até 25 m viram um vértice só, como as duas pistas de uma avenida no mesmo cruzamento e os nós de uma rotatória (Praça Cardeal Dom Serafim e a rotatória do início da Av. Itaú). Há também vértices fixos:
  - a portaria de carros da PUC Minas e um ponto da via interna do campus. Sem esse ponto, a PUC ficaria fora da área do mapa: a Av. Dom José Gaspar passa a 209 m das coordenadas do campus no catálogo, acima do limite de associação de 200 m;
  - dois pontos de quebra em curvas (Av. Edgar da Mata Machado junto ao campus e R. Padre Júlio Lombaerde), para a reta entre vértices acompanhar a rua.
  
  Cada vértice guarda em `osm_nos` os nós do OSM que o formam.
- **Arestas (50 registros, 68 direcionadas):** os trechos de rua entre vértices vizinhos, seguindo a rua de um cruzamento até o próximo. O sentido vem das tags `oneway` e `junction` do OSM; quando as duas pistas de uma avenida ligam os mesmos vértices, a aresta fica de mão dupla. O script avisa quando um trecho se afasta mais de 20 m da reta entre seus vértices, sinal de que falta um ponto de quebra. Cada aresta guarda em `osm_vias` as vias do OSM usadas. Todos os pares de vértices têm caminho (o grafo é fortemente conexo).
- **Velocidade:** `maxspeed` do OSM quando existe; senão, o limite do CTB (art. 61) para a classe da via: 30 km/h em vias locais (`residential`), 40 km/h em coletoras (`tertiary`), 60 km/h em arteriais e 80 km/h em vias de trânsito rápido. A via interna do campus usa 20 km/h. Nenhum trecho do recorte atual tem `maxspeed` no OSM.

---

## Especificação dos Dados e Hipóteses de Modelagem

- **Modo de transporte:** Exclusivamente automóveis particulares (carros).
- **Métricas:**
  - **Distância:** em metros ($m$), calculada com a fórmula geodésica de Haversine ($R = 6.371.000\,m$).
  - **Tempo:** em segundos ($s$), estimado com base no comprimento da via e velocidade máxima permitida ($\text{tempo} = \text{distancia} / (\text{velocidade} / 3.6)$). Cada trecho do `mapa.json` traz `velocidade_kmh` (ver acima); se o campo faltar, `mapa.py` assume **30 km/h**.
  - **Custo financeiro:** em Reais (R$), considerando consumo veicular médio de **10 km/l** e gasolina a **R$ 5,80/l**:
    $$\text{custo\_reais} = \left(\frac{\text{distancia\_m}}{1000.0 \times 10.0}\right) \times 5.80$$
- **Pontos de Interesse (POIs):** Inclui locais emblemáticos de Belo Horizonte (Campus PUC Minas Coração Eucarístico, Estádio Mineirão, Igreja da Pampulha, Mercado Central, Praça da Liberdade, Praça do Papa, etc.), com suporte a inclusão dinâmica de novos endereços e POIs via API com cache local.

---

## Estrutura do Arquivo `pontos_interesse.json`

```json
[
  {
    "id": "puc_minas_coreu",
    "nome": "PUC Minas - Coração Eucarístico",
    "categoria": "educacao",
    "coordenadas": [-19.9229, -43.9926],
    "endereco": "Rua Dom José Gaspar, 500 - Coração Eucarístico",
    "no_viario_associado": "no_puc_coreu"
  }
]
```
