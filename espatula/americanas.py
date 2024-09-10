from datetime import datetime
from dataclasses import dataclass
from bs4 import BeautifulSoup

from .base import TIMEZONE, BaseScraper


@dataclass
class AmericanasScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "americanas"

    @property
    def url(self) -> str:
        return "https://www.americanas.com.br"

    @property
    def input_field(self) -> str:
        return 'input[placeholder="busque aqui seu produto"]'

    @property
    def next_page_button(self) -> str:
        return 'svg[class="src__ArrowRotate-sc-82ugau-2 hWXbQX"]'

    def extract_search_data(self, produto):
        relative_url = produto.select_one("a")
        relative_url = relative_url["href"] if relative_url else None

        nome = produto.select_one("h3")
        nome = nome.text.strip() if nome else None

        avaliações = produto.select_one("span.src__Count-sc-r5o9d7-1.eDRxIY")
        avaliações = avaliações.text.strip() if avaliações else None

        preço = produto.select_one("span.list-price")
        preço = preço.text.strip() if preço else None

        preço_original = produto.select_one("span.sales-price")
        preço_original = preço_original.text.strip() if preço_original else None

        imagens = produto.select_one("img")
        imagens = imagens["src"] if imagens else None

        return {
            "nome": nome,
            "preço": preço,
            "preço_Original": preço_original,
            "avaliações": avaliações,
            "imagem": imagens,
            "url": self.url + (relative_url or ""),
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, driver, keyword):
        soup = BeautifulSoup(driver.get_page_source(), "html.parser")
        results = {}
        for item in soup.find_all(
            "div",
            attrs={
                "class": "col__StyledCol-sc-1snw5v3-0 ehOuCD theme-grid-col src__ColGridItem-sc-122lblh-1 cJnBan"
            },
        ):
            if product_data := self.extract_search_data(item):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def extract_item_data(self, driver):
        soup = BeautifulSoup(driver.get_page_source(), "html.parser")

        categoria = soup.select_one("div.breadcrumb")
        if categoria:
            self.highlight_element(driver, "div:contains(breadcrumb)")
            categoria = " | ".join(
                a.text.strip() for a in categoria.select("a") if a.text.strip()
            )

        nome = soup.select_one("h1.product-title")
        if nome:
            self.highlight_element(driver, 'h1:contains("product-title")')
            nome = nome.text.strip()

        imagens = []
        gallery = soup.select_one("div.Gallery")
        if gallery:
            self.highlight_element(driver, 'div:contains("Gallery")')
            imagens = [
                img.get("src") for img in gallery.select("img") if img.get("src")
            ]

        nota, avaliações = None, None
        popularidade = soup.select_one(
            "div[data-testid='mod-row'] span[format='score-count']"
        )
        if popularidade:
            self.highlight_element(driver, "div[data-testid=mod-row]")
            nota, avaliações = popularidade.text.strip().split(" ")
            avaliações = avaliações.strip("()")

        preço = soup.select_one("div.priceSales")
        if preço:
            self.highlight_element(driver, "div[data-testid=mod-productprice]")
            preço = (
                preço.text.strip()
                .replace("R$", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )

        descrição = soup.select_one("div[data-testid='rich-content-container']")
        if descrição:
            self.highlight_element(driver, "div[data-testid=rich-content-container]")
            descrição = descrição.text.strip()

        marca, modelo, certificado, ean, product_id = None, None, None, None, None
        características = self.parse_tables(soup)
        if características:
            driver.uc_click('button[aria-expanded="false"]')
            marca = características.get("Marca")
            modelo = características.get("Modelo")
            certificado = self.extrair_certificado(características)
            ean = self.extrair_ean(características)
            product_id = características.get("Código")

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

    def parse_tables(self, soup) -> dict:
        # Extrai o conteúdo da tabela com dados do produto e transforma em um dict
        variant_data = {}
        for table in soup.select("table"):
            rows = table.select("td")
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
