import re
from datetime import datetime
from dataclasses import dataclass

from bs4 import BeautifulSoup

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
            name = name.get_text.strip()
        if evals := produto.select_one('div[data-testid="review"]'):
            evals = evals.get_text.strip()
        if price_lower := produto.select_one('p[data-testid="price-value"]'):
            price_lower = price_lower.get_text.strip()
        if price_higher := produto.select_one('p[data-testid="price-original"]'):
            price_higher = price_higher.get_text.strip()
        if imgs := produto.select_one('img[data-testid="image"]'):
            imgs = imgs.get("src")
        if not all([name, price_lower, imgs]):
            return None
        return {
            "nome": name,
            "preço": price_lower,
            "preço_Original": price_higher,
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
        for table in soup.find_all("table"):
            rows = table.find_all("td")
            if rows and rows[0].text.strip() == "Informações complementares":
                continue
            variant_data.update(
                {
                    k.text.strip(): v.text.strip()
                    for k, v in zip(rows[::2], rows[1::2])
                    if ("R$" not in k.text.strip() and "R$" not in v.text.strip())
                }
            )
        return variant_data

    def extract_item_data(self, driver):
        soup = BeautifulSoup(driver.get_page_source(), "html.parser")

        categoria = soup.find_all("a", attrs={"data-testid": "breadcrumb-item"})
        if categoria:
            self.highlight_element(driver, "div[data-testid=breadcrumb-container]")
            categoria = " | ".join(i.text.strip() for i in categoria if i.text.strip())

        nome = soup.find("h1", attrs={"data-testid": "heading-product-title"})
        if nome:
            self.highlight_element(driver, "h1[data-testid=heading-product-title]")
            nome = nome.text.strip()

        imagens = soup.find_all("img", {"data-testid": "media-gallery-image"})
        if imagens:
            self.highlight_element(driver, "div[data-testid=media-gallery-image]")
            imagens = [i.get("src") for i in imagens if i.get("src")]

        nota, avaliações = None, None
        popularidade = soup.find("div", attrs={"data-testid": "mod-row"})
        if popularidade:
            self.highlight_element(driver, "div[data-testid=mod-row]")
            popularidade = popularidade.find("span", attrs={"format": "score-count"})
            if popularidade:
                nota, avaliações = popularidade.text.strip().split(" ")
                avaliações = avaliações.replace("(", "").replace(")", "")

        preço = None
        preço_div = soup.find("div", attrs={"data-testid": "mod-productprice"})
        if preço_div:
            self.highlight_element(driver, "div[data-testid=mod-productprice]")
            preço = preço_div.find("p", {"data-testid": "price-value"})
            if preço:
                preço = (
                    preço.text.strip()
                    .replace("R$", "")
                    .replace(".", "")
                    .replace(",", ".")
                )

        descrição = soup.find("div", attrs={"data-testid": "rich-content-container"})
        if descrição:
            self.highlight_element(driver, "div[data-testid=rich-content-container]")
            descrição = descrição.text.strip()

        marca, modelo, certificado, ean = None, None, None, None
        características = self.parse_tables(soup)
        if características:
            marca = características.get("Marca")
            modelo = características.get("Modelo")
            certificado = self.extrair_certificado(características)
            ean = self.extrair_ean(características)

        product_id = None
        match = re.search(r"/p/([\w\d]+)/", driver.get_current_url())
        if match:
            product_id = match.group(1)

        return {
            "nome": nome,
            "categoria": categoria,
            "preço": preço,
            "nota": nota,
            "avaliações": avaliações,
            "imagens": imagens,
            "descrição": descrição,
            "marca": marca,
            "modelo": modelo,
            "certificado": certificado,
            "ean_gtin": ean,
            "características": características,
            "product_id": product_id,
            "url": driver.get_current_url(),
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def input_search_params(self, driver, keyword):
        self.highlight_element(driver, self.input_field)
        driver.type(self.input_field, keyword + "\n", timeout=self.timeout)
        if department := CATEGORIES.get(keyword):
            driver.uc_click(department, timeout=self.reconnect)
