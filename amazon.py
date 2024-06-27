import re
from urllib.parse import unquote
from datetime import datetime
from dataclasses import dataclass

import typer
from base import BaseScraper


@dataclass
class AmazonScraper(BaseScraper):
    name: str = "amazon"
    url: str = "https://www.amazon.com.br"
    input_field: str = 'input[id="twotabsearchtextbox"]'
    next_page_button: str = 'a[class="s-pagination-item s-pagination-next s-pagination-button s-pagination-separator"]'

    @staticmethod
    def transform_url(source_url):
        pattern1 = re.compile(
            r"https://www\.amazon\.com\.br/sspa/click.*?/(.*?)/dp/(.*?)/"
        )
        pattern2 = re.compile(r"(^http.*)\/ref=.*")
        decoded_url = unquote(source_url)
        if match := re.search(pattern1, decoded_url):
            product_description = match.group(1)
            product_code = match.group(2)
            return f"https://www.amazon.com.br/{product_description}/dp/{product_code}"
        if match := re.search(pattern2, decoded_url):
            return match.group(1)
        return decoded_url

    def extract_product_data(self, div):
        header = div.find("h2")
        link_relativo = getattr(header.find("a"), "attrs", {}).get("href")
        nome = getattr(header.find("span"), "text", "")
        preço = getattr(
            div.find(
                "span", attrs={"class": "a-offscreen"}, mode="first", partial=False
            ),
            "text",
            "",
        )
        if stars := div.find("i", attrs={"class": "a-icon-star-small"}):
            stars = getattr(stars.find("span"), "text", "")
        evals = getattr(
            div.find("span", attrs={"class": "a-size-base s-underline-text"}),
            "text",
            "",
        )
        imgs = getattr(div.find("img", attrs={"class": "s-image"}), "attrs", {}).get(
            "srcset"
        )
        link_produto = f"{self.url}{link_relativo}"
        if not all([nome, preço, link_relativo, imgs]):
            return False
        Link = self.transform_url(link_produto)
        return {
            "Nome": nome,
            "Preço": preço,
            "Nota": stars,
            "Avaliações": evals,
            "Imagem": imgs,
            "Link": Link,
            "Data_Atualização": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, soup, keyword):
        results = {}
        for div in soup.find(
            "div",
            attrs={"class": "s-result-item", "data-component-type": "s-search-result"},
            mode="all",
            partial=True,
        ):
            if product_data := self.extract_product_data(div):
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
        scraper = AmazonScraper(headless=headless)
        scraper.search(keyword, screenshot, md)

    typer.run(main)
