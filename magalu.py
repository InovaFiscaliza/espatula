import re
from datetime import datetime
from dataclasses import dataclass

import typer
from gazpacho import Soup
from base import BaseScraper, KEYWORDS, SMARTPHONES


@dataclass
class MagaluScraper(BaseScraper):
    name: str = "magalu"
    url: str = "https://www.magazineluiza.com.br"
    input_field: str = 'input[data-testid="input-search"]'
    next_page_button: str = 'button[aria-label="Go to next page"]'

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
            "Nome": name,
            "Preço": price_lower,
            "Preço_Original": price_higher,
            "Avaliações": evals,
            "Imagem": imgs,
            "Link": self.url + relative_url,
            "Data_Atualização": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, soup, keyword):
        results = {}
        for item in soup.find(
            "a",
            attrs={"data-testid": "product-card-container"},
            partial=True,
            mode="all",
        ):
            if product_data := self.extract_search_data(item):
                product_data["Palavra_Chave"] = keyword
                results[product_data["Link"]] = product_data
        return results

    def parse_tables(self, soup) -> dict:
        # Extrai o conteúdo da tabela com dados do produto e transforma em um dict
        variant_data = {}
        if conteiner := soup.find(
            "div", attrs={"class": "sc-fqkvVR dESRav sc-czLspv jSiKdc"}, mode="first"
        ):
            for table in conteiner.find("table", mode="all"):
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
            driver.highlight("a[data-testid=breadcrumb-item]")
            categoria = " | ".join(
                i.strip() for i in categoria if hasattr(i, "strip") and i.strip()
            )

        if nome := soup.find(
            "h1", attrs={"data-testid": "heading-product-title"}, mode="first"
        ):
            driver.highlight("h1[data-testid=heading-product-title]")
            nome = nome.text.strip()

        nota, avaliações = None, None
        if popularidade := soup.find(
            "div", attrs={"data-testid": "mod-row"}, mode="first"
        ):
            driver.highlight("div[data-testid=mod-row]")
            if popularidade := popularidade.find(
                "span", attrs={"format": "score-count"}, mode="first"
            ):
                nota, avaliações = popularidade.text.strip().split(" ")
                avaliações = avaliações.replace("(", "").replace(")", "")

        if preço := soup.find("p", attrs={"data-testid": "price-value"}, mode="first"):
            driver.highlight("p[data-testid=price-value]")
            preço = (
                preço.text.strip().replace("R$", "").replace(".", "").replace(",", ".")
            )

        if imgs := soup.find("img", {"data-testid": "media-gallery-image"}, mode="all"):
            driver.highlight("img[data-testid=media-gallery-image]")
            imgs = [getattr(i, "attrs", {}).get("src") for i in imgs]

        if descrição := soup.find(
            "div", attrs={"data-testid": "rich-content-container"}, mode="first"
        ):
            driver.highlight("div[data-testid=rich-content-container]")
            descrição = descrição.text.strip()

        marca, modelo, certificado, ean = None, None, None, None
        if características := self.parse_tables(soup):
            driver.highlight("div[class=sc-fqkvVR dESRav sc-czLspv jSiKdc]")
            marca, modelo, certificado, ean = (
                características.get("Marca"),
                características.get("Modelo"),
                self.extrair_certificado(características),
                características.get("EAN"),
            )

        if not all([nome, categoria, preço, imgs]):
            return None
        return {
            "Nome": nome,
            "Categoria": categoria,
            "Preço": preço,
            "Nota": nota,
            "Avaliações": avaliações,
            "Imagem": imgs,
            "Descrição": descrição,
            "Marca": marca,
            "Modelo": modelo,
            "Certificado": certificado,
            "EAN": ean,
            "Data_Atualização": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }


if __name__ == "__main__":

    def main(
        search: bool = True,
        keyword: str = None,
        headless: bool = True,
        screenshot: bool = False,
    ):
        scraper = MagaluScraper(headless=headless)

        if not keyword:
            for keyword in SMARTPHONES:
                if search:
                    scraper.search(keyword, screenshot)
                else:
                    scraper.inspect_pages(keyword, screenshot)
        else:
            if search:
                scraper.search(keyword, screenshot)
            else:
                scraper.inspect_pages(keyword, screenshot)

    typer.run(main)
