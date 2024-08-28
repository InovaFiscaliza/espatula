import streamlit as st
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
    MARKETPLACES,
    MARKETPLACE,
    TITLE,
    KEYWORD,
    CACHE,
    FOLDER,
    RECONNECT,
    TIMEOUT,
    MAX_SEARCH,
    MAX_PAGES,
    SHUFFLE,
    SCREENSHOT,
    HIDE_BROWSER,
    START,
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
    page_title="Regulatron",
    page_icon="🤖",
    layout="wide",
)

# Initialize st.session_state.mkplc to None
if "mkplc" not in st.session_state:
    st.session_state.mkplc = None

if "keyword" not in st.session_state:
    st.session_state.keyword = ""

if "folder" not in st.session_state:
    st.session_state.folder = None

if "cache" not in st.session_state:
    st.session_state.cache = {}

if "use_cache" not in st.session_state:
    st.session_state.use_cache = CACHE[0]

if "show_cache" not in st.session_state:
    st.session_state.show_cache = False

# Retrieve previous Session State to initialize the widgets
for key in st.session_state:
    st.session_state["_" + key] = st.session_state[key]


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
def set_folder():
    # Callback function to save the keyword selection to Session State
    if Path(st.session_state._folder).is_dir():
        st.session_state.folder = st.session_state._folder
    else:
        st.session_state.folder = None


@st.fragment
def set_cache():
    # Callback function to save the keyword selection to Session State
    scraper = SCRAPERS[st.session_state.mkplc](path=st.session_state.folder)
    st.session_state.cache = scraper.get_links(st.session_state.keyword)


@st.fragment
def use_cache():
    # Callback function to save the keyword selection to Session State
    st.session_state.use_cache = st.session_state._use_cache


@st.fragment
def show_links(main_page):
    with main_page.container():
        if st.session_state.cache:
            st.write(st.session_state.cache)


def run():
    container = st.container()
    st.session_state.show_cache = False
    container.empty()
    scraper = SCRAPERS[st.session_state.mkplc](
        headless=st.session_state.headless,
        path=st.session_state.folder,
        reconnect=st.session_state.reconnect,
        timeout=st.session_state.timeout,
    )
    keyword = st.session_state.keyword

    with container.empty():
        if st.session_state.use_cache == CACHE[0]:
            progress_text = "Realizando a busca de produtos...🕸️"
            progress_bar = st.progress(0, text=progress_text)
            for i, result in enumerate(
                scraper.search(keyword=keyword, max_pages=st.session_state.max_search),
                start=1,
            ):
                with st.empty():
                    st.write(result)
                progress_bar.progress(
                    (i * (100 // st.session_state.max_search)) % 100,
                    text=progress_text,
                )
            progress_bar.empty()
    with container.empty():
        progress_text = "Realizando raspagem das páginas dos produtos...🕷️"
        progress_bar = st.progress(0, text=progress_text)
        for i, result in enumerate(
            scraper.inspect_pages(
                keyword=keyword,
                screenshot=st.session_state.screenshot,
                sample=st.session_state.max_pages,
                shuffle=st.session_state.shuffle,
            ),
            start=1,
        ):
            progress_bar.progress(
                (i * (100 // st.session_state.max_pages)) % 100, text=progress_text
            )
            with st.empty():
                st.write(result)
        progress_bar.empty()

        table = Table(
            scraper.name,
            json_source=scraper.pages_file(st.session_state.keyword),
        )
        table.process()  # TODO: adicionar form para o fiscal inserir a categoria do SCH
        st.divider()
        st.success("Processamento dos dados finalizado!", icon="🎉")
        st.dataframe(table.df.loc[:, COLUNAS])
        st.snow()


config_container = st.sidebar.container(border=True)

mkplc = config_container.selectbox(
    MARKETPLACE,
    SCRAPERS.keys(),
    key="_mkplc",
    on_change=set_mkplc,
    placeholder="Selecione uma opção",
)

if st.session_state.mkplc is None:
    st.title(TITLE)
else:
    config_container.text_input(
        KEYWORD,
        placeholder="Qual a palavra-chave a pesquisar?",
        key="_keyword",
        on_change=set_keyword,
    )

    config_container.text_input(
        FOLDER,
        key="_folder",
        on_change=set_folder,
    )

    if st.session_state.keyword:
        if st.session_state.folder is not None:
            set_cache()
            if cache := st.session_state.cache:
                container = st.sidebar.container(border=True)
                container.info(f"Existem **{len(cache)}** resultados de busca em cache")
                if container.toggle("Visualizar cache", key="show_cache"):
                    show_links(st.empty())
                container.radio(
                    "Pesquisa de links",
                    options=CACHE,
                    key="_use_cache",
                    on_change=use_cache,
                )
            else:
                st.session_state.use_cache = CACHE[0]
        else:
            st.sidebar.error("Insira um caminho válido!", icon="🚨")
    else:
        st.sidebar.warning("Insira uma palavra-chave não vazia!", icon="⚠️")


with st.sidebar:
    if mkplc is not None:
        with st.form("config", border=False):
            with st.expander("CONFIGURAÇÕES", expanded=False):
                st.number_input(RECONNECT, min_value=2, key="reconnect", value=5)
                st.number_input(TIMEOUT, min_value=1, key="timeout", value=2)
                st.number_input(
                    MAX_SEARCH,
                    min_value=1,
                    value=10,
                    key="max_search",
                    disabled=(st.session_state.use_cache == CACHE[1]),
                )
                st.number_input(
                    MAX_PAGES,
                    min_value=1,
                    value=50,
                    key="max_pages",
                )
                st.checkbox(SHUFFLE, key="shuffle")
                st.checkbox(SCREENSHOT, key="screenshot")
                st.toggle(HIDE_BROWSER, key="headless")
            st.form_submit_button(START, on_click=run, use_container_width=True)
