
import os
import streamlit as st
import folium
from streamlit_folium import st_folium

from mapa import (
    carregar_pois,
    carregar_mapa,
    construir_grafo,
    associar_poi_ao_no_mais_proximo,
    salvar_poi_cache,
    remover_poi_cache,
    buscar_poi_api,
    geocodificar_endereco,
    BBOX_BH
)
from rotas import calcularRotaDijkstra, calcularRotaBellmanFord

CAMINHO_POIS = os.path.join(os.path.dirname(__file__), "dados", "pontos_interesse.json")
CAMINHO_MAPA = os.path.join(os.path.dirname(__file__), "dados", "mapa.json")

st.set_page_config(
    page_title="Sistema de Rotas - Belo Horizonte",
    page_icon="🗺️",
    layout="wide"
)


def obter_pois():
    """Recupera a lista de POIs do arquivo local ou do session_state."""
    if "pois" not in st.session_state:
        if os.path.exists(CAMINHO_POIS):
            st.session_state["pois"] = carregar_pois(CAMINHO_POIS)
        else:
            st.session_state["pois"] = []
    return st.session_state["pois"]


@st.cache_resource
def obter_grafo():
    """Carrega o snapshot local e constrói o grafo uma vez por sessão do app."""
    dados_mapa = carregar_mapa(CAMINHO_MAPA)
    return construir_grafo(dados_mapa)


def criar_mapa(pois, rota=None):
    # Centro panorâmico de Belo Horizonte para visualização ampla dos pontos turísticos
    mapa = folium.Map(
        location=[-19.9190, -43.9550],
        zoom_start=12,
        control_scale=True
    )

    for poi in pois:
        coords = poi["coordenadas"]
        nome = poi["nome"]
        cat = poi.get("categoria", "Ponto")
        folium.Marker(
            location=coords,
            popup=f"<b>{nome}</b><br>Categoria: {cat}",
            tooltip=nome,
            icon=folium.Icon(
                color="blue",
                icon="info-sign"
            )
        ).add_to(mapa)

    if rota and rota["caminho"]:
        folium.PolyLine(
            locations=rota["caminho"],
            color="red",
            weight=5,
            opacity=0.8,
            tooltip="Rota calculada no grafo viário"
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


def exibir_metricas(rota):
    resultado = rota["resultado"]
    coluna1, coluna2, coluna3 = st.columns(3)
    if not resultado.foiEncontrada():
        st.error("Destino inalcançável." if resultado.situacao == "inalcancavel" else "Não foi possível calcular a rota: solicitação inválida ou ciclo negativo.")
        return
    coluna1.metric("Distância", f"{resultado.getDistanciaKm():.2f} km")
    coluna2.metric("Tempo estimado", f"{resultado.getTempoMinutos():.1f} min")
    coluna3.metric("Custo", f"R$ {resultado.custoTotalReais:.2f}")
    st.caption(f"Algoritmo: {rota['algoritmo']} · Nós expandidos: {resultado.nosExpandidos}")


def main():
    st.title("Sistema de Otimização de Rotas - Belo Horizonte")

    pois = obter_pois()
    grafo = obter_grafo()
    pois_ordenados = sorted(pois, key=lambda p: p["nome"].lower())
    nomes_pois = [p["nome"] for p in pois_ordenados]

    # Inicializa estados de busca na sessão
    if "resultados_busca" not in st.session_state:
        st.session_state["resultados_busca"] = []

    # Barra lateral: Gerenciamento e Busca de POIs
    with st.sidebar:
        st.header("📍 Pontos de Interesse (POIs)")
        st.caption(f"Catálogo offline com **{len(pois)} locais** em Belo Horizonte.")

        # Aba 1: Busca Dinâmica na API
        with st.expander("🔍 Buscar Local ou Ponto (API Online)", expanded=True):
            termo = st.text_input(
                "Nome do local ou referência:",
                placeholder="Ex: Drogaria Araujo, Praça Sete, Pão de Queijo...",
                key="input_busca_termo"
            )
            col_b1, col_b2 = st.columns([2, 1])
            if col_b1.button("Buscar em BH", use_container_width=True, type="primary"):
                if termo.strip():
                    with st.spinner("Consultando OpenStreetMap..."):
                        st.session_state["resultados_busca"] = buscar_poi_api(termo)
                    if not st.session_state["resultados_busca"]:
                        st.warning("Nenhum local encontrado em BH ou conexão indisponível.")
                else:
                    st.session_state["resultados_busca"] = []

            if col_b2.button("Limpar", use_container_width=True):
                st.session_state["resultados_busca"] = []
                st.rerun()

            # Renderização dos resultados persistidos na sessão (permite clique no botão Salvar)
            if st.session_state["resultados_busca"]:
                st.success(f"{len(st.session_state['resultados_busca'])} resultado(s):")
                for idx, r in enumerate(st.session_state["resultados_busca"]):
                    with st.container(border=True):
                        st.markdown(f"**{r['nome']}**")
                        if r.get("endereco"):
                            st.caption(f"📍 {r['endereco']}")
                        else:
                            st.caption(f"🏷️ Categoria: {r.get('categoria', 'geral')}")

                        if st.button("➕ Salvar no Catálogo", key=f"btn_salvar_{idx}_{r['id']}", use_container_width=True):
                            sucesso = salvar_poi_cache(r, CAMINHO_POIS)
                            if sucesso:
                                st.session_state["pois"] = carregar_pois(CAMINHO_POIS)
                                st.success(f"'{r['nome']}' salvo com sucesso!")
                                st.rerun()
                            else:
                                st.info("Este local já está cadastrado no catálogo.")

        # Aba 2: Adicionar Endereço Textual Direto
        with st.expander("📝 Cadastrar Endereço Manual", expanded=False):
            nome_manual = st.text_input("Apelido do Local:", placeholder="Ex: Casa, Escritório, Academia...")
            end_manual = st.text_input("Endereço completo em BH:", placeholder="Ex: Av. Afonso Pena, 1500 ou Rua Dom José Gaspar, 500")
            cat_manual = st.selectbox("Categoria:", ["ponto", "compras", "alimentacao", "educacao", "saude", "transporte", "lazer", "residencia"])

            if st.button("Buscar Coordenadas e Salvar", use_container_width=True):
                if nome_manual.strip() and end_manual.strip():
                    with st.spinner("Geocodificando endereço..."):
                        poi_geo = geocodificar_endereco(end_manual)
                    if poi_geo:
                        poi_geo["nome"] = nome_manual.strip()
                        poi_geo["categoria"] = cat_manual
                        sucesso = salvar_poi_cache(poi_geo, CAMINHO_POIS)
                        if sucesso:
                            st.session_state["pois"] = carregar_pois(CAMINHO_POIS)
                            st.success(f"Local '{nome_manual}' salvo com sucesso!")
                            st.rerun()
                        else:
                            st.info("Já existe um local com esse nome no catálogo.")
                    else:
                        st.error("Não foi possível encontrar as coordenadas para este endereço em BH.")
                else:
                    st.warning("Preencha o nome e o endereço completo.")

        # Aba 3: Remover Local do Catálogo
        with st.expander("🗑️ Remover Local do Catálogo", expanded=False):
            if nomes_pois:
                local_a_remover = st.selectbox(
                    "Selecione o local para excluir:",
                    nomes_pois,
                    key="sb_remover_poi"
                )
                if st.button("🗑️ Excluir Local Selecionado", use_container_width=True, type="secondary"):
                    if remover_poi_cache(local_a_remover, CAMINHO_POIS):
                        st.session_state["pois"] = carregar_pois(CAMINHO_POIS)
                        st.session_state.pop("rota", None)
                        st.success(f"'{local_a_remover}' foi removido com sucesso!")
                        st.rerun()
                    else:
                        st.error("Não foi possível remover o local selecionado.")
            else:
                st.info("Nenhum local cadastrado.")

        st.markdown("---")
        st.write("**Locais cadastrados no catálogo:**")
        for p in pois_ordenados:
            end_label = f" - _{p['endereco']}_" if p.get("endereco") else ""
            st.markdown(f"- **{p['nome']}**{end_label}")

    st.write(
        "Selecione os pontos de origem e destino "
        "e escolha o critério para calcular a rota."
    )

    coluna1, coluna2, coluna3, coluna4 = st.columns(4)

    with coluna1:
        origem_nome = st.selectbox(
            "Ponto de origem",
            nomes_pois if nomes_pois else ["Sem POIs cadastrados"],
            disabled=not nomes_pois
        )

    with coluna2:
        destino_nome = st.selectbox(
            "Ponto de destino",
            nomes_pois if nomes_pois else ["Sem POIs cadastrados"],
            index=1 if len(nomes_pois) > 1 else 0,
            disabled=not nomes_pois
        )

    with coluna3:
        criterio = st.selectbox(
            "Critério de otimização",
            ["Distância", "Tempo", "Custo"]
        )

    with coluna4:
        algoritmo = st.selectbox("Algoritmo", ["Dijkstra", "Bellman-Ford"])

    botao_calcular = st.button(
        "Calcular rota",
        type="primary",
        use_container_width=True
    )

    if botao_calcular:
        if not nomes_pois:
            st.warning("Cadastre ao menos um ponto de interesse.")
        elif origem_nome == destino_nome:
            st.session_state.pop("rota", None)

            st.warning(
                "A origem e o destino devem ser diferentes."
            )

        else:
            origem = next(
                poi for poi in pois
                if poi["nome"] == origem_nome
            )

            destino = next(
                poi for poi in pois
                if poi["nome"] == destino_nome
            )

            id_origem = origem.get("no_viario_associado")
            id_destino = destino.get("no_viario_associado")
            if id_origem not in grafo.vertices:
                id_origem = associar_poi_ao_no_mais_proximo(origem, grafo.vertices)
            if id_destino not in grafo.vertices:
                id_destino = associar_poi_ao_no_mais_proximo(destino, grafo.vertices)
            funcao = calcularRotaDijkstra if algoritmo == "Dijkstra" else calcularRotaBellmanFord
            resultado = funcao(grafo, id_origem, id_destino, criterio)
            vertices_rota = resultado.getVerticesCaminho()
            if resultado.foiEncontrada() and not vertices_rota:
                vertices_rota = [grafo.getVertice(id_origem)]
            st.session_state["rota"] = {
                "resultado": resultado,
                "caminho": [[v.latitude, v.longitude] for v in vertices_rota],
                "nomes_caminho": [v.nome or v.id for v in vertices_rota],
                "criterio": criterio,
                "algoritmo": algoritmo,
            }

    rota_atual = st.session_state.get("rota")

    mapa = criar_mapa(
        pois,
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

            if rota_atual["resultado"].foiEncontrada():
                st.write("**Caminho encontrado:**")

                st.write(" → ".join(rota_atual["nomes_caminho"]))
                st.write(f'**Critério:** {rota_atual["criterio"]}')

        else:
            st.info(
                "Selecione a origem, o destino e o critério. "
                "Depois, clique em 'Calcular rota'."
            )


if __name__ == "__main__":
    main()

