import re
import json
from urllib.parse import unquote
from datetime import datetime
from dataclasses import dataclass

import typer
from gazpacho import Soup
from base import BaseScraper, KEYWORDS, TIMEOUT


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

    @staticmethod
    def parse_tables(soup) -> dict:
        """Extrai o conteúdo da tabela com dados do produto e transforma em um dict"""
        table_data = {}
        tables = soup.find("table", attrs={"id": "productDetails"}, mode="all")
        for table in tables:
            for row in table.find("tr", mode="all"):
                key = row.find("th", mode="first")
                value = row.find("td", mode="first")
                table_data[getattr(key, "text", "")] = getattr(
                    value, "text", ""
                ).replace("\u200e", "")
        if not tables:  # special pages like iphone
            for table in soup.find(
                "table", attrs={"class": "a-bordered"}, partial=False, mode="all"
            ):
                if rows := table.find("td", mode="all"):
                    table_data.update(
                        {
                            k.strip(): v.strip()
                            for k, v in zip(rows[::2], rows[1::2])
                            if ("R$" not in k.strip() and "R$" not in v.strip())
                        }
                    )
        return table_data

    def extract_item_data(self, driver):
        soup = Soup(driver.get_page_source())
        if nome := soup.find("span", attrs={"id": "productTitle"}, mode="first"):
            nome = nome.strip()

        if categoria := soup.find(
            "div", attrs={"id": "wayfinding-breadcrumbs_feature_div"}, mode="first"
        ):
            categoria = "|".join(
                s.text.strip() for s in categoria.find("a", mode="all")
            )
        elif nome and "iphone" in nome.lower():
            categoria = "Eletrônicos e Tecnologia|Celulares e Comunicação|Celulares e Smartphones"

        if imagens := re.findall(
            r"colorImages':.*'initial':\s*(\[.+?\])},\n", soup.html
        ):
            imagens = "\n".join(
                d.get("large", "")
                for d in json.loads(imagens[0])
                if isinstance(d, dict)
            )

        if preço := soup.find("span", attrs={"class": "a-offscreen"}, mode="first"):
            preço = re.sub(r"R\$|\.", "", preço.text.strip()).replace(",", ".")

        if nota := soup.find("i", attrs={"data-hook": "average-star-rating"}):
            nota = nota.strip()

        if avaliações := soup.find(
            "div", attrs={"data-hook": "total-review-count"}, mode="first"
        ):
            avaliações = "".join(re.findall(r"\d", avaliações.strip()))
        elif avaliações := soup.find(
            "span", attrs={"id": "acrCustomerReviewText"}, mode="first"
        ):
            avaliações = avaliações.strip()

        if marca := soup.find("a", attrs={"id": "bylineInfo"}, mode="first"):
            marca = (
                f'{re.sub(r"Marca: |Visite a loja ", "", marca.text.strip())}'.title()
            )

        if vendedor := soup.find(
            "a", attrs={"id": "sellerProfileTriggerId"}, mode="first"
        ):
            link_vendedor = f"{self.url}{vendedor.attrs.get('href')}"
            vendedor = vendedor.strip()
        elif vendedor := soup.find("a", attrs={"id": "bylineInfo"}, mode="first"):
            link_vendedor = f"{self.url}{vendedor.attrs.get('href')}"
            vendedor = f'{re.sub(r"Marca: |Visite a loja ", "", vendedor.text.strip())}'.title()
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

        modelo, ean, certificado = None, None, None

        if características := self.parse_tables(soup):
            if not marca:
                marca = características.pop("Marca", "")

            ean = self.extrair_ean(características)
            certificado = self.extrair_certificado(características)

            def extrair_modelo(caracteristicas):
                chrs = caracteristicas.copy()
                return " | ".join(
                    caracteristicas.pop(k, "") for k in chrs if "modelo" in k.lower()
                )

            modelo = extrair_modelo(características)

        if vendas := soup.find(
            "span", attrs={"id": "social-proofing-faceout-title-tk_bought"}
        ):
            vendas = vendas.strip()

        return {
            "nome": nome,
            "categoria": categoria,
            "imagens": imagens,
            "preço": preço,
            "nota": nota,
            "avaliações": avaliações,
            "marca": marca,
            "vendedor": vendedor,
            "link_vendedor": link_vendedor,
            "descrição": descrição,
            "características": características,
            "certificado": certificado,
            "ean_gtin": ean,
            "modelo": modelo,
            "vendas": vendas,
            "data": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
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

    def input_search_params(self, driver, keyword):
        section = "select[id=searchDropdownBox]"
        self.highlight_element(driver, section)
        category = driver.find_element(section)
        category.uc_click()
        electronics = driver.find_element('option[value="search-alias=electronics"]')
        electronics.uc_click()
        self.highlight_element(driver, self.input_field)
        driver.type(self.input_field, keyword + "\n", timeout=TIMEOUT)


if __name__ == "__main__":

    def main(
        search: bool = True,
        keyword: str = None,
        headless: bool = True,
        screenshot: bool = False,
    ):
        scraper = AmazonScraper(headless=headless)

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
