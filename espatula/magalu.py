import re
from dataclasses import dataclass
from datetime import datetime

from markdownify import markdownify as md
from seleniumbase.common.exceptions import (
    NoSuchElementException,
    ElementNotVisibleException,
)
from .base import TIMEZONE, BaseScraper

CATEGORIES = {
    "smartphone": 'a[href="/busca/smartphone/?from=submit&filters=category---TE"]'
}


@dataclass
class MagaluScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "magalu"

    @property
    def url(self) -> str:
        return "https://www.magazineluiza.com.br"

    @property
    def input_field(self) -> str:
        return 'input[data-testid="input-search"]'

    @property
    def next_page_button(self) -> str:
        return 'button[aria-label="Go to next page"]'

    def extract_search_data(self, produto):
        relative_url = produto.get("href")
        if name := produto.select_one('h2[data-testid="product-title"]'):
            name = name.get_text().strip()
        if evals := produto.select_one('div[data-testid="review"]'):
            evals = evals.get_text().strip()
        if price_lower := produto.select_one('p[data-testid="price-value"]'):
            price_lower = price_lower.get_text().strip()
        if imgs := produto.select_one('img[data-testid="image"]'):
            imgs = imgs.get("src").replace(r"280x210", r"480x480")
        if not all([name, price_lower, imgs]):
            return None
        return {
            "nome": name,
            "preço": price_lower,
            "avaliações": evals,
            "imagem": imgs,
            "url": self.url + relative_url,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, soup, keyword):
        results = {}
        for item in soup.select(
            'a[data-testid="product-card-container"]',
        ):
            if product_data := self.extract_search_data(item):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def parse_tables(self, soup) -> dict:
        # Extrai o conteúdo da tabela com dados do produto e transforma em um dict
        variant_data = {}
        for table in soup.select("table"):
            for row in table.select("tr:has(> td:nth-child(2):last-child)"):
                left = row.select_one("td:nth-of-type(1)")
                right = row.select_one("td:nth-of-type(2)")
                if "Informações complementares" in left.get_text():
                    continue
                if "R$" in left.get_text() or "R$" in right.get_text():
                    continue
                variant_data[left.get_text().strip()] = right.get_text().strip()

        return variant_data

    def extract_item_data(self, driver):
        soup = driver.get_beautiful_soup()

        def get_selector(selector):
            self.highlight_element(driver, selector)
            return soup.select_one(selector)

        categoria = ""
        if categoria_div := get_selector("div[data-testid=breadcrumb-container]"):
            for i in categoria_div.select('a[data-testid="breadcrumb-item"]'):
                if hasattr(i, "get_text") and i.get_text().strip():
                    categoria += "|" + i.get_text().strip()

        if nome := get_selector('h1[data-testid="heading-product-title"]'):
            nome = nome.get_text().strip()

        preço = None
        if preço_div := get_selector('div[data-testid="mod-productprice"]'):
            if preço := preço_div.select_one('p[data-testid="price-value"]'):
                preço = (
                    preço.get_text()
                    .strip()
                    .replace("R$", "")
                    .replace(".", "")
                    .replace(",", ".")
                )

        if not all([categoria, nome, preço]):
            return {}

        if imagens := soup.select('img[data-testid="media-gallery-image"]'):
            self.highlight_element(driver, "div[data-testid=media-gallery-image]")
            imagens = [
                i.get("src").replace(r"90x90", r"480x480")
                for i in imagens
                if i.get("src")
            ]

        nota, avaliações = None, None
        if eval_div := get_selector('div[data-testid="mod-row"]'):
            if popularidade := eval_div.select_one('span[format="score-count"]'):
                nota, avaliações = popularidade.get_text().strip().split(" ")
                avaliações = avaliações.replace("(", "").replace(")", "")

        if descrição := get_selector('div[data-testid="rich-content-container"]'):
            descrição = md(str(descrição))

        marca, modelo, certificado, ean = None, None, None, None
        if características := self.parse_tables(soup):
            marca = características.get("Marca")
            modelo = características.get("Modelo")
            certificado = self.extrair_certificado(características)
            ean = self.extrair_ean(características)
        elif descrição:
            if certificado is None:
                certificado = self.match_certificado(descrição)
            if ean is None:
                ean = self.match_ean(descrição)

        product_id = None
        match = re.search(r"/p/([\w\d]+)/", driver.get_current_url())
        if match:
            product_id = match.group(1)

        return {
            "avaliações": avaliações,
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
            "nota": nota,
            "preço": preço,
            "product_id": product_id,
            "url": driver.get_current_url(),
            "vendas": None,
            "vendedor": None,
        }

    def input_search_params(self, driver, keyword):
        for attempt in range(self.retries):
            try:
                self.highlight_element(driver, self.input_field)
                driver.type(self.input_field, keyword + "\n", timeout=self.timeout)
                if department := CATEGORIES.get(keyword):
                    self.uc_click(driver, department)
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
