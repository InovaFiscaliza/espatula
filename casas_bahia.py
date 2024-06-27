import re
from datetime import datetime
from dataclasses import dataclass

import typer
from base import BaseScraper, KEYWORDS


@dataclass
class CasasBahiaScraper(BaseScraper):
    name: str = "casas_bahia"
    url: str = "https://www.casasbahia.com.br"
    input_field: str = 'input[id="search-form-input"]'
    next_page_button: str = 'a[aria-label="Próxima página"]'

    def extract_product_data(self, produto):
        if title := produto.find("h3", attrs={"class": "product-card__title"}):
            if relative_url := title.find("a"):
                relative_url = relative_url.attrs.get("href")
            if name := title.find("span", mode="first"):
                name = name.strip()
        if evals := produto.find(
            "span", attrs={"class": "product-card__reviews-count-text"}, mode="first"
        ):
            evals = evals.strip()
        if nota := produto.find(
            "span", attrs={"data-testid": "product-card-rating"}, mode="first"
        ):
            nota = nota.strip()
        if price_lower := produto.find(
            "div", {"class": "product-card__highlight-price"}, mode="first"
        ):
            price_lower = price_lower.strip()

        if price_higher := produto.find(
            "div", {"class": "product-card__installment-text"}, mode="first"
        ):
            price_higher = price_higher.strip()

        if hasattr(
            imgs := produto.find(
                "img", attrs={"class": "product-card__image"}, mode="first"
            ),
            "attrs",
        ):
            imgs = imgs.attrs.get("src")
        if not all([name, price_lower, imgs, relative_url]):
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
            "div",
            attrs={"class": "css-1enexmx"},
            partial=True,
            mode="all",
        ):
            if product_data := self.extract_product_data(item):
                product_data["Palavra_Chave"] = keyword
                results[product_data["Link"]] = product_data
        return results


if __name__ == "__main__":

    def main(
        keyword: str = None,
        headless: bool = True,
        screenshot: bool = False,
        md: bool = False,
    ):
        scraper = CasasBahiaScraper(headless=headless)
        if not keyword:
            for keyword in KEYWORDS:
                scraper.search(keyword, screenshot, md)
        else:
            scraper.search(keyword, screenshot, md)

    typer.run(main)
