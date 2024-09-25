from fastcore.xtras import Path
import streamlit as st

from config import (
    COLUNAS,
    LOGOS,
    TITLE,
    FOLDER,
    CLOUD,
    CACHE,
    KEYS,
    MAX_PAGES,
    MAX_SEARCH,
    SHUFFLE,
    SCREENSHOT,
    RECONNECT,
    TIMEOUT,
)
from callbacks import _set_folder, _set_cloud
from data_processing import update_processed_pages


def display_df(state, df, output_df_key):
    # The index in df should be in the default numeric order
    state[f"df_{output_df_key}"] = st.data_editor(
        df,
        height=720 if len(df) >= 20 else None,
        use_container_width=True,
        column_order=COLUNAS.keys(),
        column_config={
            "url": st.column_config.LinkColumn(
                "URL",
                width=None,
                display_text="Link",
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
                "Homologação Compulsória (Sim/Não)",
                width=None,
                help="📌Classificador Binário - Homologação Compulsória (Sim/Não)",
                disabled=False,
                required=True,
            ),
            "probabilidade": st.column_config.ProgressColumn(
                "Homologação Compulsória (%)",
                format="%.2f%%",
                min_value=0,
                max_value=100,
                help="📌Classificador Binário - Probabilidade de Homologação Compulsória",
            ),
        },
        hide_index=True,
        disabled=False,
        on_change=update_processed_pages,
        key=output_df_key,
        args=(
            state,
            output_df_key,
        ),
    )
    return state[output_df_key]


def show_results(state, container):
    with container.expander(
        "Classificador Binário: Homologação Compulsória pela Anatel",
        icon="🔥",
    ):
        rows = state.processed_pages["passível?"]
        display_df(
            state,
            state.processed_pages.loc[rows],
            output_df_key="positive",
        )
    with container.expander(
        "Classificador Binário: Não é produto de Telecomunicações", icon="🗑️"
    ):
        display_df(
            state,
            state.processed_pages.loc[~rows],
            output_df_key="negative",
        )
    st.info(
        "**É possível alterar a classificação (classe - `True/False`) de cada registro, caso incorreta!**",
        icon="✍🏽",
    )
    columns = st.columns(4, vertical_alignment="top")

    with columns[0]:
        with st.popover("📜Dados do Anúncio"):
            st.markdown("""
                        * Os registros que compõem a primeira tabela serão salvos em um arquivo Excel e sincronizados com o [OneDrive DataHub - POST/Regulatron](https://anatel365.sharepoint.com/sites/InovaFiscaliza/DataHub%20%20POST/Regulatron).
                        * Todos os dados submetidos são periodicamente mesclados numa base única, que será disponibilizada em [OneDrive DataHub - GET/Regulatron](https://anatel365.sharepoint.com/sites/InovaFiscaliza/DataHub%20%20GET/Regulatron).
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
                        * Apesar de não garantir a validade da homologação, uma taxa de 100% é uma característica útil na análise do anúncios.
                        
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
            min_value=2,
            key="reconnect",
            help="Tempo de espera para o driver se conectar ao navegador (seg)",
            value=config.get(KEYS["reconnect"], 5),
        )
        st.number_input(
            TIMEOUT,
            min_value=1,
            key="timeout",
            help="Tempo de espera para carregar os elementos da página (seg)",
            value=config.get(KEYS["timeout"], 2),
        )
