from collections import defaultdict
from enum import Enum, auto

import streamlit as st

from config import SCRAPERS, MARKETPLACE, HIDE_BROWSER, SEARCH_PARAMETERS, KEYWORD, MAX_PAGES, SEARCH_LINKS, EXTRACTION_PARAMETERS, SEARCHED_TEXT, MAX_ADS, RANDOM_SAMPLE, CAPTURE_SCREENSHOT, NAVIGATE_ADS, REDO_SEARCH


if "plataforma" not in st.session_state:
    st.session_state.plataforma = "-"
if "links" not in st.session_state:
    st.session_state.links = defaultdict(set)

if "keyword" not in st.session_state:
    st.session_state.keyword = "smartphone"

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
    st.image("images/espatula.png", caption="Espátula", use_column_width=True)


def search(headless: bool, max_pages: int):
    scraper = SCRAPERS[st.session_state.plataforma](
        headless=headless,
    )
    with st.spinner(
        f"Buscando - **{st.session_state.plataforma}** : _{st.session_state.keyword}_ ..."
    ):
        links = scraper.search(
            keyword=st.session_state.keyword,
            max_pages=max_pages,
        )
        st.success(f"Foram encontrados {len(links)} anúncios!")
        st.info(f"Links salvos em {scraper.links_file(st.session_state.keyword)}")
        st.write(list(links.values()))
        st.session_state.links[st.session_state.plataforma].add(
            st.session_state.keyword
        )


def search_page(headless: bool):
    global ITERATION  # gambiarra para não haver conflitos de chaves nos widgets
    ITERATION += 1
    with st.sidebar:
        with st.expander(f"**{SEARCH_PARAMETERS}**", expanded=True):
            st.session_state.keyword = st.text_input(
                KEYWORD,
                "smartphone",
                key=f"keyword_{ITERATION}",
            )
            max_pages = st.slider(
                MAX_PAGES,
                1,
                40,
                10,
                key=f"max_pages_{ITERATION}",
            )
        st.button(
            SEARCH_LINKS,
            on_click=search,
            args=(headless, max_pages),
            use_container_width=True,
            key=f"search_{ITERATION}",
        )


def inspect(headless: bool, screenshot: bool, sample: int, shuffle: bool):
    scraper = SCRAPERS[st.session_state.plataforma](headless=headless)
    with st.spinner("Amostrando páginas dos anúncios..."):
        dados = scraper.inspect_pages(
            keyword=st.session_state.keyword,
            screenshot=screenshot,
            sample=sample,
            shuffle=shuffle,
        )
        st.balloons()
        st.success(f"Os dados foram salvos em {getattr(scraper, "output_file", None)}")
        st.write(list(dados.values()))


def inspect_page(headless: bool):
    global ITERATION
    ITERATION += 1
    with st.sidebar.expander(f"**{EXTRACTION_PARAMETERS}**", expanded=True):
        st.info(f"{SEARCHED_TEXT}: **{st.session_state.keyword}**")
        # Using 'key="sample"' is causing duplicate error
        sample = st.slider(
            MAX_ADS,
            1,
            100,
            50,
            key="sample_{ITERATION}",
        )
        shuffle = st.checkbox(
            f"**{RANDOM_SAMPLE}**", key="shuffle_{ITERATION}"
        )
        screenshot = st.checkbox(
            f"**{CAPTURE_SCREENSHOT}**", key="screenshot_{ITERATION}"
        )
        st.button(
            f"**{NAVIGATE_ADS}**",
            on_click=inspect,
            args=(headless, screenshot, sample, shuffle),
        )
    if st.sidebar.button(
        f"**{REDO_SEARCH}**",
        use_container_width=True,
    ):
        st.session_state.links[st.session_state.plataforma].discard(
            st.session_state.keyword
        )
        return


def main():
    global ITERATION
    ITERATION += 1
    headless = st.sidebar.checkbox(
        f"**{HIDE_BROWSER}**", key=f"headless_{ITERATION}"
    )
    if st.session_state.keyword in st.session_state.links[st.session_state.plataforma]:
        inspect_page(headless)
    else:
        search_page(headless)


class PageName(Enum):
    INTRO = "—"
    AMAZON = "Amazon"
    MERCADO_LIVRE = "Mercado Livre"
    MAGALU = "Magalu"
    AMERICANAS = "Americanas"
    CASAS_BAHIA = "Casas Bahia"
    CARREFOUR = "Carrefour"

page_names_to_funcs = {PageName.INTRO: intro} | {PageName(k): main for k in SCRAPERS.keys()}

st.session_state.plataforma = st.sidebar.selectbox(
    MARKETPLACE, [page.value for page in PageName]
)

page_names_to_funcs[PageName(st.session_state.plataforma)]()
