import re
from datetime import datetime
from dataclasses import dataclass

from gazpacho import Soup

from ..constantes import KEYWORDS
from .base import BaseScraper, TIMEOUT, RECONNECT, TIMEZONE

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
        relative_url = produto.attrs.get("href")
        if name := produto.find(
            "h2", attrs={"data-testid": "product-title"}, mode="first"
        ):
            name = name.strip()
        if evals := produto.find("div", attrs={"data-testid": "review"}, mode="first"):
            evals = evals.strip()
        if price_lower := produto.find(
            "p", {"data-testid": "price-value"}, mode="first"
        ):
            price_lower = price_lower.strip()

        if price_higher := produto.find(
            "p", {"data-testid": "price-original"}, mode="first"
        ):
            price_higher = price_higher.strip()

        if hasattr(
            imgs := produto.find("img", {"data-testid": "image"}, mode="first"),
            "attrs",
        ):
            imgs = imgs.attrs.get("src")
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

    def discover_product_urls(self, driver, keyword):
        soup = Soup(driver.get_page_source())
        results = {}
        for item in soup.find(
            "a",
            attrs={"data-testid": "product-card-container"},
            partial=True,
            mode="all",
        ):
            if product_data := self.extract_search_data(item):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def parse_tables(self, soup) -> dict:
        # Extrai o conteúdo da tabela com dados do produto e transforma em um dict
        variant_data = {}
        for table in soup.find("table", mode="all"):
            if rows := table.find("td", mode="all"):
                if rows[0].strip() == "Informações complementares":
                    continue
                variant_data.update(
                    {
                        k.strip(): v.strip()
                        for k, v in zip(rows[::2], rows[1::2])
                        if ("R$" not in k.strip() and "R$" not in v.strip())
                    }
                )
        return variant_data

    def extract_item_data(self, driver):
        soup = Soup(driver.get_page_source())

        if categoria := soup.find(
            "a", attrs={"data-testid": "breadcrumb-item"}, mode="all", partial=False
        ):
            self.highlight_element(driver, "div[data-testid=breadcrumb-container]")
            categoria = " | ".join(
                i.strip() for i in categoria if hasattr(i, "strip") and i.strip()
            )

        if nome := soup.find(
            "h1", attrs={"data-testid": "heading-product-title"}, mode="first"
        ):
            self.highlight_element(driver, "h1[data-testid=heading-product-title]")
            nome = nome.text.strip()

        if imagens := soup.find(
            "img", {"data-testid": "media-gallery-image"}, mode="all"
        ):
            self.highlight_element(driver, "div[data-testid=media-gallery-image]")
            imagens = [getattr(i, "attrs", {}).get("src") for i in imagens]

        nota, avaliações = None, None
        if popularidade := soup.find(
            "div", attrs={"data-testid": "mod-row"}, mode="first"
        ):
            self.highlight_element(driver, "div[data-testid=mod-row]")
            if popularidade := popularidade.find(
                "span", attrs={"format": "score-count"}, mode="first"
            ):
                nota, avaliações = popularidade.text.strip().split(" ")
                avaliações = avaliações.replace("(", "").replace(")", "")

        if preço := soup.find(
            "div", attrs={"data-testid": "mod-productprice"}, mode="first"
        ):
            self.highlight_element(driver, "div[data-testid=mod-productprice]")
            if preço := preço.find("p", {"data-testid": "price-value"}, mode="first"):
                preço = (
                    preço.text.strip()
                    .replace("R$", "")
                    .replace(".", "")
                    .replace(",", ".")
                )
            else:
                preço = None

        if descrição := soup.find(
            "div", attrs={"data-testid": "rich-content-container"}, mode="first"
        ):
            self.highlight_element(driver, "div[data-testid=rich-content-container]")
            descrição = descrição.text.strip()

        marca, modelo, certificado, ean = None, None, None, None
        if características := self.parse_tables(soup):
            marca, modelo, certificado, ean = (
                características.get("Marca"),
                características.get("Modelo"),
                self.extrair_certificado(características),
                self.extrair_ean(características),
            )

        if match := re.search(r"/p/([\w\d]+)/", driver.current_url):
            product_id = match.group(1)
        else:
            product_id = None

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
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def input_search_params(self, driver, keyword):
        self.highlight_element(driver, self.input_field)
        driver.type(self.input_field, keyword + "\n", timeout=TIMEOUT)
        if department := CATEGORIES.get(keyword):
            driver.uc_click(department, timeout=RECONNECT)
