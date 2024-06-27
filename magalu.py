import re
from datetime import datetime
from dataclasses import dataclass

import typer
from base import BaseScraper


@dataclass
class MagaluScraper(BaseScraper):
    name: str = "magalu"
    url: str = "https://www.magazineluiza.com.br"
    input_field: str = 'input[data-testid="input-search"]'
    next_page_button: str = 'button[aria-label="Go to next page"]'

    def extract_product_data(self, produto):
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
        scraper = MagaluScraper(headless=headless)
        scraper.search(keyword, screenshot, md)

    typer.run(main)
