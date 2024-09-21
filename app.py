import time

import streamlit as st
from fastcore.xtras import Path

from config import (
    BASE,
    CACHE,
    CLOUD,
    FOLDER,
    KEYWORD,
    LOGOS,
    MARKETPLACE,
    MAX_PAGES,
    MAX_SEARCH,
    KEYS,
    START,
    SCRAPERS,
    RECONNECT,
    SCREENSHOT,
    SHUFFLE,
    TIMEOUT,
    TITLE,
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

from ui import show_results

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
                with output.empty():
                    st.write(result)
                progress_bar.progress(
                    int((i * percentage) % 100),
                    text=progress_text,
                )
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
                with output.empty():
                    left, right = st.columns([1, 1], vertical_alignment="top")
                    with left:
                        try:
                            if len(imagem := result.get("imagens", [])) >= 1:
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
    except Exception as e:
        raise e
        st.error(
            f"Erro ao realizar a navegação de páginas: {e}. Verifique sua conexão e tente novamente, se persistir, reporte o erro no Github."
        )


def run():
    save_config(CONFIG)
    STATE.show_cache = False
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
        process_data(scraper.pages_file(STATE.keyword))
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
    st.title(TITLE)
    columns = st.columns(2, vertical_alignment="center")

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
            * 🤖 Automação da busca de produtos e navegação de páginas.
            * 🖼️ Captura de página completa do anúncio em pdf otimizado.
            * 🗄️ Mesclagem dos dados de certificação da base da Anatel e sobreposição de strings.
            * 📊 Classificação binária baseada em treinamento nos dados anotados pelos fiscais.
            * 📈 Exportação de dados processados para Excel.
            """
        )
    st.sidebar.success(
        "Por favor, selecione uma plataforma para iniciar a pesquisa.",
        icon="👆🏾",
    )
else:
    set_folder()
    set_cloud()

    if STATE.folder is None or not Path(STATE.folder).is_dir():
        st.error("Insira um caminho válido para a pasta de trabalho local!", icon="🚨")
        st.text_input(
            FOLDER,
            key="_folder",
            on_change=set_folder,
        )

    elif STATE.cloud is None or not Path(STATE.cloud).is_dir():
        st.error(
            "Insira o caminho para a pasta sincronizada do OneDrive: DataHub - POST/Regulatron !",
            icon="🚨",
        )
        st.markdown("""
                    * Para sincronizar, abra o link [OneDrive DataHub - POST/Regulatron](https://anatel365.sharepoint.com/sites/InovaFiscaliza/DataHub%20%20POST/Regulatron)
                    * Clique em __Add shortcut to OneDrive | Adicionar atalho para OneDrive__
                    """)
        st.image("images/onedrive.png", width=720)
        st.markdown("""
                    * Copie o caminho da pasta sincronizada e cole no campo abaixo
        """)

        st.text_input(
            CLOUD,
            key="_cloud",
            on_change=set_cloud,
        )

    else:
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
            cache_info = ""
            if cached_links := STATE.cached_links:
                cache_info += f" * **{len(cached_links)}** resultados de busca"
            else:
                cache_info += " * :red[0] resultados de busca"
                STATE.use_cache = CACHE[1]
            if cached_pages := STATE.cached_pages:
                cache_info += f"\n* **{len(cached_pages)}** páginas completas"
            else:
                cache_info += "\n * :red[0] páginas completas"
            if (processed_pages := STATE.processed_pages) is not None:
                cache_info += f"\n* **{len(processed_pages)}** páginas processadas"
            else:
                cache_info += "\n * :red[0] páginas processadas"
            if not any([cached_links, cached_pages, processed_pages is not None]):
                container.warning("Não há dados salvos para os parâmetros inseridos")
            else:
                container.info(cache_info)
                if container.toggle("Mostrar Dados Salvos", key="show_cache"):
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
                            value=CONFIG.get(KEYS["reconnect"], 4),
                        )
                        st.number_input(
                            TIMEOUT,
                            min_value=1,
                            key="timeout",
                            value=CONFIG.get(KEYS["timeout"], 1),
                        )

                    st.form_submit_button(START, on_click=run, use_container_width=True)

        else:
            st.sidebar.warning("Insira uma palavra-chave não vazia!", icon="⚠️")
