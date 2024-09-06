import re
from dataclasses import dataclass
from datetime import datetime

from bs4 import BeautifulSoup

from .base import TIMEZONE, BaseScraper

CATEGORIES = {
    "smartphone": "https://www.mercadolivre.com.br/c/celulares-e-telefones#menu=categories"
}

URL = re.compile(
    r"https://(?:produto\.|www\.)mercadolivre\.com\.br.*?(?:-_JM|(?=\?)|(?=#))"
)

PRODUCT_ID = re.compile(r"(MLB-?\d+)")


@dataclass
class MercadoLivreScraper(BaseScraper):
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
        match = re.search(URL, text)

        # Return the first non-empty match
        return match[0] if match else text

    def extract_search_data(self, item):
        if hasattr(
            url := item.find("a", attrs={"class": "ui-search-link"}, mode="first"),
            "attrs",
        ):
            url = self.find_single_url(url.attrs.get("href"))

        if hasattr(
            imagem := item.find(
                "img",
                attrs={"class": "ui-search-result"},
                partial=True,
                mode="first",
            ),
            "attrs",
        ):
            imagem = imagem.attrs.get("src")

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

        if avaliações := item.find(
            "span",
            attrs={"class": "ui-search-reviews__amount"},
            partial=True,
            mode="first",
        ):
            avaliações = avaliações.strip()

        if nota := item.find(
            "span",
            attrs={"class": "ui-search-reviews__rating-number"},
            partial=True,
            mode="first",
        ):
            nota = nota.strip()

        if not all([nome, preço, imagem]):
            return False

        return {
            "nome": nome,
            "preço": preço,
            "avaliações": avaliações,
            "nota": nota,
            "imagem": imagem,
            "url": url,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, driver, keyword):
        soup = BeautifulSoup(driver.get_page_source(), 'html.parser')
        results = {}
        for item in soup.find_all("li", class_="ui-search-layout__item"):
            if product_data := self.extract_search_data(item):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def parse_specs(self, element) -> dict:
        specs = {}
        if tables := element.find_all("table", class_="andes-table"):
            specs.update(self.parse_tables(tables))
        if lists := element.find_all("div", class_="ui-pdp-list ui-pdp-specs__list"):
            specs.update(self.parse_lists(lists))
        return specs

    @staticmethod
    def parse_tables(tables: list) -> dict:
        """
        Parses tables from the product detail page to extract specifications and returns them as a dictionary.
        This method can be easily tested in isolation.
        """
        # Implement table parsing logic
        return {
            row.find("th").text: row.find("td").text
            for table in tables
            for row in table.find_all("tr")
        }

    @staticmethod
    def parse_lists(lists: list) -> dict:
        items = {}
        for list_div in lists:
            for li in list_div.find_all("li"):
                if item := li.find("p"):
                    k, v = item.text.strip().split(":", 1)
                    items[k.strip()] = v.strip()
        return items

    def extract_item_data(self, driver):
        soup = BeautifulSoup(driver.get_page_source(), 'html.parser')

        categoria = None
        if categoria_elements := soup.find_all("a", class_="andes-breadcrumb__link"):
            self.highlight_element(driver, "div[id=breadcrumb]")
            categoria = "|".join(
                i.text.strip() for i in categoria_elements if i.text.strip()
            )

        imgs = None
        if img_elements := soup.find_all("img", class_="ui-pdp-image ui-pdp-gallery__figure__image"):
            self.highlight_element(driver, "figure[class=ui-pdp-gallery__figure]")
            imgs = [i.get("src") for i in img_elements if i.get("src")]

        estado, vendas = None, None
        if info_vendas := soup.find("span", class_="ui-pdp-subtitle"):
            self.highlight_element(driver, "span[class=ui-pdp-subtitle]")
            if len(info_vendas := info_vendas.text.strip().split(" | ")) == 2:
                estado, vendas = info_vendas

        nome = None
        if nome_element := soup.find("h1", class_="ui-pdp-title"):
            self.highlight_element(driver, "h1[class=ui-pdp-title]")
            nome = nome_element.text.strip()

        nota, avaliações = None, None
        if info_avaliacoes := soup.find("div", class_="ui-pdp-header__info"):
            self.highlight_element(driver, "div[class=ui-pdp-header__info]")
            if nota_element := info_avaliacoes.find("span", class_="ui-pdp-review__rating"):
                nota = nota_element.text.strip()
            if avaliacoes_element := info_avaliacoes.find("span", class_="ui-pdp-review__amount"):
                avaliações = "".join(re.findall(r"\d+", avaliacoes_element.text.strip()))

        preço = None
        if preço_element := soup.find("meta", attrs={"itemprop": "price"}):
            self.highlight_element(driver, "div[class=ui-pdp-price__second-line]")
            preço = preço_element.get("content")

        estoque = None
        if estoque_element := soup.find("span", class_="quantity__available"):
            self.highlight_element(driver, "span[class=ui-pdp-buybox__quantity__available]")
            estoque = estoque_element.text.strip().split(" ")[0].replace("(", "")

        vendedor = None
        if vendedor_element := soup.find("div", class_="ui-pdp-seller__header"):
            self.highlight_element(driver, "div[class=ui-pdp-seller__header__title]")
            vendedor = vendedor_element.text.strip()

        if soup.find("button", attrs={"data-testid": "action-collapsable-target"}):
            self.highlight_element(driver, "button[data-testid=action-collapsable-target]")
            driver.uc_click("button[data-testid=action-collapsable-target]")

        if soup.find("a", attrs={"data-testid": "action-collapsable-target"}):
            self.highlight_element(driver, 'a[title="Ver descrição completa"]')
            driver.uc_click('a[title="Ver descrição completa"]')

        marca, modelo, ean, certificado = None, None, None, None
        if características_element := soup.find("div", class_="ui-vpp-highlighted-specs__striped-specs"):
            self.highlight_element(driver, "div[class=ui-vpp-highlighted-specs__striped-specs]")
            características = self.parse_specs(características_element)
            marca = características.get("Marca")
            modelo = características.get("Modelo")
            ean = self.extrair_ean(características)
            certificado = self.extrair_certificado(características)

        descrição = None
        if descrição_element := soup.find("p", class_="ui-pdp-description__content"):
            self.highlight_element(driver, "p[class=ui-pdp-description__content]")
            descrição = descrição_element.text.strip()

        url = self.find_single_url(driver.get_current_url())

        product_id = None
        if product_id_match := re.match(PRODUCT_ID, url):
            product_id = product_id_match[0]

        return {
            "categoria": categoria,
            "imagens": imgs,
            "estado": estado,
            "vendas": vendas,
            "nome": nome,
            "nota": nota,
            "avaliações": avaliações,
            "preço": preço,
            "estoque": estoque,
            "vendedor": vendedor,
            "marca": marca,
            "modelo": modelo,
            "certificado": certificado,
            "ean_gtin": ean,
            "características": características,
            "descrição": descrição,
            "url": url,
            "product_id": product_id,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def input_search_params(self, driver, keyword):
        if department := CATEGORIES.get(keyword):
            driver.uc_open_with_reconnect(department, reconnect_time=self.reconnect)
        self.highlight_element(driver, self.input_field)
        driver.type(self.input_field, keyword + "\n", timeout=self.timeout)
