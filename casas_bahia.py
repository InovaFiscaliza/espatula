from dataclasses import dataclass
from datetime import datetime

from base import TIMEZONE, BaseScraper


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
        for item in soup.find(
            "div",
            attrs={"class": "css-1enexmx"},
            partial=True,
            mode="all",
        ):
            if product_data := self.extract_product_data(item):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results
