import json
import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import unquote
from seleniumbase.common.exceptions import (
    NoSuchElementException,
    ElementNotVisibleException,
)

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
        return 'input[id*="search"]'

    @property
    def next_page_button(self) -> str:
        return 'a[class="s-pagination-item s-pagination-next s-pagination-button s-pagination-separator"]'

    @staticmethod
    def transform_url(source_url):
        decoded_url = unquote(source_url)
        patterns = [
            (
                r"https://www\.amazon\.com\.br/sspa/click.*?/(.*?)/dp/(.*?)/",
                lambda m: f"https://www.amazon.com.br/{m.group(1)}/dp/{m.group(2)}",
            ),
            (r"(^http.*)\/ref=.*", lambda m: m.group(1)),
        ]
        for pattern, replacement in patterns:
            if match := re.search(pattern, decoded_url):
                return replacement(match)
        return decoded_url

    def extract_search_results(self, div):
        def safe_get(selector, attr=None, default=""):
            element = div.select_one(selector)
            if not element:
                return default
            return element.get(attr) if attr else element.get_text().strip()

        link_relativo = safe_get("h2 a", "href")
        nome = safe_get("h2 span")
        preço = safe_get("span.a-offscreen")
        stars = safe_get("i.a-icon-star-small span")
        evals = safe_get("span.a-size-base.s-underline-text")
        imgs = safe_get("img.s-image", "srcset")

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

    def parse_tables(self, driver, soup) -> dict:
        """Extrai o conteúdo da tabela com dados do produto e transforma em um dict"""
        table_data = {}
        if tables := soup.select('table[id^="productDetails"]'):
            self.highlight_element(driver, 'table[id="productDetails"]')
            for table in tables:
                for row in table.select("tr"):
                    key = row.select_one("th")
                    value = row.select_one("td")
                    if key and value:
                        table_data[key.text.strip()] = value.text.strip().replace(
                            "\u200e", ""
                        )
        elif tables := soup.select(
            'table[class="a-bordered"]'
        ):  # special pages like iphone
            self.highlight_element(driver, 'table[class="a-bordered"]')
            for table in tables:
                rows = table.select("td")
                if rows:
                    table_data.update(
                        {
                            k.text.strip(): v.text.strip()
                            for k, v in zip(rows[::2], rows[1::2])
                            if (
                                hasattr(k, "text")
                                and "R$" not in k.text.strip()
                                and "R$" not in v.text.strip()
                            )
                        }
                    )
        return table_data

    def extract_item_data(self, driver):
        soup = driver.get_beautiful_soup()
        if nome := soup.select_one("span#productTitle"):
            self.highlight_element(driver, 'span[id="productTitle"]')
            nome = nome.get_text().strip()

        if categoria := soup.select_one("div#wayfinding-breadcrumbs_feature_div"):
            self.highlight_element(
                driver, 'div[id="wayfinding-breadcrumbs_feature_div"]'
            )
            categoria = "|".join(s.text.strip() for s in categoria.select("a"))
        elif nome and "iphone" in nome.lower():
            categoria = "Eletrônicos e Tecnologia|Celulares e Comunicação|Celulares e Smartphones"

        if vendas := soup.select_one("span#social-proofing-faceout-title-tk_bought"):
            self.highlight_element(
                driver, 'span[id="social-proofing-faceout-title-tk_bought"]'
            )
            vendas = vendas.get_text().strip()

        if imagens := re.findall(
            r"colorImages':.*'initial':\s*(\[.+?\])},\n", str(soup)
        ):
            imagens = [
                d.get("large", "")
                for d in json.loads(imagens[0])
                if isinstance(d, dict)
            ]

        if preço := soup.select_one('span[class="aok-offscreen"]'):
            self.highlight_element(driver, 'span[class="aok-offscreen"]')
            preço = re.sub(r"R\$|\.", "", preço.get_text().strip()).replace(",", ".")

        if nota := soup.select_one('i[class="cm-cr-review-stars-spacing-big"]'):
            self.highlight_element(driver, 'i[class="cm-cr-review-stars-spacing-big"]')
            nota = nota.get_text().strip()

        if avaliações := soup.select_one('div[data-hook="total-review-count"]'):
            # self.highlight_element(driver, 'div[data-hook="total-review-count"]')
            avaliações = "".join(re.findall(r"\d", avaliações.get_text().strip()))
        elif avaliações := soup.select_one("span#acrCustomerReviewText"):
            self.highlight_element(driver, 'span[id="acrCustomerReviewText"]')
            avaliações = avaliações.get_text().strip()

        if marca := soup.select_one("a#bylineInfo"):
            self.highlight_element(driver, 'a[id="bylineInfo"]')
            marca = f'{re.sub(r"Marca: |Visite a loja ", "", marca.get_text().strip())}'.title()

        if vendedor := soup.select_one("a#sellerProfileTriggerId"):
            self.highlight_element(driver, 'a[id="sellerProfileTriggerId"]')
            link_vendedor = f"{self.url}{vendedor.get('href')}"
            vendedor = vendedor.get_text().strip()
        elif vendedor := soup.select_one("a#bylineInfo"):
            self.highlight_element(driver, 'a[id="bylineInfo"]')
            link_vendedor = f"{self.url}{vendedor.get('href')}"
            vendedor = f'{re.sub(r"Marca: |Visite a loja ", "", vendedor.get_text().strip())}'.title()
        else:
            link_vendedor = ""

        descrição = ""

        if descrição_principal := soup.select_one("div#feature-bullets"):
            self.highlight_element(driver, 'div[id="feature-bullets"]')
            descrição += "\n".join(
                s.text.strip() for s in descrição_principal.select("span")
            )

        if descrição_secundária := soup.select_one("div#productDescription"):
            self.highlight_element(driver, 'div[id="productDescription"]')
            descrição += "\n".join(
                s.text.strip() for s in descrição_secundária.select("span")
            )

        modelo, ean, certificado, asin = None, None, None, None

        if características := self.parse_tables(driver, soup):
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

    def discover_product_urls(self, soup, keyword):
        results = {}
        for div in soup.select(
            'div.s-result-item[data-component-type="s-search-result"]'
        ):
            if product_data := self.extract_search_results(div):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def input_search_params(self, driver, keyword):
        for attempt in range(self.retries):
            try:
                # section = 'select[id="searchDropdownBox"]'
                # section = '//*[@id="searchDropdownBox"]'
                # self.highlight_element(driver, section)
                # category = driver.find_element(
                #     section, timeout=self.timeout, by="xpath"
                # )
                # category.uc_click()
                # electronics = driver.find_element(
                #     'option[value="search-alias=electronics"]', timeout=self.timeout
                # )
                # electronics.uc_click()
                self.highlight_element(driver, self.input_field)
                driver.type(self.input_field, keyword + "\n", timeout=self.timeout)
                break  # Success, exit the loop
            except (NoSuchElementException, ElementNotVisibleException):
                if attempt < self.retries - 1:  # if it's not the last attempt
                    print(f"Attempt {attempt + 1} failed. Retrying...")
                    driver.sleep(1)  # Wait for 1 second before retrying
                else:
                    print(
                        f"Error: Could not find search input field '{self.input_field}' after {self.retries} attempts"
                    )
                    raise  # Re-raise the last exception
        if department := CATEGORIES.get(keyword):
            for subcategory in department:
                try:
                    subcategory_tag = driver.find_element(
                        subcategory, timeout=self.timeout
                    )
                    subcategory_tag.uc_click()
                except (NoSuchElementException, ElementNotVisibleException) as e:
                    print(e)
