from datetime import datetime
from dataclasses import dataclass

import typer
from gazpacho import Soup
from base import BaseScraper, KEYWORDS, TIMEOUT, RECONNECT

CATEGORIES = {
    "smartphone": 'a[href="/busca/smartphone/?from=submit&filters=category---TE"]'
}


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

        if imgs := soup.find("img", {"data-testid": "media-gallery-image"}, mode="all"):
            self.highlight_element(driver, "div[data-testid=media-gallery-image]")
            imgs = [getattr(i, "attrs", {}).get("src") for i in imgs]

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
                características.get("EAN"),
            )

        return {
            "Nome": nome,
            "Categoria": categoria,
            "Preço": preço,
            "Nota": nota,
            "Avaliações": avaliações,
            "Imagens": imgs,
            "Descrição": descrição,
            "Marca": marca,
            "Modelo": modelo,
            "Certificado": certificado,
            "EAN": ean,
            "Características": características,
            "Data_Atualização": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def input_search_params(self, driver, keyword):
        self.highlight_element(driver, self.input_field)
        driver.type(self.input_field, keyword + "\n", timeout=TIMEOUT)
        if department := CATEGORIES.get(keyword):
            driver.uc_click(department, timeout=RECONNECT)


if __name__ == "__main__":

    def main(
        search: bool = True,
        keyword: str = None,
        headless: bool = True,
        screenshot: bool = False,
    ):
        scraper = MagaluScraper(headless=headless)

        if not keyword:
            for keyword in KEYWORDS:
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
