import re
from dataclasses import dataclass
from datetime import datetime
from seleniumbase.common.exceptions import (
    NoSuchElementException,
    ElementNotVisibleException,
)
from markdownify import markdownify as md
from .base import TIMEZONE, BaseScraper

CATEGORIES = {
    "smartphone": "https://www.mercadolivre.com.br/c/celulares-e-telefones#menu=categories"
}

URL = re.compile(
    r"""
        https://(?:produto\.|www\.)mercadolivre\.com\.br  # Matches the domain, allowing for 'produto.' or 'www.' subdomains
        .*?                                               # Matches any characters (non-greedy) after the domain
        (                                               # Non-capturing group for the end of the URL
            -_JM                                          # Matches '-_JM' at the end of the URL
            |                                             # OR
            (?=\?)                                        # Positive lookahead for '?' (start of query parameters)
            |                                             # OR
            (?=#)                                         # Positive lookahead for '#' (start of fragment identifier)
        )
    """,
    re.MULTILINE,
)

URL = re.compile(
    r"https://(?:produto\.|www\.)mercadolivre\.com\.br.*?(-_JM|(?=\?)|(?=#))"
)


PRODUCT_ID = re.compile(r"(MLB-?\d+)")


@dataclass
class MercadoLivreScraper(BaseScraper):
    browser_initialized: bool = False

    @property
    def name(self) -> str:
        return "ml"

    @property
    def url(self) -> str:
        return "https://www.mercadolivre.com.br"

    @property
    def input_field(self) -> str:
        return 'input[id="cb1-edit"]'

    @property
    def next_page_button(self) -> str:
        return 'a[title="Seguinte"]'

    @staticmethod
    def find_single_url(text):
        if match := re.search(URL, text):
            return match.group(0)
        return text

    def extract_search_data(self, item):
        if url := item.select_one("a.ui-search-link"):
            url = self.find_single_url(url.get("href"))

        if imagem := item.select_one("img"):
            imagem = imagem.get("src")

        if nome := item.select_one("h2"):
            nome = nome.get_text().strip()

        if preço := item.select_one('div[class*="price"]'):
            preço = preço.select_one("span").get_text().replace("R$", "").strip()

        if avaliações := item.select_one('span[class$="reviews__total"]'):
            avaliações = avaliações.get_text().strip()

        if nota := item.select_one('span[class$="rating"]'):
            nota = nota.get_text().strip()

        return {
            "nome": nome,
            "preço": preço,
            "avaliações": avaliações,
            "nota": nota,
            "imagem": imagem,
            "url": url,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, soup, keyword):
        results = {}
        for item in soup.select('li[class^="ui-search-layout"]'):
            if product_data := self.extract_search_data(item):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def parse_specs(self, element) -> dict:
        specs = {}
        tables = element.select("table.andes-table")
        lists = element.select("div.ui-pdp-list.ui-pdp-specs__list")
        specs.update(self.parse_tables(tables))
        specs.update(self.parse_lists(lists))
        return specs

    @staticmethod
    def parse_tables(tables: list) -> dict:
        """
        Parses tables from the product detail page to extract specifications and returns them as a dictionary.
        This method can be easily tested in isolation.
        """
        return {
            row.select_one("th").get_text().strip(): row.select_one("td")
            .get_text()
            .strip()
            for table in tables
            for row in table.select("tr")
        }

    @staticmethod
    def parse_lists(lists: list) -> dict:
        items = {}
        for list_div in lists:
            for li in list_div.select("li"):
                if item := li.select_one("p"):
                    k, v = item.get_text().strip().split(":", 1)
                    items[k.strip()] = v.strip()
        return items

    def dismiss_dialogs(self, driver):
        self.uc_click(driver, 'button[data-js="onboarding-cp-close"]', self.timeout)
        self.uc_click(
            driver, 'button[data-testid="action:understood-button"]', self.timeout
        )
        self.browser_initialized = True

    def process_url(self, driver, url: str) -> dict:
        if not self.browser_initialized:
            self.dismiss_dialogs(driver)
        driver.uc_open_with_reconnect(url, reconnect_time=self.reconnect)
        if result_page := self.extract_item_data(driver):
            if not result_page.get("categoria"):
                if not self.headless:
                    driver.post_message("Anúncio com dados incompletos - 🚮")
                return {}
        return result_page

    def extract_item_data(self, driver):
        soup = driver.get_beautiful_soup()

        def get_selector(selector):
            self.highlight_element(driver, selector)
            return soup.select_one(selector)

        categoria = None
        if categoria_elements := soup.select('a[class="andes-breadcrumb__link"]'):
            self.highlight_element(driver, "div[id=breadcrumb]")
            categoria = "|".join(
                i.get_text().strip() for i in categoria_elements if i.get_text().strip()
            )

        nome = None
        if nome_element := get_selector('h1[class="ui-pdp-title"]'):
            nome = nome_element.get_text().strip()

        preço = None
        if preço_element := soup.select_one("meta[itemprop='price']"):
            self.highlight_element(driver, "div[class=ui-pdp-price__second-line]")
            preço = preço_element.get("content")

        if not all([nome, preço, categoria]):
            return {}

        imgs = None
        if img_elements := get_selector(
            'img[class="ui-pdp-image ui-pdp-gallery__figure__image"]'
        ):
            imgs = [i.get("src") for i in img_elements if i.get("src")]

        estado, vendas = None, None
        if info_vendas := get_selector('span[class="ui-pdp-subtitle"]'):
            if len(info_vendas := info_vendas.get_text().strip().split(" | ")) == 2:
                estado, vendas = info_vendas

        nota, avaliações = None, None
        if info_avaliacoes := get_selector('div[class="ui-pdp-review__rating"]'):
            if nota_element := info_avaliacoes.select_one(
                'span[class="ui-pdp-review__rating"]'
            ):
                nota = nota_element.get_text().strip()
            if avaliacoes_element := info_avaliacoes.select_one(
                'span[class="ui-pdp-review__amount"]'
            ):
                avaliações = "".join(
                    re.findall(r"\d+", avaliacoes_element.get_text().strip())
                )

        estoque = None
        if estoque_element := get_selector(
            "span[class=ui-pdp-buybox__quantity__available]"
        ):
            estoque = estoque_element.get_text().strip().split(" ")[0].replace("(", "")

        vendedor = None
        if vendedor_element := get_selector('span[class*="ui-pdp-seller__label-sold"]'):
            if vendedor := vendedor_element.find_next_sibling("span"):
                vendedor = vendedor.get_text().strip()

        try:
            driver.click_visible_elements(
                "[data-testid=action-collapsable-target]",
                timeout=self.timeout,
            )
        except Exception:
            pass

        características, marca, modelo, ean, certificado = None, None, None, None, None
        if características_element := get_selector(
            'div[class="ui-vpp-highlighted-specs__striped-specs"]'
        ):
            características = self.parse_specs(características_element)
            for key, value in características.items():
                if "marca" in key.lower():
                    marca = value
                if "modelo" in key.lower():
                    modelo = value
            ean = self.extrair_ean(características)
            certificado = self.extrair_certificado(características)

        descrição = None
        if descrição_element := get_selector("p[class=ui-pdp-description__content]"):
            descrição = md(str(descrição_element))

        url = self.find_single_url(driver.get_current_url())

        product_id = None
        if product_id_match := re.match(PRODUCT_ID, url):
            product_id = product_id_match[0]

        if descrição:
            if certificado is None:
                certificado = self.match_certificado(descrição)
            if ean is None:
                ean = self.match_ean(descrição)

        return {
            "avaliações": avaliações,
            "categoria": categoria,
            "certificado": certificado,
            "características": características,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
            "descrição": descrição,
            "ean_gtin": ean,
            "estado": estado,
            "estoque": estoque,
            "imagens": imgs,
            "marca": marca,
            "modelo": modelo,
            "nome": nome,
            "nota": nota,
            "preço": preço,
            "product_id": product_id,
            "url": url,
            "vendas": vendas,
            "vendedor": vendedor,
        }

    def wait_for_pagination(self, driver):
        driver.assert_element('nav[aria-label="Paginação"]')

    def input_search_params(self, driver, keyword):
        driver.uc_open_with_reconnect(self.url, reconnect_time=self.reconnect)
        self.dismiss_dialogs(driver)
        for attempt in range(self.retries):
            try:
                if department := CATEGORIES.get(keyword):
                    driver.uc_open_with_reconnect(
                        department, reconnect_time=self.reconnect
                    )
                self.highlight_element(driver, self.input_field)
                driver.type(self.input_field, keyword, timeout=self.timeout)
                self.uc_click(driver, 'button[class="nav-search-btn"]')
                break
            except (NoSuchElementException, ElementNotVisibleException):
                if attempt < self.retries - 1:  # if it's not the last attempt
                    print(f"Attempt {attempt + 1} failed. Retrying...")
                    driver.sleep(2)  # Wait for 1 second before retrying
                else:
                    print(
                        f"Error: Could not find search input field '{self.input_field}' after {self.retries} attempts"
                    )
                    raise  # Re-raise the last exception
