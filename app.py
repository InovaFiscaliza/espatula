from collections import defaultdict

import streamlit as st

from espatula.spiders import (
    AmazonScraper,
    MercadoLivreScraper,
    MagaluScraper,
    AmericanasScraper,
    CasasBahiaScraper,
    CarrefourScraper,
)


if "plataforma" not in st.session_state:
    st.session_state.plataforma = "-"
if "links" not in st.session_state:
    st.session_state.links = defaultdict(set)

if "keyword" not in st.session_state:
    st.session_state.keyword = "smartphone"

SCRAPERS = {
    "Amazon": AmazonScraper,
    "Mercado Livre": MercadoLivreScraper,
    "Magalu": MagaluScraper,
    "Americanas": AmericanasScraper,
    "Casas Bahia": CasasBahiaScraper,
    "Carrefour": CarrefourScraper,
}

ITERATION = 0

st.set_page_config(
    page_title="Espátula",
    page_icon="🛠️",
)


def intro():
    st.write("# Regulatron")
    st.logo("images/logo.svg", icon_image="images/logo.svg")
    st.sidebar.success("Selecione uma plataforma")
    st.info("""
        Essa aplicação efetua primariamente a raspagem de dados _(webscraping)_ de anúncios de
        produtos para telecomunicações publicados em alguns dos principais _marketplaces_ do país. 
        """)
    st.markdown(
        """
    
        * 👨🏻‍💻 Simular o comportamento de um consumidor ao acessar o site.
        * 👾 Generalizar a implementação para outras plataformas
        * 🤖 Tornar a extração independente da categorização de cada marketplace.
        * 🗄️ Cruzar com os registros de produtos homologados da Anatel.
        * 📊 Categorizar e efetuar análises quantitativas
        
        **👈 Para iniciar selecione qual plataforma deseja pesquisar no menu ao lado!**
        """
    )
    st.image("espatula.png", caption="Espátula", use_column_width=True)


def search():
    scraper = SCRAPERS[st.session_state.plataforma](
        headless=st.session_state.headless,
    )
    with st.spinner(
        f"Buscando - **{st.session_state.plataforma}** : _{st.session_state.keyword}_ ..."
    ):
        links = scraper.search(
            keyword=st.session_state.keyword,
            max_pages=st.session_state.max_pages,
        )
        st.success(f"Foram encontrados {len(links)} anúncios!")
        st.info(f"Links salvos em {scraper.links_file(st.session_state.keyword)}")
        st.write(list(links.values()))
        st.session_state.links[st.session_state.plataforma].add(
            st.session_state.keyword
        )

    st.divider()


def search_page():
    global ITERATION  # gambiarra para não haver conflitos de chaves nos widgets
    ITERATION += 1
    with st.sidebar:
        with st.expander("**Parâmetros da Busca**", expanded=True):
            st.session_state.keyword = st.text_input(
                "Palavra-chave",
                "smartphone",
                key=f"keyword_{ITERATION}",
            )
            st.session_state.max_pages = st.slider(
                "Número máximo de páginas de busca a navegar",
                1,
                40,
                10,
                key=f"max_pages_{ITERATION}",
            )
        st.button("Iniciar Busca🔎", on_click=search, use_container_width=True)


def inspect():
    scraper = SCRAPERS[st.session_state.plataforma](headless=st.session_state.headless)
    with st.spinner("Amostrando páginas dos anúncios..."):
        dados = scraper.inspect_pages(
            keyword=st.session_state.keyword,
            screenshot=st.session_state.screenshot,
            sample=st.session_state.sample,
            shuffle=st.session_state.shuffle,
        )
        st.balloons()
        st.success(f"Os dados foram salvos em {getattr(scraper, "output_file", None)}")
        st.write(list(dados.values()))


def inspect_page():
    with st.sidebar:
        with st.expander("**Parâmetros da Extração de Dados**", expanded=True):
            st.info(f"Texto Pesquisado: **{st.session_state.keyword}**")
            # Using 'key="sample"' is causing duplicate error
            st.slider("Número máximo de anúncios a extrair", 1, 100, 50, key="sample")
            st.checkbox("**Amostrar páginas aleatoriamente**", key="shuffle")
            st.checkbox("**Capturar tela do anúncio**", key="screenshot")
            st.button("**Navegar páginas dos anúncios🚀**", on_click=inspect)


def main():
    global ITERATION
    st.session_state.headless = st.sidebar.checkbox(
        "**Ocultar o navegador**", key=f"headless_{ITERATION}"
    )
    if st.session_state.keyword in st.session_state.links[st.session_state.plataforma]:
        with st.sidebar:
            inspect_page()
            if st.button(
                "**Refazer Busca😵‍💫**",
                on_click=search_page,
                use_container_width=True,
            ):
                st.session_state.links[st.session_state.plataforma].discard(
                    st.session_state.keyword
                )
                ITERATION += 1
                main()
    else:
        search_page()


page_names_to_funcs = {"—": intro} | {k: main for k in SCRAPERS.keys()}

st.session_state.plataforma = st.sidebar.selectbox(
    "Marketplace", page_names_to_funcs.keys()
)

page_names_to_funcs[st.session_state.plataforma]()
