
import os
import streamlit as st
import folium
from streamlit_folium import st_folium

from mapa import (
    carregar_pois,
    carregar_mapa,
    construir_grafo,
    salvar_poi_cache,
    remover_poi_cache,
    buscar_poi_api,
    geocodificar_endereco,
    calcular_bbox_area,
    separar_pois_por_area
)
from apoio_interface import (
    ALGORITMOS,
    ROTULOS_CRITERIOS,
    aviso_poucos_pois_na_area,
    calcular_rota_entre_pois,
    formatar_distancia,
    formatar_km,
    formatar_minutos,
    formatar_reais,
    legenda_pois_fora_da_area,
    limites_do_enquadramento,
    limites_dos_pontos,
    motivo_fora_da_area,
    parametros_da_selecao,
    rota_corresponde_a_selecao,
    trechos_do_mapa
)

CAMINHO_POIS = os.path.join(os.path.dirname(__file__), "dados", "pontos_interesse.json")
CAMINHO_MAPA = os.path.join(os.path.dirname(__file__), "dados", "mapa.json")

st.set_page_config(
    page_title="Sistema de Rotas - Belo Horizonte",
    page_icon=":material/map:",
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


def criar_mapa(pois, rota=None, trechos_mapa=()):
    # Centro panorâmico de Belo Horizonte para visualização ampla dos pontos turísticos
    mapa = folium.Map(
        location=[-19.9190, -43.9550],
        zoom_start=12,
        control_scale=True
    )

    # Área do mapa: ruas cobertas pelo grafo, em cinza claro por baixo do resto
    for trecho in trechos_mapa:
        folium.PolyLine(
            locations=trecho,
            color="#8c8c8c",
            weight=3,
            opacity=0.6
        ).add_to(mapa)
    if trechos_mapa and not rota:
        # Sem rota, enquadra a área do mapa (em BH inteira ela ficaria pequena demais)
        mapa.fit_bounds(limites_dos_pontos([p for trecho in trechos_mapa for p in trecho]), padding=(20, 20))

    # Origem e destino da rota têm marcadores próprios, sem o azul por baixo
    ids_origem_destino = set()
    if rota:
        ids_origem_destino = {rota["origem"]["poi"]["id"], rota["destino"]["poi"]["id"]}

    for poi in pois:
        if poi["id"] in ids_origem_destino:
            continue
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

    if rota:
        origem = rota["origem"]
        destino = rota["destino"]

        folium.PolyLine(
            locations=rota["caminho"],
            color="red",
            weight=5,
            opacity=0.8,
            tooltip="Rota calculada no grafo viário"
        ).add_to(mapa)

        # Trecho a pé, em linha reta, entre cada POI e o vértice associado a ele
        for trecho in (origem, destino):
            folium.PolyLine(
                locations=[trecho["poi"]["coordenadas"], trecho["coordenadas_vertice"]],
                color="gray",
                weight=3,
                opacity=0.9,
                dash_array="6, 8",
                tooltip=f"A pé até o grafo: {formatar_distancia(trecho['distancia_m'])}"
            ).add_to(mapa)

        folium.Marker(
            location=origem["poi"]["coordenadas"],
            popup=f"<b>Origem</b><br>{origem['poi']['nome']}",
            tooltip=f"Origem: {origem['poi']['nome']}",
            icon=folium.Icon(
                color="green",
                icon="play"
            )
        ).add_to(mapa)

        folium.Marker(
            location=destino["poi"]["coordenadas"],
            popup=f"<b>Destino</b><br>{destino['poi']['nome']}",
            tooltip=f"Destino: {destino['poi']['nome']}",
            icon=folium.Icon(
                color="red",
                icon="flag"
            )
        ).add_to(mapa)

        mapa.fit_bounds(limites_do_enquadramento(rota), padding=(30, 30))

    return mapa


def exibir_informacoes_rota(rota):
    resultado = rota["resultado"]
    parametros = rota["parametros"]
    origem = rota["origem"]
    destino = rota["destino"]

    # Uma métrica por linha: em três colunas dentro do painel estreito os valores eram cortados
    st.metric("Distância", formatar_km(resultado.distanciaTotalMetros))
    st.metric("Tempo estimado", formatar_minutos(resultado.tempoTotalSegundos))
    st.metric("Custo", formatar_reais(resultado.custoTotalReais))
    st.caption(
        f"Critério: {parametros['criterio']} · Algoritmo: {parametros['algoritmo']} · "
        f"Nós expandidos: {resultado.nosExpandidos}"
    )

    st.write("**Trechos a pé** (em linha reta, fora dos totais acima):")
    st.markdown(
        f"- Origem: {origem['poi']['nome']} → {origem['nome_vertice']}: "
        f"**{formatar_distancia(origem['distancia_m'])}**\n"
        f"- Destino: {destino['nome_vertice']} → {destino['poi']['nome']}: "
        f"**{formatar_distancia(destino['distancia_m'])}**"
    )

    st.write("**Caminho encontrado:**")
    st.write(" → ".join(rota["nomes_caminho"]))


def main():
    st.title("Sistema de Otimização de Rotas - Belo Horizonte")

    pois = obter_pois()
    grafo = obter_grafo()
    bbox_area = calcular_bbox_area(grafo)
    trechos_mapa = trechos_do_mapa(grafo)
    pois_ordenados = sorted(pois, key=lambda p: p["nome"].lower())
    nomes_pois = [p["nome"] for p in pois_ordenados]

    # Só podem ser origem ou destino os POIs a até LIMITE_ASSOCIACAO_METROS de um vértice
    pois_na_area, pois_fora_da_area = separar_pois_por_area(pois_ordenados, grafo)
    nomes_na_area = [p["nome"] for p in pois_na_area]

    # Inicializa estados de busca na sessão
    if "resultados_busca" not in st.session_state:
        st.session_state["resultados_busca"] = []

    # Barra lateral: Gerenciamento e Busca de POIs
    with st.sidebar:
        st.header(":material/location_on: Pontos de Interesse (POIs)")
        st.caption(f"Catálogo offline com **{len(pois)} locais** em Belo Horizonte.")

        # Aba 1: Busca Dinâmica na API
        with st.expander("Buscar Local ou Ponto (API Online)", expanded=True, icon=":material/search:"):
            st.caption("A busca considera só a área do mapa (ruas em cinza).")
            termo = st.text_input(
                "Nome do local ou referência:",
                placeholder="Ex: padaria, farmácia, Praça Cardeal Dom Serafim...",
                key="input_busca_termo"
            )
            # Um botão por linha: lado a lado, o nome do bairro e o "Limpar" eram cortados
            if st.button("Buscar na área do mapa", use_container_width=True, type="primary"):
                if termo.strip():
                    with st.spinner("Consultando OpenStreetMap..."):
                        st.session_state["resultados_busca"] = buscar_poi_api(termo, bbox=bbox_area)
                    if not st.session_state["resultados_busca"]:
                        st.warning("Nenhum local encontrado na área do mapa ou conexão indisponível.")
                else:
                    st.session_state["resultados_busca"] = []

            if st.button("Limpar", use_container_width=True):
                st.session_state["resultados_busca"] = []
                st.rerun()

            # Renderização dos resultados persistidos na sessão (permite clique no botão Salvar)
            if st.session_state["resultados_busca"]:
                st.success(f"{len(st.session_state['resultados_busca'])} resultado(s):")
                for idx, r in enumerate(st.session_state["resultados_busca"]):
                    with st.container(border=True):
                        st.markdown(f"**{r['nome']}**")
                        if r.get("endereco"):
                            st.caption(f":material/location_on: {r['endereco']}")
                        else:
                            st.caption(f":material/label: Categoria: {r.get('categoria', 'geral')}")

                        fora_da_area = motivo_fora_da_area(r, grafo)
                        if fora_da_area:
                            st.caption(f":material/warning: Fora da área do mapa: {fora_da_area}. Não pode ser salvo.")
                        elif st.button("Salvar no Catálogo", key=f"btn_salvar_{idx}_{r['id']}", use_container_width=True,
                                       icon=":material/add:"):
                            sucesso = salvar_poi_cache(r, CAMINHO_POIS)
                            if sucesso:
                                st.session_state["pois"] = carregar_pois(CAMINHO_POIS)
                                st.success(f"'{r['nome']}' salvo com sucesso!")
                                st.rerun()
                            else:
                                st.info("Este local já está cadastrado no catálogo.")

        # Aba 2: Adicionar Endereço Textual Direto
        with st.expander("Cadastrar Endereço Manual", expanded=False, icon=":material/edit_note:"):
            nome_manual = st.text_input("Apelido do Local:", placeholder="Ex: Casa, Escritório, Academia...")
            end_manual = st.text_input("Endereço (dentro da área do mapa):", placeholder="Ex: Avenida Dom José Gaspar, 500")
            cat_manual = st.selectbox("Categoria:", ["ponto", "compras", "alimentacao", "educacao", "saude", "transporte", "lazer", "residencia"])

            if st.button("Buscar Coordenadas e Salvar", use_container_width=True):
                if nome_manual.strip() and end_manual.strip():
                    with st.spinner("Geocodificando endereço..."):
                        # A área só dá preferência: um endereço de fora volta e o aviso diz onde ele fica
                        poi_geo = geocodificar_endereco(end_manual, bbox=bbox_area, somente_na_bbox=False)
                    if not poi_geo:
                        st.error("Endereço não encontrado ou conexão indisponível. Nada foi salvo.")
                    else:
                        fora_da_area = motivo_fora_da_area(poi_geo, grafo)
                        if fora_da_area:
                            st.error(
                                f"Endereço encontrado ({poi_geo['endereco']}), mas fora da área do mapa: "
                                f"{fora_da_area}. Nada foi salvo."
                            )
                        else:
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
                    st.warning("Preencha o nome e o endereço completo.")

        # Aba 3: Remover Local do Catálogo
        with st.expander("Remover Local do Catálogo", expanded=False, icon=":material/delete:"):
            if nomes_pois:
                local_a_remover = st.selectbox(
                    "Selecione o local para excluir:",
                    nomes_pois,
                    key="sb_remover_poi"
                )
                if st.button("Excluir Local Selecionado", use_container_width=True, type="secondary",
                             icon=":material/delete:"):
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

    legenda_fora = legenda_pois_fora_da_area(len(pois_fora_da_area), len(pois))
    if legenda_fora:
        st.caption(legenda_fora)

    # Sem seleção completa, não há com o que comparar a rota guardada
    parametros_atuais = None
    aviso_poucos_pois = aviso_poucos_pois_na_area(len(nomes_na_area))

    if aviso_poucos_pois:
        st.warning(aviso_poucos_pois)
    else:
        coluna1, coluna2, coluna3, coluna4 = st.columns(4)

        with coluna1:
            origem_nome = st.selectbox("Ponto de origem", nomes_na_area)

        with coluna2:
            destino_nome = st.selectbox("Ponto de destino", nomes_na_area, index=1)

        with coluna3:
            criterio = st.selectbox("Critério de otimização", list(ROTULOS_CRITERIOS))

        with coluna4:
            algoritmo = st.selectbox("Algoritmo", list(ALGORITMOS))

        parametros_atuais = parametros_da_selecao(origem_nome, destino_nome, criterio, algoritmo)

        botao_calcular = st.button(
            "Calcular rota",
            type="primary",
            use_container_width=True
        )

        if botao_calcular:
            # A rota anterior sai antes do cálculo e só é substituída se este der certo
            st.session_state.pop("rota", None)
            try:
                origem = next(poi for poi in pois_na_area if poi["nome"] == origem_nome)
                destino = next(poi for poi in pois_na_area if poi["nome"] == destino_nome)
                rota, aviso = calcular_rota_entre_pois(grafo, origem, destino, criterio, algoritmo)
            except Exception as erro:
                st.error(f"Não foi possível calcular a rota: {erro}")
            else:
                if aviso:
                    st.warning(aviso)
                else:
                    st.session_state["rota"] = rota

    rota_guardada = st.session_state.get("rota")
    # Rota calculada com outra origem, destino, critério ou algoritmo não é desenhada
    rota_atual = rota_guardada if rota_corresponde_a_selecao(rota_guardada, parametros_atuais) else None

    mapa = criar_mapa(
        pois,
        rota_atual,
        trechos_mapa
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
            exibir_informacoes_rota(rota_atual)
        elif rota_guardada:
            st.info(
                "A seleção mudou desde o último cálculo. "
                "Clique em 'Calcular rota' para recalcular a rota."
            )
        else:
            st.info(
                "Selecione a origem, o destino e o critério. "
                "Depois, clique em 'Calcular rota'."
            )


if __name__ == "__main__":
    main()

