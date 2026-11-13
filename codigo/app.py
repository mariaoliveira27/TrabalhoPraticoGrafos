
import streamlit as st
import folium

from streamlit_folium import st_folium









st.set_page_config(
    page_title="Sistema de Rotas",
    page_icon="🗺️",
    layout="wide"
)


POIS = [
    {
        "nome": "PUC Minas",
        "coordenadas": [-19.9230, -43.9920]
    },
    {
        "nome": "Praça da Liberdade",
        "coordenadas": [-19.9320, -43.9370]
    },
    {
        "nome": "Mercado Central",
        "coordenadas": [-19.9250, -43.9410]
    },
    {
        "nome": "Parque Municipal",
        "coordenadas": [-19.9200, -43.9260]
    },
    {
        "nome": "Rodoviária de Belo Horizonte",
        "coordenadas": [-19.9167, -43.9400]
    }
]


def criar_mapa(pois, rota=None):
    mapa = folium.Map(
        location=[-19.9250, -43.9450],
        zoom_start=13,
        control_scale=True
    )

    for poi in pois:
        folium.Marker(
            location=poi["coordenadas"],
            popup=poi["nome"],
            tooltip=poi["nome"],
            icon=folium.Icon(
                color="blue",
                icon="map-marker"
            )
        ).add_to(mapa)

    if rota:
        folium.PolyLine(
            locations=rota["caminho"],
            color="red",
            weight=5,
            opacity=0.8,
            tooltip="Rota simulada"
        ).add_to(mapa)

        folium.Marker(
            location=rota["caminho"][0],
            popup="Origem",
            icon=folium.Icon(
                color="green",
                icon="play"
            )
        ).add_to(mapa)

        folium.Marker(
            location=rota["caminho"][-1],
            popup="Destino",
            icon=folium.Icon(
                color="red",
                icon="flag"
            )
        ).add_to(mapa)

        mapa.fit_bounds(rota["caminho"])

    return mapa


def calcular_rota_simulada(origem, destino, criterio):
    caminho = [
        origem["coordenadas"],
        destino["coordenadas"]
    ]

    return {
        "estado": "Simulação",
        "caminho": caminho,
        "nomes_caminho": [
            origem["nome"],
            destino["nome"]
        ],
        "distancia": 3.5,
        "tempo": 12,
        "custo": 2.50,
        "criterio": criterio
    }


def exibir_metricas(rota):
    coluna1, coluna2, coluna3 = st.columns(3)

    coluna1.metric(
        "Distância",
        f'{rota["distancia"]:.2f} km'
    )

    coluna2.metric(
        "Tempo estimado",
        f'{rota["tempo"]:.0f} min'
    )

    coluna3.metric(
        "Custo",
        f'R$ {rota["custo"]:.2f}'
    )

    st.warning(
        "Rota simulada. O algoritmo Dijkstra ainda não foi integrado."
    )


def main():
    st.title("st.image("caminho/para/seu_icone.png", width=40) Sistema de Rotas")

    st.write(
        "Selecione os pontos de origem e destino "
        "e escolha o critério para calcular a rota."
    )

    nomes_pois = [poi["nome"] for poi in POIS]

    coluna1, coluna2, coluna3 = st.columns(3)

    with coluna1:
        origem_nome = st.selectbox(
            "Ponto de origem",
            nomes_pois
        )

    with coluna2:
        destino_nome = st.selectbox(
            "Ponto de destino",
            nomes_pois,
            index=1
        )

    with coluna3:
        criterio = st.selectbox(
            "Critério de otimização",
            ["Distância", "Tempo", "Custo"]
        )

    botao_calcular = st.button(
        "Calcular rota",
        type="primary",
        use_container_width=True
    )

    if botao_calcular:
        if origem_nome == destino_nome:
            st.session_state.pop("rota", None)

            st.warning(
                "A origem e o destino devem ser diferentes."
            )

        else:
            origem = next(
                poi for poi in POIS
                if poi["nome"] == origem_nome
            )

            destino = next(
                poi for poi in POIS
                if poi["nome"] == destino_nome
            )

            rota = calcular_rota_simulada(
                origem,
                destino,
                criterio
            )

            st.session_state["rota"] = rota

    rota_atual = st.session_state.get("rota")

    mapa = criar_mapa(
        POIS,
        rota_atual
    )

    coluna_mapa, coluna_metricas = st.columns([2, 1])

    with coluna_mapa:
        st.subheader("Mapa")

        st_folium(
            mapa,
            width=None,
            height=550,
            key="mapa_rotas"
        )

    with coluna_metricas:
        st.subheader("Informações da rota")

        if rota_atual:
            exibir_metricas(rota_atual)

            st.write("**Caminho encontrado:**")

            st.write(
                " → ".join(rota_atual["nomes_caminho"])
            )

            st.write(
                f'**Critério:** {rota_atual["criterio"]}'
            )

        else:
            st.info(
                "Selecione a origem, o destino e o critério. "
                "Depois, clique em 'Calcular rota'."
            )


if __name__ == "__main__":
    main()

