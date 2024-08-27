import logging
import random
import os
from collections import defaultdict

import streamlit as st
import requests
from fastcore.xtras import Path

from espatula.spiders import (
    AmazonScraper,
    MercadoLivreScraper,
    MagaluScraper,
    AmericanasScraper,
    CasasBahiaScraper,
    CarrefourScraper,
)

from espatula.processamento import Table, COLUNAS


from config import (
    CAPTURE_SCREENSHOT,
    EXTRACTION_PARAMETERS,
    HIDE_BROWSER,
    KEYWORD,
    MARKETPLACE,
    MAX_ADS,
    MAX_PAGES,
    NAVIGATE_ADS,
    RANDOM_SAMPLE,
    SEARCH_LINKS,
    SEARCH_PARAMETERS,
    SEARCHED_TEXT,
)

SCRAPERS = {
    "Amazon": AmazonScraper,
    "Mercado Livre": MercadoLivreScraper,
    "Magalu": MagaluScraper,
    "Americanas": AmericanasScraper,
    "Casas Bahia": CasasBahiaScraper,
    "Carrefour": CarrefourScraper,
}


st.set_page_config(
    page_title="Espátula",
    page_icon="🛠️",
)
# Now import the configuration and scraper classe
logging.basicConfig(level=logging.ERROR)

# if "folder" not in st.session_state:
#     st.session_state.folder = str(Path.cwd())

# if "reconnect" not in st.session_state:
#     st.session_state.reconnect = 10

# if "timeout" not in st.session_state:
#     st.session_state.timeout = 5

# if "scrapers" not in st.session_state:
#     st.session_state.scrapers = defaultdict(list)


@st.fragment
def amazon_search(scraper):
    with st.status(f"Buscando - **Amazon** : _{st.session_state.amazon_keyword}_ ..."):
        scraper.search(
            keyword=st.session_state.amazon_keyword,
            max_pages=st.session_state.amazon_max_pages,
        )


@st.fragment
def amazon_links():
    scraper = AmazonScraper(
        headless=st.session_state.amazon_headless,
        # timeout=st.session_state.timeout,
        # reconnect=st.session_state.reconnect,
        # folder=st.session_state.folder,
    )
    if links := scraper.get_links(st.session_state.amazon_keyword):
        st.success(
            f"Foram encontrados {len(links)} anúncios para o termo {st.session_state.amazon_keyword}!",
            icon="✅",
        )
        st.info(
            f"Links salvos em {scraper.links_file(st.session_state.amazon_keyword)}"
        )
        st.write(list(links.values()))
        label = "Refazer Busca🔄"

    else:
        st.warning(
            f"Nenhum link salvo para o termo {st.session_state.amazon_keyword}!",
            icon="⚠️",
        )
        label = "Efetuar Busca➡️"

    st.button(label, on_click=amazon_search, args=(scraper,), use_container_width=True)


def amazon():
    name = "Amazon🛒🛍"
    st.title(name)
    # TODO: Escrever uma explicação aqui
    tabs = st.tabs(["🔎Links", "🗐 Páginas"])

    with tabs[0]:
        st.sidebar.title(SEARCH_PARAMETERS)
        with st.sidebar.form("search_form"):
            st.checkbox(f"**{HIDE_BROWSER}**", key="amazon_headless")
            st.text_input(
                KEYWORD,
                key="amazon_keyword",
            )
            st.slider(
                MAX_PAGES,
                1,
                40,
                10,
                key="amazon_max_pages",
            )
            submit = st.form_submit_button(
                SEARCH_LINKS,
            )
            if submit:
                st.success("Variáveis de busca definidas com sucesso!")
        if submit:
            amazon_links()
            # timeout=st.session_state.timeout,
            # reconnect=st.session_state.reconnect,
            # folder=st.session_state.folder,


def intro():
    st.title("Projeto Regulatron - Módulo Espátula")
    st.image("images/espatula.png", caption="Espátula", use_column_width=True)
    st.logo("images/logo.svg", icon_image="images/logo.svg")
    st.info("""
        Raspagem de dados _(webscraping)_ de anúncios de
        produtos para telecomunicações. 
        """)
    st.markdown(
        """
    
        * 👨🏻‍💻 Simular o comportamento de um consumidor ao acessar o site.
        * 👾 Generalizar a implementação para outras plataformas
        * 🤖 Tornar a extração independente da categorização de cada marketplace atráves da busca por termos
        * 🗄️ Cruzar com os registros de produtos homologados da Anatel.
        * 📊 Categorizar e efetuar análises quantitativas
        
        **👈 Para iniciar primeiramente defina os parâmetros globais 
        (aplicáveis a todos os _scrapers_) ao lado, depois é só navegar em qualquer página e seguir as instruções!**
        """
    )
    st.sidebar.title("Parâmetros Globais")

    with st.sidebar.form("env_vars_form"):
        st.text_input(
            "PASTA",
            key="folder",
            value=str(Path.cwd()),
        )
        st.number_input("TEMPO DE RECONEXÃO(s)", min_value=2, key="reconnect", value=5)
        st.number_input("TEMPO DE ESPERA(s)", min_value=1, key="timeout", value=2)
        submit = st.form_submit_button(
            "Definir Parâmetros",
        )
        if submit:
            st.success("Variáveis globais definidas com sucesso!")


intro_page = st.Page(intro, title="Introdução", icon=":material/login:")
amazon_page = st.Page(amazon, title="Amazon")

pg = st.navigation([intro_page, amazon_page])
pg.run()


# st.text_input(
#     KEYWORD,
#     key="keyword",
# )
# headless = st.checkbox(f"**{HIDE_BROWSER}**", key="headless")


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
        st.session_state.links[st.session_state.plataforma][st.session_state.keyword][
            "links"
        ] = links


def search_page():
    # global ITERATION  # gambiarra para não haver conflitos de chaves nos widgets
    # ITERATION += 1
    st.sidebar.title(SEARCH_PARAMETERS)
    with st.sidebar.form("search_form"):
        st.slider(
            MAX_PAGES,
            1,
            40,
            10,
            key="max_pages",
        )
        st.form_submit_button(
            SEARCH_LINKS,
            on_click=search,
            use_container_width=True,
        )


def inspect(keyword):
    scraper = SCRAPERS[st.session_state.plataforma](headless=st.session_state.headless)
    with st.spinner("Acessando os anúncios, aguarde..."):
        dados = scraper.inspect_pages(
            keyword=keyword,
            screenshot=st.session_state.screenshot,
            sample=st.session_state.sample,
            shuffle=st.session_state.shuffle,
        )
        table = Table(scraper.name, dados, json_source=scraper.pages_file(keyword))
        table.process()  # TODO: adicionar form para o fiscal inserir a categoria do SCH
        st.balloons()
        st.dataframe(table.df.loc[:, COLUNAS])


def inspect_page():
    st.sidebar.title(EXTRACTION_PARAMETERS)
    with st.sidebar.form(f"**{EXTRACTION_PARAMETERS}**"):
        st.info(f"{SEARCHED_TEXT}: **{st.session_state.keyword}**")
        st.slider(
            MAX_ADS,
            1,
            100,
            50,
            key="sample",
        )
        st.checkbox(f"**{RANDOM_SAMPLE}**", key="shuffle")
        st.checkbox(f"**{CAPTURE_SCREENSHOT}**", key="screenshot")
        st.form_submit_button(
            f"**{NAVIGATE_ADS}**",
            on_click=inspect,
            args=(st.session_state.keyword,),
        )


@st.cache_data
def get_dog():
    response = requests.get("https://random.dog/doggos")
    return [f"https://random.dog/{img}" for img in response.json()]


# def main():
#     handle_page_layout()
#     if not st.session_state.links[
#         st.session_state.plataforma
#     ]:  # Show dog if empty dict of links
#         dog = random.choice(get_dog())
#         if dog[-4:] == ".mp4":
#             st.video(
#                 dog,
#                 autoplay=True,
#                 loop=True,
#             )
#         else:
#             st.image(
#                 dog,
#                 caption="Aguardando a busca de anúncios...",
#                 width=480,
#             )


# def intro_page():
#     page_names_to_funcs = {"—": intro} | {k: main for k in SCRAPERS.keys()}

#     try:
#         st.session_state.plataforma = st.sidebar.selectbox(
#             MARKETPLACE, page_names_to_funcs.keys()
#         )
#         page_names_to_funcs[st.session_state.plataforma]()
#     except Exception as e:
#         logging.error(
#             f"An error occurred while selecting or executing page function: {str(e)}"
#         )
#         st.error("An error occurred while loading the page. Please try again later.")


# intro_page()
