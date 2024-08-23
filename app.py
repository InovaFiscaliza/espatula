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


if "plataforma" not in st.session_state:
    st.session_state.plataforma = "-"
if "links" not in st.session_state:
    st.session_state.links = defaultdict(set)

if "keyword" not in st.session_state:
    st.session_state.keyword = ""


def set_environment_variables():
    st.sidebar.title("Parâmetros Globais")
    with st.sidebar.form("env_vars_form"):
        folder = st.text_input(
            "PASTA", value=os.environ.get("FOLDER", f"{Path(__file__)}/data")
        )
        reconnect = st.number_input(
            "TEMPO DE RECONEXÃO",
            min_value=2,
            value=int(os.environ.get("RECONNECT", 10)),
        )
        timeout = st.number_input(
            "TEMPO DE ESPERA", min_value=1, value=int(os.environ.get("TIMEOUT", 5))
        )
        st.checkbox(f"**{HIDE_BROWSER}**", key="headless")

        submit = st.form_submit_button("Definir Parâmetros")
        if submit:
            os.environ["FOLDER"] = str(folder)
            os.environ["RECONNECT"] = str(reconnect)
            os.environ["TIMEOUT"] = str(timeout)
            st.success("Variáveis de ambiente definidas com sucesso!")


set_environment_variables()


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


def search_page():
    # global ITERATION  # gambiarra para não haver conflitos de chaves nos widgets
    # ITERATION += 1
    st.sidebar.title(SEARCH_PARAMETERS)
    with st.sidebar.form("search_form"):
        st.text_input(
            KEYWORD,
            "smartphone",
            key="keyword",
        )
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


def handle_page_logic():
    try:
        if (
            st.session_state.keyword
            in st.session_state.links[st.session_state.plataforma]
        ):
            inspect_page()
            return "inspect"
        else:
            search_page()
            return "search"
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        st.error("An unexpected error occurred. Please try again later.")


@st.cache_data
def get_dog():
    response = requests.get("https://random.dog/doggos")
    return [f"https://random.dog/{img}" for img in response.json()]


def main():
    if handle_page_logic() == "search":
        dog = random.choice(get_dog())
        if dog[-4:] == ".mp4":
            st.video(
                dog,
                autoplay=True,
                loop=True,
            )
        else:
            st.image(
                dog,
                caption="Aguardando a busca de anúncios...",
                width=480,
            )


def intro_page():
    page_names_to_funcs = {"—": intro} | {k: main for k in SCRAPERS.keys()}

    try:
        st.session_state.plataforma = st.sidebar.selectbox(
            MARKETPLACE, page_names_to_funcs.keys()
        )
        page_names_to_funcs[st.session_state.plataforma]()
    except Exception as e:
        logging.error(
            f"An error occurred while selecting or executing page function: {str(e)}"
        )
        st.error("An error occurred while loading the page. Please try again later.")


intro_page()
