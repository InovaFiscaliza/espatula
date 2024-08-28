import streamlit as st
from fastcore.xtras import Path, loads
from espatula.spiders import (
    AmazonScraper,
    MercadoLivreScraper,
    MagaluScraper,
    AmericanasScraper,
    CasasBahiaScraper,
    CarrefourScraper,
)
from espatula.processamento import Table, COLUNAS
from config import *

SCRAPERS = {
    "Amazon": AmazonScraper,
    "Mercado Livre": MercadoLivreScraper,
    "Magalu": MagaluScraper,
    "Americanas": AmericanasScraper,
    "Casas Bahia": CasasBahiaScraper,
    "Carrefour": CarrefourScraper,
}

st.set_page_config(
    page_title="Regulatron",
    page_icon="🤖",
    layout="wide",
)

# Initialize st.session_state.mkplc to None
if "mkplc" not in st.session_state:
    st.session_state.mkplc = None

if "keyword" not in st.session_state:
    st.session_state.keyword = ""

if "cache" not in st.session_state:
    st.session_state.cache = {}

if "use_cache" not in st.session_state:
    st.session_state.use_cache = None

if "show_cache" not in st.session_state:
    st.session_state.show_cache = False

# Retrieve the mkplc from Session State to initialize the widget
st.session_state._mkplc = st.session_state.mkplc


@st.fragment
def set_mkplc():
    # Callback function to save the mkplc selection to Session State
    st.session_state.mkplc = st.session_state._mkplc
    st.title(MARKETPLACES[st.session_state._mkplc])


@st.fragment
def set_keyword():
    # Callback function to save the keyword selection to Session State
    keyword = st.session_state._keyword.strip()
    st.session_state.keyword = keyword


@st.fragment
def set_cache():
    # Callback function to save the keyword selection to Session State
    scraper = SCRAPERS[st.session_state.mkplc]()
    st.session_state.cache = scraper.get_links(st.session_state.keyword)


@st.fragment
def use_cache():
    # Callback function to save the keyword selection to Session State
    if st.session_state._use_cache == "Utilizar resultados do cache":
        st.session_state.use_cache = True
    else:
        st.session_state.use_cache = False


@st.fragment
def show_links(main_page):
    with main_page.container():
        if st.session_state.cache:
            st.write(st.session_state.cache)


def run():
    st.session_state.show_cache = False
    scraper = SCRAPERS[st.session_state.mkplc](st.session_state.headless)
    keyword = st.session_state.keyword
    msg = st.toast("Iniciando a navegação...")
    if not st.session_state.use_cache:
        scraper.search(keyword=keyword)
        msg.toast("Pesquisa de links realizada com sucesso!")
    dados = scraper.inspect_pages(
        keyword=keyword,
        screenshot=st.session_state.screenshot,
        sample=st.session_state.sample_size,
        shuffle=st.session_state.shuffle,
    )
    msg.toast("Captação de Anúncios Concluída!")
    table = Table(
        scraper.name,
        dados,
        json_source=scraper.pages_file(st.session_state.keyword),
    )
    table.process()  # TODO: adicionar form para o fiscal inserir a categoria do SCH
    msg.toast("Processamento dos dados finalizado!", icon="🎉")
    st.dataframe(table.df.loc[:, COLUNAS])
    st.snow()


mkplc = st.sidebar.selectbox(
    MARKETPLACE,
    SCRAPERS.keys(),
    key="_mkplc",
    on_change=set_mkplc,
    placeholder="Selecione uma opção",
)

if st.session_state.mkplc is None:
    st.title("🤖 Regulatron")
else:
    st.sidebar.text_input(
        KEYWORD,
        placeholder="Qual a palavra-chave a pesquisar?",
        key="_keyword",
        on_change=set_keyword,
    )
    if st.session_state.keyword:
        set_cache()
        if cache := st.session_state.cache:
            container = st.sidebar.container(border=True)
            container.info(f"Existem **{len(cache)}** resultados de busca em cache")
            if container.toggle("Visualizar cache", key="show_cache"):
                show_links(st.empty())
            container.radio(
                "Pesquisa de links",
                options=["Efetuar nova busca", "Utilizar resultados do cache"],
                key="_use_cache",
                on_change=use_cache,
            )
        else:
            st.session_state.use_cache = False


with st.sidebar:
    if mkplc is not None:
        with st.form("config", border=False):
            with st.expander("CONFIGURAÇÕES", expanded=False):
                st.text_input(
                    FOLDER,
                    key="folder",
                    value=str(Path.cwd()),
                )
                st.number_input(
                    "Tempo de reconexão (seg)", min_value=2, key="reconnect", value=5
                )
                st.number_input(
                    "Tempo de espera (seg)", min_value=1, key="timeout", value=2
                )
                st.number_input(
                    "Número máximo de páginas de busca a navegar",
                    min_value=1,
                    value=10,
                    key="max_pages",
                    disabled=st.session_state.use_cache,
                )
                st.number_input(
                    "Número máximo de produtos a capturar",
                    min_value=1,
                    value=50,
                    key="sample_size",
                )
                st.checkbox(RANDOM_SAMPLE, key="shuffle")
                st.checkbox(CAPTURE_SCREENSHOT, key="screenshot")
                st.toggle(HIDE_BROWSER, key="headless")
            st.form_submit_button(NAVIGATE_ADS, on_click=run, use_container_width=True)
