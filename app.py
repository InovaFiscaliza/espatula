import streamlit as st

from espatula.constantes import KEYWORDS
from espatula.spiders import (
    AmazonScraper,
    MercadoLivreScraper,
    MagaluScraper,
    AmericanasScraper,
    CasasBahiaScraper,
    CarrefourScraper,
)

from espatula.spiders.base import FOLDER, TODAY

if "scraper" not in st.session_state:
    st.session_state.scraper = None

SCRAPERS = {
    "Amazon": AmazonScraper,
    "Mercado Livre": MercadoLivreScraper,
    "Magalu": MagaluScraper,
    "Americanas": AmericanasScraper,
    "Casas Bahia": CasasBahiaScraper,
    "Carrefour": CarrefourScraper,
}

st.set_page_config(
    page_title="Espátula",
    page_icon="🛠️",
)


def intro():
    st.write("# Regulatron")
    st.logo("images/logo.svg", icon_image="images/logo.svg")
    st.sidebar.success("Selecione uma plataforma")
    st.markdown(
        """
        Essa aplicação efetua raspagem de dados _(webscraping)_ em anúncios de 
        produtos para telecomunicações publicados em alguns dos principais _marketplaces_ do país, 
        com intuito de possibilitar análises quantitativas e qualitativas acerca dos anúncios.
        
        **👈 Para iniciar selecione qual plataforma deseja pesquisar no menu ao lado!**
        """
    )
    st.image("espatula.png", caption="Espátula", use_column_width=True)


def start_scraping(
    plataforma: str,
    headless: bool,
    keyword: str,
    max_pages: int,
    sample: int,
    screenshot: bool,
):
    scraper = SCRAPERS[plataforma](
        headless=headless,
    )
    scraper.search(
        keyword=keyword,
        max_pages=max_pages,
    )


def main():
    st.info(
        "A raspagem de dados é orientada à busca por termos relacionados aos produtos para telecomunicações"
    )
    st.markdown(
        """
        
        * 🤖 Simular o comportamento de um consumidor ao acessar o site.
        * 👾 Generalizar a implementação para outras plataformas
        * 👨🏻‍💻 Tornar a extração independente da categorização de cada marketplace.
        
        """
    )
    st.divider()
    with st.sidebar:
        headless = st.radio("Mostrar o navegador?", ["Sim", "Não"], index=1)
        headless = headless == "Sim"
        with st.expander("Parâmetros da Busca"):
            keyword = st.text_input("Palavra-chave", "smartphone")
            max_pages = st.number_input(
                "Número máximo de páginas de busca a navegar", 1, 40, 10
            )
        with st.expander("Parâmetros da Extração de Dados"):
            sample = st.number_input("Número máximo de anúncios a extrair", 1, 100, 50)
            screenshot = st.checkbox("Capturar tela do anúncio?")
        kwargs = {
            "plataforma": st.session_state.plataforma,
            "headless": headless,
            "keyword": keyword,
            "max_pages": max_pages,
            "sample": sample,
            "screenshot": screenshot,
        }
        st.button("🚀Iniciar", on_click=start_scraping, kwargs=kwargs)


page_names_to_funcs = {"—": intro} | {k: main for k in SCRAPERS.keys()}

plataforma = st.sidebar.selectbox("Marketplace", page_names_to_funcs.keys())
if st.session_state.scraper is None:
    if plataforma != "—":
        st.session_state.plataforma = plataforma

if plataforma != "-":
    st.session_state.plataforma = plataforma


page_names_to_funcs[plataforma]()
