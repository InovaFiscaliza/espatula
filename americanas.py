from datetime import datetime
from dataclasses import dataclass

from base import BaseScraper, TIMEZONE


@dataclass
class AmericanasScraper(BaseScraper):
    name: str = "americanas"
    url: str = "https://www.americanas.com.br"
    input_field: str = 'input[placeholder="busque aqui seu produto"]'
    next_page_button: str = 'svg[class="src__ArrowRotate-sc-82ugau-2 hWXbQX"]'

    def extract_search_data(self, produto):
        if relative_url := produto.find("a"):
            relative_url = relative_url.attrs.get("href")
        if nome := produto.find("h3", mode="first"):
            nome = nome.strip()
        if avaliações := produto.find(
            "span", attrs={"class": "src__Count-sc-r5o9d7-1 eDRxIY"}, mode="first"
        ):
            avaliações = avaliações.strip()
        if preço := produto.find("span", {"class": "list-price"}, mode="first"):
            preço = preço.strip()

        if preço_original := produto.find(
            "span", {"class": "sales-price"}, mode="first"
        ):
            preço_original = preço_original.strip()

        if hasattr(
            imagens := produto.find("img", mode="first"),
            "attrs",
        ):
            imagens = imagens.attrs.get("src")
        return {
            "nome": nome,
            "preço": preço,
            "preço_Original": preço_original,
            "avaliações": avaliações,
            "imagem": imagens,
            "url": self.url + relative_url,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
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
            if product_data := self.extract_search_data(item):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results
