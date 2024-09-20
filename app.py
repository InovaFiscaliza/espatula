import os
import time
import json

import streamlit as st
import pandas as pd
from fastcore.xtras import Path
from gradio_client import Client, handle_file

from config import (
    BASE,
    CACHE,
    COLUNAS,
    CLOUD,
    FOLDER,
    KEYWORD,
    LOGOS,
    MARKETPLACE,
    MAX_PAGES,
    MAX_SEARCH,
    KEYS,
    START,
    RECONNECT,
    SCREENSHOT,
    SHUFFLE,
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
    if not (folder := (Path(__file__).parent / "data").resolve()).is_dir():
        folder.mkdir(parents=True, exist_ok=True)
    STATE[key] = rf"{folder}"

if (key := "cloud") not in STATE:
    if not (cloud := CONFIG.get(KEYS[key])):
        if onedrive := os.environ.get("OneDriveCommercial", ""):
            if (
                onedrive := (Path(onedrive) / "DataHub - POST/Regulatron").resolve()
            ).is_dir():
                cloud = rf"{onedrive}"
            elif (
                onedrive := (
                    Path.home() / "ANATEL/InovaFiscaliza - DataHub - POST/Regulatron"
                ).resolve()
            ).is_dir():
                cloud = rf"{onedrive}"
    STATE[key] = cloud


if "cached_links" not in STATE:
    STATE.cached_links = {}

if "show_cache" not in STATE:
    STATE.show_cache = True

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
def set_cloud():
    # Callback function to save the keyword selection to Session State
    if STATE._cloud is not None and Path(STATE._cloud).is_dir():
        STATE.cloud = STATE._cloud


@st.fragment
def set_cached_links():
    # Callback function to save the keyword selection to Session State
    scraper = SCRAPERS[STATE.mkplc](path=STATE.folder)
    STATE.cached_links = scraper.get_links(STATE.keyword)


@st.fragment
def set_cached_pages():
    scraper = SCRAPERS[STATE.mkplc](path=STATE.folder)
    STATE.cached_pages = scraper.get_pages(STATE.keyword)


def request_table(json_path: Path) -> pd.DataFrame:
    client = Client("ronaldokun/ecomproc")
    result = client.predict(
        json_file=handle_file(str(json_path)),
        api_name="/process_to_table",
    )
    df = pd.DataFrame(result["data"], columns=result["headers"], dtype="string").astype(
        COLUNAS
    )
    df["marketplace"] = STATE.mkplc

    return df


def save_table():
    scraper = SCRAPERS[STATE.mkplc](path=STATE.folder)
    try:
        if (df := STATE.processed_pages) is not None:
            output_table = scraper.pages_file(STATE.keyword).with_suffix(".xlsx")
            df["marketplace"] = STATE.mkplc
            df.to_excel(output_table, index=False)
    except Exception as e:
        st.error(f"Erro ao salvar os dados processados: {e}")


def process_data(pages_file: Path):
    df = request_table(pages_file)
    df["probabilidade"] *= 100
    df.sort_values(
        by=["passível?", "probabilidade"],
        ascending=False,
        inplace=True,
        ignore_index=True,
    )
    df.sort_values(
        by=["modelo_score", "nome_score"],
        ascending=False,
        inplace=True,
        ignore_index=True,
    )
    STATE.processed_pages = df
    save_table()


@st.fragment
def set_processed_pages():
    scraper = SCRAPERS[STATE.mkplc](path=STATE.folder)
    json_file = scraper.pages_file(STATE.keyword)
    excel_file = json_file.with_suffix(".xlsx")

    if excel_file.is_file():
        try:
            df = pd.read_excel(excel_file, dtype="string").astype(COLUNAS)
            df.sort_values(
                by=["passível?", "probabilidade"],
                ascending=False,
                inplace=True,
                ignore_index=True,
            )
            df.sort_values(
                by=["modelo_score", "nome_score"],
                ascending=False,
                inplace=True,
                ignore_index=True,
            )
            STATE.processed_pages = df
        except Exception:
            process_data(json_file)
    elif json_file.is_file():
        process_data(json_file)

    if STATE.cached_pages is not None and STATE.processed_pages is not None:
        if set(list(STATE.cached_pages.keys())).difference(
            STATE.processed_pages["url"].to_list()
        ):
            process_data(json_file)


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
        with st.container(border=False):
            format_df(STATE.processed_pages)


def update_processed_pages(output_df_key):
    edited = STATE[output_df_key]["edited_rows"]
    for index, row in edited.items():
        for column, value in row.items():
            STATE.processed_pages.loc[index, column] = str(value)


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


def display_df(df, column_order, output_df_key):
    st.data_editor(
        df,
        height=720 if len(df) >= 20 else None,
        use_container_width=True,
        column_order=column_order,
        column_config={
            "url": st.column_config.LinkColumn(
                "URL",
                width=None,
                display_text="Link",
                help="Dados do Anúncio",
                disabled=True,
            ),
            "imagem": st.column_config.ImageColumn(
                "Imagem", width="small", help="Dados do Anúncio"
            ),
            "nome": st.column_config.TextColumn(
                "Título", width=None, help="Dados do Anúncio", disabled=True
            ),
            "fabricante": st.column_config.TextColumn(
                "Fabricante", width=None, help="Dados do Anúncio", disabled=True
            ),
            "modelo": st.column_config.TextColumn(
                "Modelo", width=None, help="Dados do Anúncio", disabled=True
            ),
            "certificado": st.column_config.TextColumn(
                "Certificado", width=None, help="Dados do Anúncio", disabled=True
            ),
            "ean_gtin": st.column_config.TextColumn(
                "EAN/GTIN", width=None, help="Dados do Anúncio", disabled=True
            ),
            "subcategoria": st.column_config.TextColumn(
                "Categoria", width=None, help="Dados do Anúncio", disabled=True
            ),
            "nome_sch": st.column_config.SelectboxColumn(
                "SCH - Nome Comercial",
                width=None,
                help="Dados de Certificação - SCH",
                disabled=True,
            ),
            "fabricante_sch": st.column_config.SelectboxColumn(
                "SCH - Fabricante",
                width=None,
                help="Dados de Certificação - SCH",
                disabled=True,
            ),
            "modelo_sch": st.column_config.SelectboxColumn(
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
                "Classe (True/False)",
                width=None,
                help="Classificador - Homologação Compulsória",
                disabled=False,
            ),
            "probabilidade": st.column_config.ProgressColumn(
                "Classe (Probabilidade)",
                format="%.2f%%",
                min_value=0,
                max_value=100,
                help="Classificador - Homologação Compulsória",
            ),
        },
        hide_index=True,
        disabled=False,
        on_change=update_processed_pages,
        key=output_df_key,
        args=(output_df_key,),
    )


def format_df(df):
    df = STATE.processed_pages
    with st.expander(
        "Dados Positivos - Homologação Compulsória pela Anatel", icon="🔥"
    ):
        display_df(
            df.loc[df["passível?"] == "True"],
            COLUNAS.keys(),
            output_df_key="df_positive",
        )
    with st.expander("Dados Negativos - Não Relevante (_Serão descartados_)", icon="🗑️"):
        display_df(
            df.loc[df["passível?"] == "False"],
            COLUNAS.keys(),
            output_df_key="df_negative",
        )

    st.info("É possível alterar a classificação, caso incorreta!", icon="✍🏽")
    columns = st.columns(4, vertical_alignment="top")

    with columns[0]:
        with st.popover("Dados do Anúncio"):
            st.markdown("""
                        * Os registros que compõem a primeira tabela serão salvos em um arquivo Excel e posteriormente sincronizados com o [OneDrive DataHub - POST/Regulatron](https://anatel365.sharepoint.com/sites/InovaFiscaliza/DataHub%20%20POST/Regulatron).
                        * Todos os dados brutos do anúncio serão salvos, as colunas acima são apenas um recorte.
                        """)

    with columns[1]:
        with st.popover("🗃️Dados de Certificação - SCH"):
            st.markdown("""
                        * Caso o anúncio contenha um nº de homologação, este é verificado e, caso válido, as colunas __Fabricante__, __Modelo__, __Tipo__ e __Nome Comercial__ são preenchidas com os dados do certificado.
                        * Os dados de Certificação - SCH são extraídos do portal de dados abertos: [link](https://dados.gov.br/dados/conjuntos-dados/produtos-de-telecomunicacoes-homologados-pela-anatel)
                        """)
    with columns[2]:
        with st.popover("🖇️Comparação de Strings - Anúncio x SCH"):
            st.markdown("""
                        * Para os registros com dados do certificado inseridos, as seguintes colunas correspondentes são comparadas:
                            * Título do anúncio x SCH - Nome Comercial
                            * Modelo do anúncio x SCH - Modelo
                        * A comparação é feita calculando-se a sobreposição textual (_fuzzy string matching - Distância de Levenshtein_).
                        * A taxa de sobreposição é mostrada nas colunas __Título x SCH - Nome Comercial (%)__ e __Modelo x SCH - Modelo (%)__.
                        * Uma taxa de sobreposição de `100%` indica que um dado está contido no outro.
                        * Este é um indicativo de correspondência entre os dados do anúncio e o certificado apontado.
                        * Apesar de não garantir a validade da homologação, uma taxa de 100% é mais um artifício a favor da classificação.
                        
                        """)
    with columns[3]:
        with st.popover("📌Classificador Binário"):
            st.link_button(
                "Mais informações",
                url="https://anatel365.sharepoint.com/sites/InovaFiscaliza/SitePages/Regulatron--Experimento-de-classifica%C3%A7%C3%A3o-3.aspx",
                use_container_width=True,
            )

            st.markdown("""
                    * Classe :green[True] ✅ - O produto foi classificado como **Positivo**, i.e. **possui homologação compulsória**.
                        * 👉🏽Para alterar de :green[True] para :red[False], basta desmarcar o checkbox na coluna `Classe` da primeira tabela. A `Classe` será alterada para :red[False] e o registro migrado para a segunda tabela.
                    * Classe :red[False] 🔲 - O produto  foi classificado como **Negativo**, i.e. **NÃO possui homologação compulsória**.
                        * 👉🏽Para alterar de :red[False] para :green[True], basta marcar o checkbox na coluna `Classe` da segunda tabela. A `Classe` será alterada para :green[True] e o registro migrado para a primeira tabela.

                    """)


def run():
    save_config()
    STATE.show_cache = False
    scraper = SCRAPERS[STATE.mkplc](
        path=STATE.folder,
        reconnect=STATE.reconnect,
        timeout=STATE.timeout,
    )
    if STATE.use_cache == CACHE[1]:
        run_search(scraper)
    inspect_pages(scraper)
    process_data(scraper.pages_file(STATE.keyword))
    st.snow()
    st.success("Processamento dos dados finalizado!", icon="🎉")
    show_processed_pages()


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
            * 🤖 Automação da busca e navegação para de produtos e navegação  páginas.
            * 🖼️ Captura de página completa anúncios em pdf otimizado.
            * 🗄️ Mesclagem dos dados de certificação na base da Anatel com fuzzy search.
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
