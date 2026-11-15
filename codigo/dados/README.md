# Dados do Mapa e Pontos de Interesse (POIs)

Esta pasta armazena os arquivos de dados locais e snapshots utilizados pela aplicação para execução determinística e offline.

## Arquivos de Dados

| Arquivo | Descrição | Formato | Status |
| :--- | :--- | :--- | :--- |
| `mapa.json` | Snapshot das vias e cruzamentos (nós, vias, sentidos de mão única e limites de velocidade) | JSON | Concluído |
| `pontos_interesse.json` | Catálogo de pontos de interesse (POIs) estratégicos com ID, nome, coordenadas, endereço e associação ao nó viário | JSON | Concluído (12+ locais) |

---

## Proveniência dos Dados, Licença e Metadados

- **Fonte:** OpenStreetMap (OSM) via Overpass API / Nominatim.
- **Licença:** *Open Database License (ODbL)* © Colaboradores do OpenStreetMap.
- **Data da Extração:** Novembro de 2026.
- **Área de Cobertura (Bounding Box):**
  - **Belo Horizonte Amplo:** Latitude `[-20.0600, -19.7500]`, Longitude `[-44.1000, -43.8500]`.
  - **Coração Eucarístico (Snapshot Viário):** Latitude `[-19.9320, -19.9180]`, Longitude `[-43.9960, -43.9750]`.

---

## Especificação dos Dados e Hipóteses de Modelagem

- **Modo de transporte:** Exclusivamente automóveis particulares (carros).
- **Métricas:**
  - **Distância:** em metros ($m$), calculada com a fórmula geodésica de Haversine ($R = 6.371.000\,m$).
  - **Tempo:** em segundos ($s$), estimado com base no comprimento da via e velocidade máxima permitida ($\text{tempo} = \text{distancia} / (\text{velocidade} / 3.6)$). Vias sem velocidade informada assumem a velocidade padrão de **30 km/h**.
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
