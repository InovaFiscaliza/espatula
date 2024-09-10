from dataclasses import dataclass
from datetime import datetime

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
    turnstile: bool = True

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
        url = product_tag.select_one("a.product-summary")
        url = url.get("href") if url else None

        nome = product_tag.select_one("h2.productName")
        nome = nome.text.strip() if nome else None

        imagem = product_tag.select_one("img.product-summary")
        imagem = imagem.get("src") if imagem else None

        preço_original = product_tag.select_one("span.listPrice")
        preço_original = preço_original.text.strip() if preço_original else None

        preço = product_tag.select_one("span.spotPriceValue")
        preço = preço.text.strip() if preço else None

        url = self.url + url if url else None
        return {
            "nome": nome,
            "preço_original": preço_original,
            "preço": preço,
            "imagem": imagem,
            "url": url,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, driver, keyword: str):
        soup = BeautifulSoup(driver.get_page_source(), "html.parser")
        results = {}
        for div in soup.select("div.galleryItem"):
            if product_data := self.extract_search_data(div):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def extract_item_data(self, driver):
        soup = BeautifulSoup(driver.get_page_source(), "html.parser")
        categoria = soup.select("span.breadcrumb")
        categoria = "|".join(i.text.strip() for i in categoria if i.text.strip() != "")

        marca = soup.select_one("span.productBrandName")
        marca = marca.text.strip() if marca else None

        vendedor = soup.select_one("span.carrefourSeller")
        vendedor = vendedor.text.strip() if vendedor else None

        desconto = soup.select_one("span.PriceSavings")
        desconto = desconto.text.strip() if desconto else None

        cod_produto = soup.select_one("span.product-identifier__value")
        cod_produto = cod_produto.text.strip() if cod_produto else None

        descrição = soup.select_one("td.ItemSpecifications")
        descrição = descrição.get("data-specification") if descrição else None

        imagens = soup.select("img.thumbImg")
        imagens = [i.get("src") for i in imagens if i.get("src")]

        certificado, ean, modelo = None, None, None
        if características := self.parse_tables(soup):
            certificado = self.extrair_certificado(características)
            ean = self.extrair_ean(características)
            modelo = características.get("Modelo")

        return {
            "categoria": categoria,
            "marca": marca,
            "modelo": modelo,
            "vendedor": vendedor,
            "desconto": desconto,
            "product_id": cod_produto,
            "url": driver.get_current_url(),
            "certificado": certificado,
            "ean_gtin": ean,
            "descrição": descrição,
            "características": características,
            "imagens": imagens,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def parse_tables(self, soup):
        # Extrai o conteúdo da tabela com dados do produto e transforma em um dict
        table_data = {}
        table = soup.select_one("div.table_main_container")
        if table:
            for row in table.select("tr"):
                cols = row.select("th")
                if len(cols) == 2:
                    table_data[cols[0].text.strip()] = cols[1].text.strip()
        return table_data
