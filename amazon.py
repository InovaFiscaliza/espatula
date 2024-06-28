import re
import json
from urllib.parse import unquote
from datetime import datetime
from dataclasses import dataclass

import typer
from base import BaseScraper, KEYWORDS


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

    def extract_search_results(self, div):
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

    def extract_item_data(self, soup):
        if nome := soup.find("span", attrs={"id": "productTitle"}, mode="first"):
            nome = nome.strip()

        if categoria := soup.find(
            "div", attrs={"id": "wayfinding-breadcrumbs_feature_div"}, mode="first"
        ):
            categoria = " | ".join(
                s.text.strip() for s in categoria.find("a", mode="all")
            )

        if imagens := re.findall(
            r"colorImages':.*'initial':\s*(\[.+?\])},\n", soup.html
        ):
            imagens = "\n".join(
                d.get("large", "")
                for d in json.loads(imagens[0])
                if isinstance(d, dict)
            )

        if preço := soup.find("span", attrs={"class": "a-offscreen"}, mode="first"):
            preço = preço.strip().replace(r"R$|\.|,", "", regex=True)

        if nota := soup.find("i", attrs={"data-hook": "average-star-rating"}):
            nota = nota.strip()

        if avaliações := soup.find(
            "div", attrs={"data-hook": "total-review-count"}, mode="first"
        ):
            avaliações = "".join(re.findall(r"\d", avaliações.strip()))

        if marca := soup.find("a", attrs={"id": "bylineInfo"}, mode="first"):
            marca = f'{marca.strip().replace(r"Marca: |Visite a loja ", "", regex=True)}'.title()

        if vendedor := soup.find(
            "a", attrs={"id": "sellerProfileTriggerId"}, mode="first"
        ):
            vendedor = vendedor.strip()
            link_vendedor = f"{self.url}{vendedor.attrs.get('href')}"
        else:
            link_vendedor = ""

        descrição = ""

        if descrição_principal := soup.find(
            "div", attrs={"id": "feature-bullets"}, mode="first"
        ):
            descrição += "\n".join(
                s.text.strip() for s in descrição_principal.find("span", mode="all")
            )

        if descrição_secundária := soup.find(
            "div", attrs={"id": "productDescription"}, mode="first"
        ):
            descrição += "\n".join(
                s.text.strip() for s in descrição_secundária.find("span", mode="all")
            )

        características = self.parse_tables(soup)

        if not marca:
            marca = características.pop("Marca", "")

        certificado = self.extrair_certificado(características)

        if not (ean := características.pop("EAN", "")):
            ean = características.pop("GTIN", "")

        def extrair_modelo(caracteristicas):
            chrs = caracteristicas.copy()
            return " | ".join(
                caracteristicas.pop(k, "") for k in chrs if "modelo" in k.lower()
            )

        modelo = extrair_modelo(características)

        if not all([nome, categoria, preço, imagens]):
            return {}

        return {
            "Nome": nome,
            "Categoria": categoria,
            "Imagens": imagens,
            "Preço": preço,
            "Nota": nota,
            "Avaliações": avaliações,
            "Marca": marca,
            "Vendedor": vendedor,
            "Link_Vendedor": link_vendedor,
            "Descrição": descrição,
            "Características": características,
            "Certificado": certificado,
            "EAN": ean,
            "Modelo": modelo,
        }

    def discover_product_urls(self, soup, keyword):
        results = {}
        for div in soup.find(
            "div",
            attrs={"class": "s-result-item", "data-component-type": "s-search-result"},
            mode="all",
            partial=True,
        ):
            if product_data := self.extract_search_results(div):
                product_data["Palavra_Chave"] = keyword
                results[product_data["Link"]] = product_data
        return results


if __name__ == "__main__":

    def main(
        keyword: str = None,
        headless: bool = True,
        screenshot: bool = False,
    ):
        scraper = AmazonScraper(headless=headless)
        if not keyword:
            for keyword in KEYWORDS:
                scraper.inspect_pages(keyword, screenshot)
        else:
            scraper.inspect_pages(keyword, screenshot)

    typer.run(main)
