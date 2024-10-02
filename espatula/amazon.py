import json
import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import unquote

from markdownify import markdownify as md
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
        if imgs:
            imgs = imgs.split(" ")[0]

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

        def extract_tables(tables):
            for table in tables:
                if hasattr(table, "select"):
                    for row in table.select("tr"):
                        key = row.select_one("th")
                        value = row.select_one("td")
                        if key and value:
                            table_data[key.text.strip()] = value.text.strip().replace(
                                "\u200e", ""
                            )

        if tables := self.get_selector(
            driver, soup, 'table[id^="productDetails"]', True
        ):
            extract_tables(tables)
        elif tables := soup.select('table[class="a-keyvalue prodDetTable"]'):
            extract_tables(tables)

        elif tables := self.get_selector(
            driver, soup, 'table[class="a-bordered"]', True
        ):  # special pages like iphone
            for table in tables:
                if hasattr(table, "select"):
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

        if categoria := self.get_selector(
            driver, soup, 'div[id="wayfinding-breadcrumbs_feature_div"]'
        ):
            categoria = "|".join(
                s.text.strip()
                for s in categoria.select("a")
                if hasattr(categoria, "select")
            )

        if nome := self.get_selector(driver, soup, 'span[id="productTitle"]'):
            nome = nome.get_text().strip()

        if not categoria and nome and "iphone" in nome.lower():
            categoria = "Eletrônicos e Tecnologia|Celulares e Comunicação|Celulares e Smartphones"

        if marca := self.get_selector(driver, soup, 'a[id="bylineInfo"]'):
            marca = f'{re.sub(r"Marca: |Visite a loja ", "", marca.get_text().strip())}'.title()

        if vendedor := self.get_selector(
            driver, soup, 'a[id="sellerProfileTriggerId"]'
        ):
            # link_vendedor = f"{self.url}{vendedor.get('href')}"
            vendedor = vendedor.get_text().strip()
        elif vendedor := self.get_selector(driver, soup, 'a[id="bylineInfo"]'):
            # link_vendedor = f"{self.url}{vendedor.get('href')}"
            vendedor = f'{re.sub(r"Marca: |Visite a loja ", "", vendedor.get_text().strip())}'.title()
        # else:
        #     link_vendedor = ""

        if nota := self.get_selector(
            driver, soup, 'i[class="cm-cr-review-stars-spacing-big"]'
        ):
            nota = nota.get_text().strip()

        if avaliações := self.get_selector(
            driver, soup, 'div[data-hook="total-review-count"]'
        ):
            avaliações = "".join(re.findall(r"\d", avaliações.get_text().strip()))
        elif avaliações := self.get_selector(
            driver, soup, "span#acrCustomerReviewText"
        ):
            avaliações = avaliações.get_text().strip()

        if preço := self.get_selector(driver, soup, 'span[class="a-offscreen"]'):
            preço = re.sub(r"R\$|\.", "", preço.get_text()).replace(",", ".").strip()

        if vendas := self.get_selector(
            driver, soup, 'span[id="social-proofing-faceout-title-tk_bought"]'
        ):
            vendas = vendas.get_text().strip()

        if imagens := re.findall(
            r"colorImages':.*'initial':\s*(\[.+?\])},\n", str(soup)
        ):
            imagens = [
                d.get("large", "")
                for d in json.loads(imagens[0])
                if isinstance(d, dict)
            ]

        descrição = ""
        if descrição_secundária := self.get_selector(
            driver, soup, 'div[id="productDescription"]'
        ):
            if hasattr(descrição_secundária, "select"):
                descrição += md(str(descrição_secundária.select("span")))

        try:
            driver.click_visible_elements(
                'a[class^="a-expander-header"]', timeout=self.timeout
            )
            self.highlight_element(driver, 'div[id="productDetails"]')
        except Exception as e:
            print(e)

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

        if descrição_principal := self.get_selector(
            driver, soup, 'div[id="feature-bullets"]'
        ):
            if hasattr(descrição_principal, "select"):
                descrição = md(str(descrição_principal.select("span")))

        if descrição:
            if certificado is None:
                certificado = self.match_certificado(descrição)
            if ean is None:
                ean = self.match_ean(descrição)

        if not all([nome, preço, categoria]):
            return {}

        return {
            "avaliações": avaliações,
            "categoria": categoria,
            "certificado": certificado,
            "características": características,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
            "descrição": descrição,
            "ean_gtin": ean,
            "estado": None,
            "estoque": None,
            "imagens": imagens,
            "marca": marca,
            "modelo": modelo,
            "nome": nome,
            "nota": nota,
            "preço": preço,
            "product_id": asin,
            "url": driver.get_current_url(),
            "vendas": vendas,
            "vendedor": vendedor,
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
                self.highlight_element(driver, self.input_field)
                driver.type(self.input_field, keyword, timeout=self.timeout)
                self.uc_click(
                    driver, 'input[id="nav-search-submit-button"]', timeout=self.timeout
                )
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
