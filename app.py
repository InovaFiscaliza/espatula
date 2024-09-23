import time

import streamlit as st

from config import (
    BASE,
    CACHE,
    KEYWORD,
    LOGOS,
    MARKETPLACE,
    KEYS,
    START,
    SCRAPERS,
    save_config,
    load_config,
    init_session_state,
)

from callbacks import (
    _set_folder,
    _set_cloud,
    _set_cached_links,
    _set_cached_pages,
    _set_processed_pages,
)

from data_processing import process_data

from ui import (
    show_results,
    presentation_page,
    is_folders_ok,
    get_cached_info,
    get_params,
)

CONFIG = load_config()

st.set_page_config(
    page_title="Regulatron",
    page_icon="🤖",
    layout="wide",
    menu_items={
        "Report a bug": "https://github.com/InovaFiscaliza/Regulatron/issues",
        "About": "*Fiscalização de Produtos Telecomunicações - Anatel*",
    },
)

STATE = st.session_state

init_session_state(STATE, CONFIG)

# Retrieve previous Session State to initialize the widgets
for key in STATE:
    if key != "use_cache":
        STATE["_" + key] = STATE[key]
    if key in KEYS:
        CONFIG[KEYS[key]] = STATE[key]


# Functions to set the STATE Variables
@st.fragment
def set_mkplc():
    # Callback function to save the mkplc selection to Session State
    STATE.mkplc = STATE._mkplc
    img = LOGOS[STATE._mkplc]
    st.logo(img)
    st.image(img, width=270)


@st.fragment
def set_keyword():
    STATE.keyword = STATE._keyword.strip()


@st.fragment
def set_folder():
    _set_folder(STATE)


@st.fragment
def set_cloud():
    _set_cloud(STATE)


@st.fragment
def use_cache():
    STATE.use_cache = STATE._use_cache


@st.fragment
def set_cached_links():
    _set_cached_links(STATE)


@st.fragment
def set_cached_pages():
    _set_cached_pages(STATE)


@st.fragment
def set_processed_pages():
    _set_processed_pages(STATE)


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
        with st.container(border=False):
            show_results(STATE, STATE.processed_pages)


def run_search(scraper):
    try:
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
                percentage = i * percentage
                progress_bar.progress(
                    percentage, text=f"{progress_text} {percentage:.0}%"
                )
                with output.empty():
                    st.write(result)
            time.sleep(1)
            output.empty()
            progress_bar.empty()
    except Exception as e:
        raise e


def inspect_pages(scraper):
    try:
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
                percentage = int(i * percentage)
                progress_bar.progress(
                    percentage, text=f"{progress_text} {percentage:.0}%"
                )
                with output.empty():
                    left, right = st.columns([1, 1], vertical_alignment="top")
                    with left:
                        try:
                            if imagem := result.get("imagens"):
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
            time.sleep(1)
            output.empty()
            progress_bar.empty()
    except Exception as e:
        st.error(
            f"Erro ao realizar a navegação de páginas: {e}. Verifique sua conexão e tente novamente, se persistir, reporte o erro no Github."
        )


def run():
    save_config(CONFIG)
    scraper = SCRAPERS[STATE.mkplc](
        path=STATE.folder,
        reconnect=STATE.reconnect,
        timeout=STATE.timeout,
    )
    try:
        if STATE.use_cache == CACHE[1]:
            run_search(scraper)
    except Exception as e:
        st.error(
            f"Erro ao realizar a busca: {e}. Verifique sua conexão e tente novamente, se persistir, reporte o erro no Github."
        )

    try:
        inspect_pages(scraper)
        process_data(STATE, scraper.pages_file(STATE.keyword))
        st.snow()
        st.success("Processamento dos dados finalizado!", icon="🎉")
        show_processed_pages()
    except Exception as e:
        st.error(
            f"Erro ao realizar a navegação de páginas: {e}. Verifique sua conexão e tente novamente, se persistir, reporte o erro no Github."
        )


config_container = st.sidebar.expander(label=BASE, expanded=True)

mkplc = config_container.selectbox(
    MARKETPLACE,
    SCRAPERS.keys(),
    key="_mkplc",
    on_change=set_mkplc,
    placeholder="Selecione uma opção",
)

if STATE.mkplc is None:
    presentation_page()
else:
    set_folder()
    set_cloud()

    if is_folders_ok(STATE):
        config_container.text_input(
            KEYWORD,
            placeholder="Qual a palavra-chave a pesquisar?",
            key="_keyword",
            on_change=set_keyword,
        )

        if STATE.keyword:
            set_cached_links()
            set_cached_pages()
            set_processed_pages()
            container = st.sidebar.expander("DADOS", expanded=True)
            has_data, cache_info = get_cached_info(STATE)
            if not has_data:
                container.warning("⚠️ Não há dados salvos! ⚠️")
                container.info("👇🏽 Inicie uma Pesquisa 👇🏽")
            else:
                container.success(cache_info)
                left_tab, right_tab = st.tabs(
                    [
                        "Dado Processado",
                        "Dado Bruto",
                    ]
                )
                with right_tab:
                    left, right = st.columns([1, 1], vertical_alignment="top")
                    with left:
                        left.subheader("Resultado de Busca")
                        show_links()
                    with right:
                        right.subheader("Página Completa")
                        show_pages()
                with left_tab:
                    show_processed_pages()
            if STATE.cached_links:
                container.radio(
                    "Links para Navegação de Páginas",
                    options=CACHE,
                    index=0 if CONFIG[CACHE[0]] else 1,
                    key="_use_cache",
                    on_change=use_cache,
                )

            with st.sidebar:
                with st.form("config", border=False):
                    get_params(STATE, CONFIG)
                    st.form_submit_button(START, on_click=run, use_container_width=True)

        else:
            st.sidebar.warning("Insira uma palavra-chave não vazia!", icon="⚠️")
