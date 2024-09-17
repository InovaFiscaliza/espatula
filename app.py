import time
import json

import streamlit as st
import pandas as pd
from fastcore.xtras import Path
from gradio_client import Client, handle_file

from config import (
    BASE,
    CACHE,
    FOLDER,
    SHOW_BROWSER,
    KEYWORD,
    LOGOS,
    MARKETPLACE,
    MAX_PAGES,
    MAX_SEARCH,
    START,
    RECONNECT,
    SCREENSHOT,
    SHUFFLE,
    TIMEOUT,
    TITLE,
    USER_PROFILE,
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
    "passível?": "category",
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
    "load_user_profile": USER_PROFILE,
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
if "cached_links" not in STATE:
    STATE.cached_links = {}

if "show_cache" not in STATE:
    STATE.show_cache = False

if "cached_pages" not in STATE:
    STATE.cached_pages = None

if "processed_pages" not in STATE:
    STATE.processed_pages = None

if (key := "use_cache") not in STATE:
    STATE[key] = CACHE[0] if CONFIG.get(KEYS[key]) else CACHE[1]


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
def set_cached_links():
    # Callback function to save the keyword selection to Session State
    scraper = SCRAPERS[STATE.mkplc](path=STATE.folder)
    STATE.cached_links = scraper.get_links(STATE.keyword)


@st.fragment
def set_cached_pages():
    scraper = SCRAPERS[STATE.mkplc](path=STATE.folder)
    STATE.cached_pages = scraper.get_pages(STATE.keyword)


@st.fragment
def set_processed_pages():
    scraper = SCRAPERS[STATE.mkplc](path=STATE.folder)
    if (excel_file := scraper.pages_file(STATE.keyword).with_suffix(".xlsx")).is_file():
        STATE.processed_pages = pd.read_excel(excel_file, dtype="string").astype(
            COLUNAS
        )
    else:
        STATE.processed_pages = None


@st.fragment
def use_cache():
    # Callback function to save the keyword selection to Session State
    STATE.use_cache = STATE._use_cache


@st.fragment
def show_links():
    if STATE.cached_links:
        st.json(list(STATE.cached_links.values()), expanded=True)


@st.fragment
def show_pages():
    if STATE.cached_pages is not None:
        st.json(list(STATE.cached_pages.values()), expanded=1)


@st.fragment
def show_processed_pages():
    if STATE.processed_pages is not None:
        format_df(STATE.processed_pages)


def request_table(json_path: Path) -> pd.DataFrame:
    client = Client("ronaldokun/ecomproc")
    result = client.predict(
        json_file=handle_file(str(json_path)),
        api_name="/process_to_table",
    )
    return pd.DataFrame(
        result["data"], columns=result["headers"], dtype="string"
    ).astype(COLUNAS)


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


def format_df(df):
    # Create MultiIndex for columns
    columns = pd.MultiIndex.from_tuples(
        [
            ("Anúncio", "URL"),
            ("Anúncio", "Título"),
            ("Anúncio", "Fabricante"),
            ("Anúncio", "Modelo"),
            ("Anúncio", "Certificado"),
            ("Anúncio", "EAN/GTIN"),
            ("Anúncio", "Categoria"),
            ("SCH", "Nome"),
            ("SCH", "Tipo"),
            ("SCH", "Fabricante"),
            ("SCH", "Modelo"),
            ("Sobreposição de Strings - Anúncio x SCH", "Título - Nome Comercial (%)"),
            ("Sobreposição de Strings - Anúncio x SCH", "Modelo - Nome Comercial (%)"),
            ("Classificador Binário", "Homologação Compulsória"),
            ("Classificador Binário", "Probabilidade"),
        ],
        names=["Origem dos Dados", "Coluna"],
    )

    df_show = df.loc[:, list(COLUNAS.keys())]
    df_show["probabilidade"] *= 100
    df_show.sort_values(by="passível?", ascending=False, inplace=True)
    df_show.sort_values(by="modelo_score", ascending=False, inplace=True)
    # df_show.columns = columns

    return st.data_editor(
        df_show,
        use_container_width=True,
        column_config={
            "url": st.column_config.LinkColumn(
                "URL", width=None, display_text="Link", help="Dados do Anúncio"
            ),
            "nome": st.column_config.TextColumn(
                "Título", width=None, help="Dados do Anúncio"
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
                "SCH - Nome Comercial",
                width=None,
                help="Dados de Certificação - SCH",
                disabled=True,
            ),
            "fabricante_sch": st.column_config.TextColumn(
                "SCH - Fabricante",
                width=None,
                help="Dados de Certificação - SCH",
                disabled=True,
            ),
            "modelo_sch": st.column_config.TextColumn(
                "SCH - Modelo",
                width=None,
                help="Dados de Certificação - SCH",
                disabled=True,
            ),
            "tipo_sch": st.column_config.SelectboxColumn(
                "SCH - Tipo de Produto",
                width=None,
                help="Dados de Certificação - SCH",
                disabled=True,
            ),
            "modelo_score": st.column_config.ProgressColumn(
                "Modelo x SCH - Modelo (%)",
                width=None,
                help="Sobreposição de strings - Anúncio versus SCH",
            ),
            "nome_score": st.column_config.ProgressColumn(
                "Título x SCH - Nome Comercial (%)",
                width=None,
                help="Sobreposição de strings - Anúncio versus SCH",
            ),
            "passível?": st.column_config.CheckboxColumn(
                "Homologação Compulsória (True/False)",
                width=None,
                help="Classificação - Binária",
                disabled=True,
            ),
            "probabilidade": st.column_config.ProgressColumn(
                "Probabilidade",
                format="%.2f%%",
                min_value=0,
                max_value=100,
                help="Classificação - Binária",
            ),
        },
        hide_index=True,
        disabled=False,
        on_change=None,
    )


def save_pages():
    scraper = SCRAPERS[STATE.mkplc](path=STATE.folder)
    try:
        if (df := STATE.cached_pages) is not None:
            output_table = scraper.pages_file(STATE.keyword).with_suffix(".xlsx")
            df.to_excel(output_table, index=False)
    except Exception as e:
        st.error(f"Erro ao salvar os dados processados: {e}")


def process_data(pages_file: Path):
    df = request_table(pages_file)
    st.divider()
    st.snow()
    STATE.processed_pages = df
    save_pages()
    st.success("Processamento dos dados finalizado!", icon="🎉")
    show_pages()


def run():
    save_config()
    STATE.show_cache = False
    scraper = SCRAPERS[STATE.mkplc](
        headless=not STATE.show_browser,
        path=STATE.folder,
        reconnect=STATE.reconnect,
        timeout=STATE.timeout,
        load_user_profile=STATE.load_user_profile,
    )
    if STATE.use_cache == CACHE[1]:
        run_search(scraper)

    inspect_pages(scraper)

    process_data(scraper.pages_file(STATE.keyword))


config_container = st.sidebar.expander(label=BASE, expanded=True)

mkplc = config_container.selectbox(
    MARKETPLACE,
    SCRAPERS.keys(),
    key="_mkplc",
    on_change=set_mkplc,
    placeholder="Selecione uma opção",
)

if STATE.mkplc is None:
    st.title(TITLE)
    columns = st.columns(2)

    columns[0].image(
        LOGOS["Espatula"],
        width=480,
        caption="Espátula raspando dados de E-commerce",
    )
    with columns[1]:
        st.info("""
        Essa aplicação efetua a raspagem de dados _(webscraping)_ de
        produtos para telecomunicações publicados em alguns dos principais _marketplaces_ do país. 
        """)
        st.markdown(
            """
            **Características**:
            * 👨🏻‍💻 Pesquisa por palavra-chave.
            * 👾 Implementação de mecanismos anti-bot sofisticados.
            * 🤖 Automação da busca de links e navegação de páginas.
            * 🗄️ Mesclagem dos dados de certificação na base da Anatel com fuzzy search.
            * 📊 Classificação binária baseada em treinamento nos dados anotados pelos fiscais.
            * 📈 Exportação de dados processados para Excel.
            * 🖼️ Captura de tela completa de anúncios em pdf otimizado.
            """
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
            set_cached_links()
            set_cached_pages()
            set_processed_pages()
            container = st.sidebar.expander("DADOS", expanded=True)
            cache_info = ""
            if cached_links := STATE.cached_links:
                cache_info += f" * **{len(cached_links)}** resultados de busca"
            else:
                STATE.use_cache = CACHE[1]
            if cached_pages := STATE.cached_pages:
                cache_info += f"\n* **{len(cached_pages)}** páginas completas"
            if (processed_pages := STATE.processed_pages) is not None:
                cache_info += f"\n* **{len(processed_pages)}** páginas processadas"
            if not cached_links and not cached_pages:
                container.warning("Não há dados salvos para os parâmetros inseridos")
            else:
                container.info(cache_info)
                if container.toggle("Mostrar Dados Salvos", key="show_cache"):
                    left_tab, right_tab = st.tabs(
                        [
                            "Navegação de Páginas",
                            "Dado Processado",
                        ]
                    )
                    with left_tab:
                        left, right = st.columns([1, 1], vertical_alignment="top")
                        with left:
                            left.subheader("Resultado de Busca")
                            show_links()
                        with right:
                            right.subheader("Página Completa")
                            show_pages()
                    with right_tab:
                        right_tab.subheader("Tabela de Dados Processados")
                        show_processed_pages()
            if cached_links:
                container.radio(
                    "Links para Navegação de Páginas",
                    options=CACHE,
                    index=0 if CONFIG[CACHE[0]] else 1,
                    key="_use_cache",
                    on_change=use_cache,
                )

            with st.sidebar:
                with st.form("config", border=False):
                    with st.expander("PARÂMETROS - PESQUISA", expanded=False):
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
                            value=CONFIG.get(KEYS["shuffle"], True),
                        )
                        st.checkbox(
                            SCREENSHOT,
                            key="screenshot",
                            value=CONFIG.get(KEYS["screenshot"], True),
                        )

                    with st.expander("CONFIGURAÇÕES - BROWSER", expanded=False):
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
                        st.toggle(
                            USER_PROFILE,
                            key="load_user_profile",
                            value=CONFIG.get(KEYS["load_user_profile"], True),
                        )
                        st.toggle(
                            SHOW_BROWSER,
                            key="show_browser",
                            value=CONFIG.get(KEYS["show_browser"], True),
                        )

                    st.form_submit_button(START, on_click=run, use_container_width=True)

        else:
            st.sidebar.error("Insira um caminho válido!", icon="🚨")
    else:
        st.sidebar.warning("Insira uma palavra-chave não vazia!", icon="⚠️")
