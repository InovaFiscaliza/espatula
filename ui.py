import base64
import uuid


from fastcore.xtras import Path
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer


from config import (
    COLUNAS,
    CLOUD_PATH,
    LOGOS,
    TITLE,
    FOLDER,
    CLOUD,
    CACHE,
    KEYS,
    MAX_PAGES,
    MAX_SEARCH,
    SHUFFLE,
    RECONNECT,
    TIMEOUT,
)
from callbacks import _set_folder, _set_cloud
from data_processing import update_processed_pages


def display_df(state, df, output_df_key):
    # Generate a unique key for the edited rows state to avoid conflicts
    edited_key = f"{output_df_key}_{uuid.uuid4()}"
    # The index in df should be in the default numeric order
    df.loc[:, ["pdf"]] = f"{CLOUD_PATH}/" + df.loc[:, "screenshot"].astype("string")
    colunas = list(COLUNAS.keys())
    colunas.insert(1, "pdf")
    state[output_df_key] = st.data_editor(
        df,
        height=720 if len(df) >= 20 else None,
        use_container_width=True,
        column_order=colunas,
        column_config={
            "url": st.column_config.LinkColumn(
                "URL",
                width=None,
                display_text="Link",
                help="📜Dados do Anúncio",
                disabled=True,
            ),
            "pdf": st.column_config.LinkColumn(
                "PDF",
                width=None,
                display_text="PDF",
                help="📜Dados do Anúncio",
                disabled=True,
            ),
            "imagem": st.column_config.ImageColumn(
                "Imagem", width="small", help="📜Dados do Anúncio"
            ),
            "nome": st.column_config.TextColumn(
                "Título", width=None, help="📜Dados do Anúncio", disabled=True
            ),
            "fabricante": st.column_config.TextColumn(
                "Fabricante", width=None, help="📜Dados do Anúncio", disabled=True
            ),
            "modelo": st.column_config.TextColumn(
                "Modelo", width=None, help="📜Dados do Anúncio", disabled=True
            ),
            "certificado": st.column_config.TextColumn(
                "Certificado", width=None, help="📜Dados do Anúncio", disabled=True
            ),
            "ean_gtin": st.column_config.TextColumn(
                "EAN/GTIN", width=None, help="📜Dados do Anúncio", disabled=True
            ),
            "subcategoria": st.column_config.TextColumn(
                "Categoria", width=None, help="📜Dados do Anúncio", disabled=True
            ),
            "nome_sch": st.column_config.SelectboxColumn(
                "SCH - Nome Comercial",
                width=None,
                help="🗃️Dados de Certificação - SCH",
                disabled=True,
            ),
            "fabricante_sch": st.column_config.SelectboxColumn(
                "SCH - Fabricante",
                width=None,
                help="🗃️Dados de Certificação - SCH",
                disabled=True,
            ),
            "modelo_sch": st.column_config.SelectboxColumn(
                "SCH - Modelo",
                width=None,
                help="🗃️Dados de Certificação - SCH",
                disabled=True,
            ),
            "tipo_sch": st.column_config.SelectboxColumn(
                "SCH - Tipo de Produto",
                width=None,
                help="🗃️Dados de Certificação - SCH",
                disabled=True,
            ),
            "modelo_score": st.column_config.ProgressColumn(
                "Modelo x SCH - Modelo (%)",
                width=None,
                help="🖇️Comparação de Strings - Anúncio x SCH",
            ),
            "nome_score": st.column_config.ProgressColumn(
                "Título x SCH - Nome Comercial (%)",
                width=None,
                help="🖇️Comparação de Strings - Anúncio x SCH",
            ),
            "passível?": st.column_config.CheckboxColumn(
                "Positivo/Negativo",
                width=None,
                help="📌Classe do Produto considerando a probabilidade retornada pelo modelo",
                disabled=False,
                required=True,
            ),
            "probabilidade": st.column_config.ProgressColumn(
                "Homologação Compulsória (%)",
                format="%.2f%%",
                min_value=0,
                max_value=100,
                help="📌Classificador - Probabilidade de Homologação Compulsória",
            ),
        },
        hide_index=True,
        disabled=False,
        on_change=update_processed_pages,
        key=edited_key,
        args=(state, output_df_key, edited_key),
    )
    return state[output_df_key]


def pdf_container(pdf_path):
    base64_pdf = base64.b64encode(Path(pdf_path).read_bytes()).decode("utf-8")
    return pdf_viewer(input=base64_pdf, width="100%")


def show_results(state):
    columns = st.columns(4, gap="small", vertical_alignment="top")

    with columns[0]:
        with st.popover("📜Dados do Anúncio"):
            st.markdown("""
                        * Os registros que compõem a primeira tabela serão salvos em um arquivo Excel e sincronizados com o [OneDrive DataHub - POST/Regulatron](https://anatel365.sharepoint.com/sites/InovaFiscaliza/DataHub%20%20POST/Regulatron).
                        * Todos os dados submetidos são periodicamente mesclados numa base única, que será disponibilizada em [OneDrive DataHub - GET/Regulatron](https://anatel365.sharepoint.com/sites/InovaFiscaliza/DataHub%20%20GET/Regulatron).
                        * :red[Todos os dados brutos do anúncio serão salvos, as colunas acima são apenas um recorte.]
                        """)
    with columns[1]:
        with st.popover("🗃️Dados de Certificação - SCH"):
            st.markdown("""
                        * Caso o anúncio contenha um nº de homologação, este é verificado e, caso válido, as colunas __Fabricante__, __Modelo__, __Tipo__ e __Nome Comercial__ são preenchidas com os dados do certificado.
                        * :red[Os dados de Certificação - SCH são extraídos do portal de dados abertos: [link](https://dados.gov.br/dados/conjuntos-dados/produtos-de-telecomunicacoes-homologados-pela-anatel)]
                        """)
    with columns[2]:
        with st.popover("🖇️Comparação de Strings - Anúncio x SCH"):
            st.markdown("""
                        * Para os registros contendo certificado válido, são comparados:
                            * Título do anúncio x SCH - Nome Comercial
                            * Modelo do anúncio x SCH - Modelo
                        * A comparação é feita calculando-se a % de sobreposição textual
                            * (_fuzzy string matching - Distância de Levenshtein_).
                        * _Uma taxa de `100%` indica que um dado está contido no outro._
                            * :red[Isso não garante a validade da homologação, somente é um indicativo de correspondência dos dados.]                        
                        """)
    with columns[3]:
        with st.popover("📌Classificador Binário"):
            st.link_button(
                "Mais Informações 🧐",
                url="https://anatel365.sharepoint.com/sites/InovaFiscaliza/SitePages/Regulatron--Experimento-de-classifica%C3%A7%C3%A3o-3.aspx",
                use_container_width=True,
            )

            st.markdown("""
                    * :green[Positivo] ✅ - O modelo retornou probabilidade **acima** de `50%`, portanto o produto foi considerado de **Homologação Compulsória**.
                        * 👉🏽Para alterar de :green[Positivo] para :red[Negativo], basta *desmarcar* o checkbox da linha correspondente na última coluna à direita `Positivo/Negativo`
                        * *O registro será migrado para a segunda tabela.*
                    * :red[Negativo] 🔲 - O modelo retornou probabilidade **abaixo** de `50%`, portanto o produto **não** foi considerado de **Homologação Compulsória**.
                        * 👉🏽Para alterar de :red[Negativo] para :green[Positivo], basta *selecionar* o checkbox da linha correspondente na última coluna à direita `Positivo/Negativo`
                        * *O registro será migrado para a primeira tabela.*

                    """)

    with st.expander(
        "Classificação: :green[Positivo ✅ - Homologação Compulsória pela Anatel]",
        icon="🔥",
        expanded=True,
    ):
        rows = state.processed_pages["passível?"]
        display_df(
            state,
            state.processed_pages.loc[rows],
            output_df_key="df_positive",
        )

    with st.expander(
        "Classificação: :red[Negativo🔲 - Não é produto de Telecomunicações]", icon="🗑️"
    ):
        display_df(
            state,
            state.processed_pages.loc[~rows],
            output_df_key="df_negative",
        )
    st.info(
        "É possível alterar a Classe, caso incorreta, clicando na coluna _Positivo/Negativo_!",
        icon="✍🏽",
    )


def presentation_page():
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
    st.sidebar.info(
        "Por favor, selecione uma plataforma para iniciar a pesquisa.",
        icon="👆🏾",
    )


def is_folders_ok(state):
    check = True
    if state.folder is None or not Path(state.folder).is_dir():
        st.error("Insira um caminho válido para a pasta de trabalho local!", icon="🚨")
        st.text_input(
            FOLDER,
            key="_folder",
            on_change=_set_folder,
        )
        check = False

    if state.cloud is None or not Path(state.cloud).is_dir():
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
            on_change=_set_cloud,
        )
        check = False

    return check


def get_cached_info(state):
    cache_info = ""
    if cached_links := state.cached_links:
        cache_info += f" * **{len(cached_links)}** resultados de busca"
    else:
        cache_info += " * :red[0] resultados de busca"
        state.use_cache = CACHE[1]
    if cached_pages := state.cached_pages:
        cache_info += f"\n* **{len(cached_pages)}** anúncios completos"
    else:
        cache_info += "\n * :red[0] anúncios completos"
    if (processed_pages := state.processed_pages) is not None:
        cache_info += f"\n* **{len(processed_pages)}** anúncios processados"
    else:
        cache_info += "\n * :red[0] anúncios processados"
    return any([cached_links, cached_pages, processed_pages is not None]), cache_info


def get_params(state, config):
    with st.expander("PARÂMETROS - NAVEGAÇÃO", expanded=False):
        st.number_input(
            MAX_SEARCH,
            min_value=1,
            value=config.get(KEYS["max_search"], 10),
            key="max_search",
            help="Nº máximo de páginas de busca a navegar, a cada nova pesquisa",
            disabled=(state.use_cache == CACHE[0]),
        )
        st.number_input(
            MAX_PAGES,
            min_value=1,
            help="Nº máximo de produtos a capturar, dentre os links coletados",
            value=config.get(KEYS["max_pages"], 50),
            key="max_pages",
        )
        st.checkbox(
            SHUFFLE,
            key="shuffle",
            help="Seleciona aleatoriamente os links para navegação de páginas",
            value=config.get(KEYS["shuffle"], True),
        )
        # st.checkbox(
        #     SCREENSHOT,
        #     key="screenshot",
        #     help="Captura a página completa do anúncio em pdf otimizado",
        #     value=config.get(KEYS["screenshot"], True),
        # )

    with st.expander("CONFIGURAÇÕES - BROWSER", expanded=False):
        st.number_input(
            RECONNECT,
            min_value=1.0,
            max_value=60.0,
            step=0.1,
            key="reconnect",
            help="Tempo de espera para o driver se conectar ao navegador (seg)",
            value=float(config.get(KEYS["reconnect"], 5)),
        )
        st.number_input(
            TIMEOUT,
            min_value=0.1,
            max_value=60.0,
            step=0.1,
            key="timeout",
            help="Tempo de espera para carregar os elementos da página (seg)",
            value=float(config.get(KEYS["timeout"], 1)),
        )


# file_path = "C:/streamlit/todo_app/assets/todo_guide.pdf"
# with open(file_path, "rb") as f:  # pdf file is binary, use rb
#     bytes_data = f.read()
# uploaded_file = io.BytesIO(bytes_data)  # this one


# from streamlit_pdf_viewer import pdf_viewer

# pdf_path = "F:/Downloads/mm-bradley-terry-1079120141.pdf"
# with open(pdf_path, "rb") as pdf_ref:
#     bytes_data = pdf_ref.read()
# pdf_viewer(input=bytes_data, width=700)


# # Create a dataframe
# df = pd.DataFrame({"col1": ["Item1", "Item2", "Item3", "Item4"], "col2": [1, 2, 3, 4]})

# # Display the dataframe with multi-row selection enabled
# event = st.dataframe(
#     df,
#     on_select="rerun",
#     selection_mode="multi-row",
# )

# # Check if any rows are selected
# if event.selection:
#     # Get the selected rows
#     selected_rows = df.iloc[event.selection.rows]

#     # Display the selected rows in a container
#     with st.container():
#         st.header("Selected rows")
#         st.dataframe(selected_rows)
