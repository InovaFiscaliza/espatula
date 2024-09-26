from dataclasses import dataclass
from datetime import datetime

from markdownify import markdownify as md
from seleniumbase.common.exceptions import (
    NoSuchElementException,
    ElementNotVisibleException,
)

from .base import TIMEZONE, BaseScraper

CATEGORIES = {
    "smartphone": "https://www.carrefour.com.br/celulares-smartphones-e-smartwatches/smartphones#crfint=hm-tlink|celulares-e-smartphones|smartphones|1"
}


@dataclass
class CarrefourScraper(BaseScraper):
    handle_captcha: bool = True

    @property
    def name(self) -> str:
        return "carrefour"

    @property
    def url(self) -> str:
        return "https://www.carrefour.com.br/"

    @property
    def input_field(self) -> str:
        return 'input[placeholder="Pesquise por produtos ou marcas"]'

    @property
    def next_page_button(self) -> str:
        return "li.carrefourbr-carrefour-components-0-x-Pagination_NextButtonContainer>a>div"

    def input_search_params(self, driver, keyword):
        for attempt in range(self.retries):
            try:
                if department := CATEGORIES.get(keyword):
                    driver.uc_open_with_reconnect(
                        department, reconnect_time=self.reconnect
                    )
                self.highlight_element(driver, self.input_field)
                driver.type(self.input_field, keyword + "\n", timeout=self.timeout)
                break
            except (NoSuchElementException, ElementNotVisibleException):
                if attempt < self.retries - 1:  # if it's not the last attempt
                    print(f"Attempt {attempt + 1} failed. Retrying...")
                    driver.sleep(2)  # Wait for 1 second before retrying
                else:
                    print(
                        f"Error: Could not find search input field '{self.input_field}' after {self.retries} attempts"
                    )
                    raise  # Re-raise the last exception

    def extract_search_data(self, product_tag):
        if url := product_tag.select_one('a[class*="product-summary"]'):
            url = self.url + url.get("href")

        if nome := product_tag.select_one('h2[class*="productName"]'):
            nome = nome.get_text().strip()

        if imagem := product_tag.select_one('img[class*="product-summary"]'):
            imagem = imagem.get("src")

        if preço := product_tag.select_one('span[class*="spotPriceValue"]'):
            preço = preço.get_text().strip()

        if not all([url, nome, preço, imagem]):
            return False

        return {
            "nome": nome,
            "preço": preço,
            "imagem": imagem,
            "url": url,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, soup, keyword: str):
        results = {}
        for div in soup.select('div[class*="galleryItem"]'):
            if product_data := self.extract_search_data(div):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def extract_item_data(self, driver):
        soup = driver.get_beautiful_soup()

        def get_selector(selector):
            self.highlight_element(driver, selector)
            return soup.select_one(selector)

        if preço := get_selector('span[class*="currencyContainer"]'):
            preço = preço.get_text().strip()

        if nome := get_selector('h1[class*="productNameContainer"]'):
            nome = nome.get_text().strip()

        categoria = []
        for i in soup.select('span[class*="breadcrumb"]'):
            if hasattr(i, "get_text"):
                if (cat := i.get_text().strip()) not in ["", nome]:
                    categoria.append(cat)
        categoria = "|".join(categoria)

        if not all([categoria, nome, preço]):
            return {}

        if marca := get_selector('span[class*="productBrandName"]'):
            marca = marca.get_text().strip()

        if vendedor := get_selector('span[class*="carrefourSeller"]'):
            vendedor = vendedor.get_text().strip()

        if cod_produto := get_selector('span[class*="product-identifier__value"]'):
            cod_produto = cod_produto.get_text().strip()

        if descrição := get_selector('td[class*="ItemSpecifications"]'):
            descrição = md(descrição.get("data-specification", ""))

        imagens = []
        for img in soup.select('img[class*="thumbImg"]'):
            if i := img.get("src"):
                imagens.append(i)

        certificado, ean, modelo = None, None, None
        if características := self.parse_tables(soup):
            certificado = self.extrair_certificado(características)
            ean = self.extrair_ean(características)
            modelo = características.get("Modelo")
        elif descrição:
            if certificado is None:
                certificado = self.match_certificado(descrição)
            if ean is None:
                ean = self.match_ean(descrição)

        return {
            "avaliações": None,
            "categoria": categoria,
            "certificado": certificado,
            "características": características,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
            "descrição": descrição,
            "ean_gtin": ean,
            "estado": None,
            "estoque": None,
            "imagens": imagens,
            "marca": marca,
            "modelo": modelo,
            "nome": nome,
            "nota": None,
            "preço": preço,
            "product_id": cod_produto,
            "url": driver.get_current_url(),
            "vendas": None,
            "vendedor": vendedor,
        }

    def parse_tables(self, soup):
        # Extrai o conteúdo da tabela com dados do produto e transforma em um dict
        table_data = {}
        if table := soup.select_one('div[class*="table_main_container"]'):
            for row in table.select("tr"):
                cols = row.select("th")
                if len(cols) == 2:
                    table_data[cols[0].get_text().strip()] = cols[1].get_text().strip()
        return table_data
