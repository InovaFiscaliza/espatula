from collections import defaultdict

import streamlit as st

from config import SCRAPERS


if "plataforma" not in st.session_state:
    st.session_state.plataforma = "-"
if "links" not in st.session_state:
    st.session_state.links = defaultdict(set)

if "keyword" not in st.session_state:
    st.session_state.keyword = "smartphone"

ITERATION = 0

st.set_page_config(
    page_title="Espátula",
    page_icon="🛠️",
)


def intro():
    st.write("# Regulatron")
    st.logo("images/logo.svg", icon_image="images/logo.svg")
    st.sidebar.success("Selecione uma plataforma")
    st.info("""
        Essa aplicação efetua primariamente a raspagem de dados _(webscraping)_ de anúncios de
        produtos para telecomunicações publicados em alguns dos principais _marketplaces_ do país. 
        """)
    st.markdown(
        """
    
        * 👨🏻‍💻 Simular o comportamento de um consumidor ao acessar o site.
        * 👾 Generalizar a implementação para outras plataformas
        * 🤖 Tornar a extração independente da categorização de cada marketplace.
        * 🗄️ Cruzar com os registros de produtos homologados da Anatel.
        * 📊 Categorizar e efetuar análises quantitativas
        
        **👈 Para iniciar selecione qual plataforma deseja pesquisar no menu ao lado!**
        """
    )
    st.image("images/espatula.png", caption="Espátula", use_column_width=True)


def search():
    scraper = SCRAPERS[st.session_state.plataforma](
        headless=st.session_state.headless,
    )
    with st.spinner(
        f"Buscando - **{st.session_state.plataforma}** : _{st.session_state.keyword}_ ..."
    ):
        links = scraper.search(
            keyword=st.session_state.keyword,
            max_pages=st.session_state.max_pages,
        )
        st.success(f"Foram encontrados {len(links)} anúncios!")
        st.info(f"Links salvos em {scraper.links_file(st.session_state.keyword)}")
        st.write(list(links.values()))
        st.session_state.links[st.session_state.plataforma].add(
            st.session_state.keyword
        )

    st.divider()


def search_page():
    global ITERATION  # gambiarra para não haver conflitos de chaves nos widgets
    ITERATION += 1
    with st.sidebar:
        with st.expander("**Parâmetros da Busca**", expanded=True):
            st.session_state.keyword = st.text_input(
                "Palavra-chave",
                "smartphone",
                key=f"keyword_{ITERATION}",
            )
            st.session_state.max_pages = st.slider(
                "Número máximo de páginas de busca a navegar",
                1,
                40,
                10,
                key=f"max_pages_{ITERATION}",
            )
        st.button(
            "Buscar links🔎",
            on_click=search,
            use_container_width=True,
            key=f"search_{ITERATION}",
        )


def inspect(screenshot: bool, sample: int, shuffle: bool):
    scraper = SCRAPERS[st.session_state.plataforma](headless=st.session_state.headless)
    with st.spinner("Amostrando páginas dos anúncios..."):
        dados = scraper.inspect_pages(
            keyword=st.session_state.keyword,
            screenshot=screenshot,
            sample=sample,
            shuffle=shuffle,
        )
        st.balloons()
        st.success(f"Os dados foram salvos em {getattr(scraper, "output_file", None)}")
        st.write(list(dados.values()))


def inspect_page():
    global ITERATION
    ITERATION += 1
    with st.sidebar.expander("**Parâmetros da Extração de Dados**", expanded=True):
        st.info(f"Texto Pesquisado: **{st.session_state.keyword}**")
        # Using 'key="sample"' is causing duplicate error
        sample = st.slider(
            "Número máximo de anúncios a extrair",
            1,
            100,
            50,
            key="sample_{ITERATION}",
        )
        shuffle = st.checkbox(
            "**Amostrar páginas aleatoriamente**", key="shuffle_{ITERATION}"
        )
        screenshot = st.checkbox(
            "**Capturar tela do anúncio**", key="screenshot_{ITERATION}"
        )
        st.button(
            "**Navegar páginas dos anúncios🚀**",
            on_click=inspect,
            args=(screenshot, sample, shuffle),
        )
    if st.sidebar.button(
        "**Refazer Pesquisa de Links😵‍💫**",
        use_container_width=True,
    ):
        st.session_state.links[st.session_state.plataforma].discard(
            st.session_state.keyword
        )
        return


def main():
    global ITERATION
    ITERATION += 1
    st.session_state.headless = st.sidebar.checkbox(
        "**Ocultar o navegador**", key=f"headless_{ITERATION}"
    )
    if st.session_state.keyword in st.session_state.links[st.session_state.plataforma]:
        inspect_page()

    else:
        search_page()


page_names_to_funcs = {"—": intro} | {k: main for k in SCRAPERS.keys()}

st.session_state.plataforma = st.sidebar.selectbox(
    "Marketplace", page_names_to_funcs.keys()
)

page_names_to_funcs[st.session_state.plataforma]()
