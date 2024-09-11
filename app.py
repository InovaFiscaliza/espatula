import time
import json

import streamlit as st
import pandas as pd
from fastcore.xtras import Path
from gradio_client import Client, handle_file
import streamlit as st

from config import (
    CACHE,
    FOLDER,
    SHOW_BROWSER,
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

COLUNAS = {
    "url": "string",
    "nome": "string",
    "fabricante": "category",
    "modelo": "category",
    "certificado": "string",
    "ean_gtin": "string",
    "subcategoria": "category",
    "nome_sch": "string",
    "tipo_sch": "category",
    "fabricante_sch": "category",
    "modelo_sch": "category",
    "nome_score": "int8",
    "modelo_score": "int8",
    "passível?": "bool",
    "probabilidade": "float32",
}


KEYS = {
    "keyword": KEYWORD,
    "folder": FOLDER,
    "use_cache": CACHE[0],
    "show_browser": SHOW_BROWSER,
    "marketplace": MARKETPLACE,
    "max_pages": MAX_PAGES,
    "max_search": MAX_SEARCH,
    "reconnect": RECONNECT,
    "screenshot": SCREENSHOT,
    "shuffle": SHUFFLE,
    "timeout": TIMEOUT,
    "title": TITLE,
    "logos": LOGOS,
}

config_file = Path(__file__).parent / "config.json"

if config_file.exists():
    CONFIG = config_file.read_json()
else:
    CONFIG = {}

st.set_page_config(
    page_title="Regulatron",
    page_icon="🤖",
    layout="wide",
)

STATE = st.session_state

# Initialize STATE.mkplc to None
if "mkplc" not in STATE:
    STATE.mkplc = None

if (key := "keyword") not in STATE:
    STATE[key] = CONFIG.get(KEYS[key], "")

if (key := "folder") not in STATE:
    if not (folder := CONFIG.get(KEYS[key], "")):
        folder = rf"{Path.home()}"
    STATE[key] = folder
if "cache" not in STATE:
    STATE.cached_links = {}

if (key := "use_cache") not in STATE:
    STATE[key] = CACHE[0] if CONFIG.get(KEYS[key]) else CACHE[1]

if "show_cache" not in STATE:
    STATE.show_cache = False

# Retrieve previous Session State to initialize the widgets
for key in STATE:
    if key != "use_cache":
        STATE["_" + key] = STATE[key]
    if key in KEYS:
        CONFIG[KEYS[key]] = STATE[key]


def save_config():
    # Callback function to save the configuration to a JSON file
    json.dump(
        CONFIG,
        config_file.open("w", encoding="utf-8"),
        ensure_ascii=False,
    )


@st.fragment
def set_mkplc():
    # Callback function to save the mkplc selection to Session State
    STATE.mkplc = STATE._mkplc
    img = LOGOS[STATE._mkplc]
    st.logo(img)
    st.image(img, width=320)


@st.fragment
def set_keyword():
    # Callback function to save the keyword selection to Session State
    keyword = STATE._keyword.strip()
    STATE.keyword = keyword


@st.fragment
def set_folder():
    # Callback function to save the keyword selection to Session State
    if Path(STATE._folder).is_dir():
        STATE.folder = STATE._folder


@st.fragment
def set_cache():
    # Callback function to save the keyword selection to Session State
    scraper = SCRAPERS[STATE.mkplc](path=STATE.folder)
    STATE.cached_links = scraper.get_links(STATE.keyword)


@st.fragment
def use_cache():
    # Callback function to save the keyword selection to Session State
    STATE.use_cache = STATE._use_cache


@st.fragment
def show_links():
    with st.container(height=720):
        if STATE.cached_links:
            st.json(list(STATE.cached_links.values()), expanded=True)


def request_table(json_path: Path) -> pd.DataFrame:
    client = Client("ronaldokun/ecomproc")
    result = client.predict(
        json_file=handle_file(str(json_path)),
        api_name="/process_to_table",
    )
    return pd.DataFrame(result["data"], columns=result["headers"]).astype(COLUNAS)


def run_search(scraper):
    with st.container():
        progress_text = "Realizando a busca de produtos...🕸️"
        progress_bar = st.progress(0, text=progress_text)
        output = st.empty()
        percentage = 100 / STATE.max_search
        for i, result in enumerate(
            scraper.search(
                keyword=STATE.keyword,
                max_pages=STATE.max_search,
            ),
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


def inspect_pages(scraper):
    with st.container():
        progress_text = "Realizando raspagem das páginas dos produtos...🕷️"
        progress_bar = st.progress(0, text=progress_text)
        output = st.empty()
        percentage = 100 / STATE.max_pages
        for i, result in enumerate(
            scraper.inspect_pages(
                keyword=STATE.keyword,
                screenshot=STATE.screenshot,
                sample=STATE.max_pages,
                shuffle=STATE.shuffle,
            ),
            start=1,
        ):
            with output.empty():
                left, right = st.columns([1, 1], vertical_alignment="top")
                with left:
                    try:
                        imagem = result.get("imagens", [])
                        if len(imagem) > 1:
                            imagem = imagem[0]
                        else:
                            imagem = result.get("imagem")
                        left.write("Imagem do produto")
                        nome = result.get("nome")
                        left.image(imagem, width=480, caption=nome)
                    except Exception:
                        left.write("Não foi possível carregar a imagem do produto")
                with right:
                    right.write("Dados do produto")
                    right.json(result, expanded=1)
            progress_bar.progress(int((i * percentage) % 100), text=progress_text)
        time.sleep(1)
        output.empty()
        progress_bar.empty()


def process_data(pages_file: Path):
    df = request_table(pages_file)
    st.divider()
    st.success("Processamento dos dados finalizado!", icon="🎉")
    st.dataframe(
        df.loc[:, list(COLUNAS.keys())],
        use_container_width=True,
        column_config={
            "url": st.column_config.LinkColumn(
                "URL", width=None, display_text="Link", help="Dados do Anúncio"
            ),
            "nome": st.column_config.TextColumn(
                "Nome", width=None, help="Dados do Anúncio"
            ),
            "fabricante": st.column_config.TextColumn(
                "Fabricante", width=None, help="Dados do Anúncio"
            ),
            "modelo": st.column_config.TextColumn(
                "Modelo", width=None, help="Dados do Anúncio"
            ),
            "certificado": st.column_config.TextColumn(
                "Certificado", width=None, help="Dados do Anúncio"
            ),
            "ean_gtin": st.column_config.TextColumn(
                "EAN/GTIN", width=None, help="Dados do Anúncio"
            ),
            "subcategoria": st.column_config.SelectboxColumn(
                "Categoria", width=None, help="Dados do Anúncio"
            ),
            "nome_sch": st.column_config.TextColumn(
                "Nome SCH", width=None, help="Dados de Certificação - SCH"
            ),
            "fabricante_sch": st.column_config.TextColumn(
                "Fabricante SCH", width=None, help="Dados de Certificação - SCH"
            ),
            "modelo_sch": st.column_config.TextColumn(
                "Modelo SCH", width=None, help="Dados de Certificação - SCH"
            ),
            "tipo_sch": st.column_config.SelectboxColumn(
                "Tipo SCH", width=None, help="Dados de Certificação - SCH"
            ),
            "nome_score": st.column_config.ProgressColumn(
                "Taxa de Sobreposição - Nome",
                width=None,
                help="Comparativo textual - Distância de Levenshtein",
            ),
            "modelo_score": st.column_config.ProgressColumn(
                "Taxa de Sobroposição - Modelo",
                width=None,
                help="Comparativo textual - Distância de Levenshtein",
            ),
            "passível?": st.column_config.CheckboxColumn(
                "Homologação Compulsória",
                width=None,
                help="Classificação - Machine Learning",
            ),
            "probabilidade": st.column_config.ProgressColumn(
                "Probabilidade",
                format="%.4f%%",
                min_value=0,
                max_value=100,
                help="Classificação - Machine Learning",
            ),
        },
        hide_index=True,
        on_select="rerun",
        selection_mode="single-column",
    )
    st.snow()


def run():
    save_config()
    STATE.show_cache = False
    scraper = SCRAPERS[STATE.mkplc](
        headless=not STATE.show_browser,
        path=STATE.folder,
        reconnect=STATE.reconnect,
        timeout=STATE.timeout,
    )
    if STATE.use_cache == CACHE[1]:
        run_search(scraper)

    inspect_pages(scraper)

    process_data(scraper.pages_file(STATE.keyword))


config_container = st.sidebar.container(border=True)

mkplc = config_container.selectbox(
    MARKETPLACE,
    SCRAPERS.keys(),
    key="_mkplc",
    on_change=set_mkplc,
    placeholder="Selecione uma opção",
)

if STATE.mkplc is None:
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

    if STATE.keyword:
        if Path(STATE.folder).is_dir():
            set_cache()
            if cached_links := STATE.cached_links:
                container = st.sidebar.container(border=True)
                container.info(
                    f"Existem **{len(cached_links)}** resultados de busca (links) em cache"
                )
                if container.toggle("Visualizar links em cache", key="show_cache"):
                    show_links()
                container.radio(
                    "Pesquisa de links",
                    options=CACHE,
                    index=0 if CONFIG[CACHE[0]] else 1,
                    key="_use_cache",
                    on_change=use_cache,
                )
            else:
                STATE.use_cache = CACHE[1]

            with st.sidebar:
                with st.form("config", border=False):
                    with st.expander("CONFIGURAÇÕES", expanded=False):
                        st.number_input(
                            RECONNECT,
                            min_value=2,
                            key="reconnect",
                            value=CONFIG.get(KEYS["reconnect"], 5),
                        )
                        st.number_input(
                            TIMEOUT,
                            min_value=1,
                            key="timeout",
                            value=CONFIG.get(KEYS["timeout"], 2),
                        )
                        st.number_input(
                            MAX_SEARCH,
                            min_value=1,
                            value=CONFIG.get(KEYS["max_search"], 10),
                            key="max_search",
                            disabled=(STATE.use_cache == CACHE[0]),
                        )
                        st.number_input(
                            MAX_PAGES,
                            min_value=1,
                            value=CONFIG.get(KEYS["max_pages"], 50),
                            key="max_pages",
                        )
                        st.checkbox(
                            SHUFFLE,
                            key="shuffle",
                            value=CONFIG.get(KEYS["shuffle"], False),
                        )
                        st.checkbox(
                            SCREENSHOT,
                            key="screenshot",
                            value=CONFIG.get(KEYS["screenshot"], False),
                        )
                        st.toggle(
                            SHOW_BROWSER,
                            key="show_browser",
                            value=CONFIG.get(KEYS["show_browser"], False),
                        )
                    st.form_submit_button(START, on_click=run, use_container_width=True)

        else:
            st.sidebar.error("Insira um caminho válido!", icon="🚨")
    else:
        st.sidebar.warning("Insira uma palavra-chave não vazia!", icon="⚠️")
