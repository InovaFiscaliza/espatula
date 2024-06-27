import re
from datetime import datetime
from dataclasses import dataclass

import typer
from base import BaseScraper


@dataclass
class AmericanasScraper(BaseScraper):
    name: str = "americanas"
    url: str = "https://www.americanas.com.br"
    input_field: str = 'input[placeholder="busque aqui seu produto"]'
    next_page_button: str = 'a[class="src__PageLink-sc-82ugau-3 exDCiw"]'

    def extract_product_data(self, produto):
        if relative_url := produto.find("a"):
            relative_url = relative_url.attrs.get("href")
        if name := produto.find("h3", mode="first"):
            name = name.strip()
        if evals := produto.find(
            "span", attrs={"class": "src__Count-sc-r5o9d7-1 eDRxIY"}, mode="first"
        ):
            evals = evals.strip()
        if price_lower := produto.find("span", {"class": "list-price"}, mode="first"):
            price_lower = price_lower.strip()

        if price_higher := produto.find("span", {"class": "sales-price"}, mode="first"):
            price_higher = price_higher.strip()

        if hasattr(
            imgs := produto.find("img", mode="first"),
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
            attrs={
                "class": "col__StyledCol-sc-1snw5v3-0 ehOuCD theme-grid-col src__ColGridItem-sc-122lblh-1 cJnBan"
            },
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
        scraper = AmericanasScraper(headless=headless)
        scraper.search(keyword, screenshot, md)

    typer.run(main)
