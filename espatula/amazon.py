import json
import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import unquote
from seleniumbase.common.exceptions import (
    NoSuchElementException,
    ElementNotVisibleException,
)

from bs4 import BeautifulSoup

from .base import TIMEZONE, BaseScraper

CATEGORIES = {"smartphone": ['li[id="n/16243803011"] a', 'li[id="n/16243890011"] a']}


@dataclass
class AmazonScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "amazon"

    @property
    def url(self) -> str:
        return "https://www.amazon.com.br"

    @property
    def input_field(self) -> str:
        return 'input[id="twotabsearchtextbox"]'

    @property
    def next_page_button(self) -> str:
        return 'a[class="s-pagination-item s-pagination-next s-pagination-button s-pagination-separator"]'

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
        link_relativo = (
            header.find("a").get("href") if header and header.find("a") else None
        )
        nome = header.find("span").text if header and header.find("span") else ""
        preço = (
            div.find("span", attrs={"class": "a-offscreen"}).text
            if div.find("span", attrs={"class": "a-offscreen"})
            else ""
        )
        stars = div.find("i", attrs={"class": "a-icon-star-small"})
        stars = stars.find("span").text if stars and stars.find("span") else ""
        evals = div.find("span", attrs={"class": "a-size-base s-underline-text"})
        evals = evals.text if evals else ""
        imgs = div.find("img", attrs={"class": "s-image"})
        imgs = imgs.get("srcset") if imgs else None
        link_produto = f"{self.url}{link_relativo}" if link_relativo else ""
        if not all([nome, preço, link_relativo, imgs]):
            return False
        Link = self.transform_url(link_produto)
        return {
            "nome": nome,
            "preço": preço,
            "nota": stars,
            "avaliações": evals,
            "imagem": imgs,
            "url": Link,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def parse_tables(self, driver) -> dict:
        """Extrai o conteúdo da tabela com dados do produto e transforma em um dict"""
        soup = BeautifulSoup(driver.get_page_source(), "html.parser")
        table_data = {}
        tables = soup.find_all("table", attrs={"id": "productDetails"})
        if tables:
            self.highlight_element(driver, 'table[id="productDetails"]')
        for table in tables:
            for row in table.find_all("tr"):
                key = row.find("th")
                value = row.find("td")
                if key and value:
                    table_data[key.text.strip()] = value.text.strip().replace(
                        "\u200e", ""
                    )
        if not tables:  # special pages like iphone
            for table in soup.find_all("table", attrs={"class": "a-bordered"}):
                rows = table.find_all("td")
                if rows:
                    table_data.update(
                        {
                            k.strip(): v.strip()
                            for k, v in zip(rows[::2], rows[1::2])
                            if ("R$" not in k.strip() and "R$" not in v.strip())
                        }
                    )
        return table_data

    def extract_item_data(self, driver):
        soup = BeautifulSoup(driver.get_page_source(), "html.parser")
        if nome := soup.find("span", attrs={"id": "productTitle"}):
            self.highlight_element(driver, 'span[id="productTitle"]')
            nome = nome.text.strip()

        if categoria := soup.find(
            "div", attrs={"id": "wayfinding-breadcrumbs_feature_div"}
        ):
            self.highlight_element(
                driver, 'div[id="wayfinding-breadcrumbs_feature_div"]'
            )
            categoria = "|".join(s.text.strip() for s in categoria.find_all("a"))
        elif nome and "iphone" in nome.lower():
            categoria = "Eletrônicos e Tecnologia|Celulares e Comunicação|Celulares e Smartphones"

        if vendas := soup.find(
            "span", attrs={"id": "social-proofing-faceout-title-tk_bought"}
        ):
            self.highlight_element(
                driver, 'span[id="social-proofing-faceout-title-tk_bought"]'
            )
            vendas = vendas.text.strip()

        if imagens := re.findall(
            r"colorImages':.*'initial':\s*(\[.+?\])},\n", str(soup)
        ):
            imagens = [
                d.get("large", "")
                for d in json.loads(imagens[0])
                if isinstance(d, dict)
            ]

        if preço := soup.find("span", attrs={"class": "a-offscreen"}):
            self.highlight_element(driver, 'span[class="a-offscreen"]')
            preço = re.sub(r"R\$|\.", "", preço.text.strip()).replace(",", ".")

        if nota := soup.find(
            "i",
            attrs={"class": "cm-cr-review-stars-spacing-big"},
        ):
            self.highlight_element(driver, 'i[class="cm-cr-review-stars-spacing-big"]')
            nota = nota.text.strip()

        if avaliações := soup.find("div", attrs={"data-hook": "total-review-count"}):
            # self.highlight_element(driver, 'div[data-hook="total-review-count"]')
            avaliações = "".join(re.findall(r"\d", avaliações.text.strip()))
        elif avaliações := soup.find("span", attrs={"id": "acrCustomerReviewText"}):
            self.highlight_element(driver, 'span[id="acrCustomerReviewText"]')
            avaliações = avaliações.text.strip()

        if marca := soup.find("a", attrs={"id": "bylineInfo"}):
            self.highlight_element(driver, 'a[id="bylineInfo"]')
            marca = (
                f'{re.sub(r"Marca: |Visite a loja ", "", marca.text.strip())}'.title()
            )

        if vendedor := soup.find("a", attrs={"id": "sellerProfileTriggerId"}):
            self.highlight_element(driver, 'a[id="sellerProfileTriggerId"]')
            link_vendedor = f"{self.url}{vendedor.get('href')}"
            vendedor = vendedor.text.strip()
        elif vendedor := soup.find("a", attrs={"id": "bylineInfo"}):
            self.highlight_element(driver, 'a[id="bylineInfo"]')
            link_vendedor = f"{self.url}{vendedor.get('href')}"
            vendedor = f'{re.sub(r"Marca: |Visite a loja ", "", vendedor.text.strip())}'.title()
        else:
            link_vendedor = ""

        descrição = ""

        if descrição_principal := soup.find("div", attrs={"id": "feature-bullets"}):
            self.highlight_element(driver, 'div[id="feature-bullets"]')
            descrição += "\n".join(
                s.text.strip() for s in descrição_principal.find_all("span")
            )

        if descrição_secundária := soup.find("div", attrs={"id": "productDescription"}):
            self.highlight_element(driver, 'div[id="productDescription"]')
            descrição += "\n".join(
                s.text.strip() for s in descrição_secundária.find_all("span")
            )

        modelo, ean, certificado, asin = None, None, None, None

        if características := self.parse_tables(driver):
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
            asin = características.pop("ASIN", None)

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
            "product_id": asin,
            "url": driver.get_current_url(),
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, driver, keyword):
        soup = BeautifulSoup(driver.get_page_source(), "html.parser")
        results = {}
        for div in soup.find_all(
            "div",
            attrs={"class": "s-result-item", "data-component-type": "s-search-result"},
        ):
            if product_data := self.extract_search_results(div):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def input_search_params(self, driver, keyword):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                section = "select[id=searchDropdownBox]"
                self.highlight_element(driver, section)
                category = driver.find_element(section, timeout=self.timeout)
                category.uc_click(timeout=self.timeout)
                electronics = driver.find_element(
                    'option[value="search-alias=electronics"]', timeout=self.timeout
                )
                electronics.uc_click(timeout=self.timeout)
                self.highlight_element(driver, self.input_field)
                driver.type(self.input_field, keyword + "\n", timeout=self.timeout)
                break  # Success, exit the loop
            except (NoSuchElementException, ElementNotVisibleException):
                if attempt < max_retries - 1:  # if it's not the last attempt
                    print(f"Attempt {attempt + 1} failed. Retrying...")
                    driver.sleep(1)  # Wait for 1 second before retrying
                else:
                    print(
                        f"Error: Could not find search input field '{self.input_field}' after {max_retries} attempts"
                    )
                    raise  # Re-raise the last exception
        if department := CATEGORIES.get(keyword):
            for subcategory in department:
                try:
                    subcategory_tag = driver.find_element(
                        subcategory, timeout=self.timeout
                    )
                    subcategory_tag.uc_click(timeout=self.timeout)
                except (NoSuchElementException, ElementNotVisibleException) as e:
                    print(e)
