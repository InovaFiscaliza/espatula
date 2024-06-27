import re
from datetime import datetime
from dataclasses import dataclass

import typer
from base import BaseScraper


@dataclass
class MercadoLivreScraper(BaseScraper):
    name: str = "ml"
    url: str = "https://www.mercadolivre.com.br"
    input_field: str = 'input[id="cb1-edit"]'
    next_page_button: str = 'a[title="Seguinte"]'

    @staticmethod
    def find_single_url(text):
        pattern = (
            r"https://(?:produto\.|www\.)mercadolivre\.com\.br.*?(?:-_JM|(?=\?)|(?=#))"
        )
        match = re.search(pattern, text)

        # Return the first non-empty match
        return match[0] if match else text

    def extract_product_data(self, item):
        if hasattr(
            link := item.find("a", attrs={"class": "ui-search-link"}, mode="first"),
            "attrs",
        ):
            link = self.find_single_url(link.attrs.get("href"))

        if hasattr(
            img := item.find(
                "img",
                attrs={"class": "ui-search-result"},
                partial=True,
                mode="first",
            ),
            "attrs",
        ):
            img = img.attrs.get("src")

        if nome := item.find(
            "h2",
            attrs={"class": "ui-search-item"},
            partial=True,
            mode="first",
        ):
            nome = nome.strip()

        if preço := item.find(
            "span",
            attrs={"class": "andes-money-amount__fraction"},
            partial=True,
            mode="first",
        ):
            preço = preço.strip()

        if evals := item.find(
            "span",
            attrs={"class": "ui-search-reviews__amount"},
            partial=True,
            mode="first",
        ):
            evals = evals.strip()

        if nota := item.find(
            "span",
            attrs={"class": "ui-search-reviews__rating-number"},
            partial=True,
            mode="first",
        ):
            nota = nota.strip()

        if not all([nome, preço, img]):
            return False

        return {
            "Nome": nome,
            "Preço": preço,
            "Avaliações": evals,
            "Nota": nota,
            "Imagem": img,
            "Link": link,
            "Data_Atualização": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, soup, keyword):
        results = {}
        for item in soup.find(
            "li", attrs={"class": "ui-search-layout__item"}, partial=True, mode="all"
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
        scraper = MercadoLivreScraper(headless=headless)
        scraper.search(keyword, screenshot, md)

    typer.run(main)
