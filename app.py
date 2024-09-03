import time

import streamlit as st
import pandas as pd
from fastcore.xtras import Path
from gradio_client import Client, handle_file


from config import (
    CACHE,
    FOLDER,
    HIDE_BROWSER,
    KEYWORD,
    LOGOS,
    MARKETPLACE,
    MAX_PAGES,
    MAX_SEARCH,
    RECONNECT,
    SCREENSHOT,
    SHUFFLE,
    START,
    TIMEOUT,
    TITLE,
)
from espatula import (
    AmazonScraper,
    AmericanasScraper,
    CarrefourScraper,
    CasasBahiaScraper,
    MagaluScraper,
    MercadoLivreScraper,
)

SCRAPERS = {
    "Amazon": AmazonScraper,
    "Mercado Livre": MercadoLivreScraper,
    "Magalu": MagaluScraper,
    "Americanas": AmericanasScraper,
    "Casas Bahia": CasasBahiaScraper,
    "Carrefour": CarrefourScraper,
}

COLUNAS = [
    "nome",
    "fabricante",
    "modelo",
    "certificado",
    "ean_gtin",
    "passível?",
    "probabilidade",
    "nome_sch",
    "fabricante_sch",
    "modelo_sch",
    "nome_score",
    "modelo_score",
    "tipo_sch",
    "subcategoria",
    "indice",
    "página_de_busca",
    "palavra_busca",
    "data",
    "screenshot",
    "url",
]

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
    st.session_state.folder = rf"{Path.home()}\regulatron"

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
    img = LOGOS[st.session_state._mkplc]
    st.logo(img)
    st.image(img, width=320)


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
def show_links():
    with st.container(height=720):
        if st.session_state.cache:
            st.write(st.session_state.cache)


def request_table(json_path):
    client = Client("ronaldokun/ecomproc")
    result = client.predict(
        json_file=handle_file(str(json_path)),
        api_name="/process_to_table",
    )
    return pd.DataFrame(result["data"], columns=result["headers"], dtype="string")


def run():
    st.session_state.show_cache = False
    scraper = SCRAPERS[st.session_state.mkplc](
        headless=not st.session_state.show_browser,
        path=st.session_state.folder,
        reconnect=st.session_state.reconnect,
        timeout=st.session_state.timeout,
    )
    keyword = st.session_state.keyword

    with st.container():
        if st.session_state.use_cache == CACHE[0]:
            progress_text = "Realizando a busca de produtos...🕸️"
            progress_bar = st.progress(0, text=progress_text)
            output = st.empty()
            percentage = 100 / st.session_state.max_search
            for i, result in enumerate(
                scraper.search(keyword=keyword, max_pages=st.session_state.max_search),
                start=1,
            ):
                with output.empty():
                    st.write(result)
                progress_bar.progress(
                    int((i * percentage) % 100),
                    text=progress_text,
                )
            time.sleep(1)
            output.empty()
            progress_bar.empty()
    with st.container():
        progress_text = "Realizando raspagem das páginas dos produtos...🕷️"
        progress_bar = st.progress(0, text=progress_text)
        output = st.empty()
        percentage = 100 / st.session_state.max_pages
        for i, result in enumerate(
            scraper.inspect_pages(
                keyword=keyword,
                screenshot=st.session_state.screenshot,
                sample=st.session_state.max_pages,
                shuffle=st.session_state.shuffle,
            ),
            start=1,
        ):
            with output.empty():
                left, right = st.columns([1, 1], vertical_alignment="top")
                with left:
                    if not (imagem := result.get("imagens", [])[0]):
                        imagem = result.get("imagem")
                    left.write("Imagem do produto")
                    nome = result.get("nome")
                    left.image(imagem, width=480, caption=nome)
                with right:
                    right.write("Dados do produto")
                    right.write(result)
            progress_bar.progress(int((i * percentage) % 100), text=progress_text)
        time.sleep(1)
        output.empty()
        progress_bar.empty()
        df = request_table(scraper.pages_file(st.session_state.keyword))
        st.divider()
        st.success("Processamento dos dados finalizado!", icon="🎉")
        st.snow()
    st.dataframe(df.loc[:, COLUNAS], use_container_width=True)


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
    st.image(
        LOGOS["Espatula"],
        width=480,
        caption="Raspagem de Dados de Produtos de Telecomunicações",
    )
    st.sidebar.success(
        "Por favor, selecione uma plataforma para iniciar a pesquisa.",
        icon="👆🏾",
    )
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
        if Path(st.session_state.folder).is_dir():
            set_cache()
            if cache := st.session_state.cache:
                container = st.sidebar.container(border=True)
                container.info(f"Existem **{len(cache)}** resultados de busca em cache")
                if container.toggle("Visualizar cache", key="show_cache"):
                    show_links()
                container.radio(
                    "Pesquisa de links",
                    options=CACHE,
                    key="_use_cache",
                    on_change=use_cache,
                )
            else:
                st.session_state.use_cache = CACHE[0]

            with st.sidebar:
                with st.form("config", border=False):
                    with st.expander("CONFIGURAÇÕES", expanded=False):
                        st.number_input(
                            RECONNECT, min_value=2, key="reconnect", value=5
                        )
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
                        st.toggle(HIDE_BROWSER, key="show_browser")
                    st.form_submit_button(START, on_click=run, use_container_width=True)

        else:
            st.sidebar.error("Insira um caminho válido!", icon="🚨")
    else:
        st.sidebar.warning("Insira uma palavra-chave não vazia!", icon="⚠️")
