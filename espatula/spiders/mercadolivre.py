import re
from dataclasses import dataclass
from datetime import datetime

from gazpacho import Soup

from base import RECONNECT, TIMEOUT, TIMEZONE, BaseScraper

CATEGORIES = {
    "smartphone": "https://www.mercadolivre.com.br/c/celulares-e-telefones#menu=categories"
}


@dataclass
class MercadoLivreScraper(BaseScraper):
    name: str = "ml"
    url: str = "https://www.mercadolivre.com.br"
    input_field: str = 'input[id="cb1-edit"]'
    next_page_button: str = 'a[title="Seguinte"]'
    pages: int = None

    @staticmethod
    def find_single_url(text):
        pattern = (
            r"https://(?:produto\.|www\.)mercadolivre\.com\.br.*?(?:-_JM|(?=\?)|(?=#))"
        )
        match = re.search(pattern, text)

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
        soup = Soup(driver.get_page_source())
        results = {}
        for item in soup.find(
            "li", attrs={"class": "ui-search-layout__item"}, partial=True, mode="all"
        ):
            if product_data := self.extract_search_data(item):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def parse_specs(self, element) -> dict:
        specs = {}
        if tables := element.find("table", attrs={"class": "andes-table"}, mode="all"):
            specs.update(self.parse_tables(tables))
        if lists := element.find(
            "div", attrs={"class": "ui-pdp-list ui-pdp-specs__list"}, mode="all"
        ):
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
            for row in table.find("tr", mode="all")
        }

    @staticmethod
    def parse_lists(lists: str) -> dict:
        items = {}
        for li in lists.find("li", mode="all"):
            if item := li.find("p"):
                k, v = item.strip().split(":", 1)
                items[k.strip()] = v.strip()
        return items

    def extract_item_data(self, driver):
        soup = Soup(driver.get_page_source())

        if categoria := soup.find(
            "a", attrs={"class": "andes-breadcrumb__link"}, mode="all"
        ):
            self.highlight_element(driver, "div[id=breadcrumb]")
            categoria = "|".join(
                i.strip() for i in categoria if hasattr(i, "strip") and i.strip()
            )

        if imgs := soup.find(
            "img",
            attrs={"class": "ui-pdp-image ui-pdp-gallery__figure__image"},
            mode="all",
        ):
            self.highlight_element(driver, "figure[class=ui-pdp-gallery__figure]")
            imgs = [getattr(i, "attrs", {}).get("src") for i in imgs]

        estado, vendas = None, None
        if info_vendas := soup.find(
            "span", attrs={"class": "ui-pdp-subtitle"}, mode="first"
        ):
            self.highlight_element(driver, "span[class=ui-pdp-subtitle]")
            if len(info_vendas := info_vendas.strip().split(" | ")) == 2:
                estado, vendas = info_vendas
            # elif len(info_vendas) == 1:
            #     vendas = info_vendas[0].strip()
            #     if estado := soup.find(
            #         "p", attrs={"class": "andes-badge__content"}, mode="first"
            #     ):
            #         estado = estado.strip()

        if nome := soup.find("h1", attrs={"class": "ui-pdp-title"}, mode="first"):
            self.highlight_element(driver, "h1[class=ui-pdp-title]")
            nome = nome.strip()

        nota, avaliações = None, None
        if info_avaliacoes := soup.find(
            "div", attrs={"class": "ui-pdp-header__info"}, mode="first"
        ):
            self.highlight_element(driver, "div[class=ui-pdp-header__info]")
            if nota := info_avaliacoes.find(
                "span", attrs={"class": "ui-pdp-review__rating"}, mode="first"
            ):
                nota = nota.strip()
            if avaliações := info_avaliacoes.find(
                "span", attrs={"class": "ui-pdp-review__amount"}, mode="first"
            ):
                avaliações = "".join(re.findall(r"\d+", avaliações.strip()))

        if preço := soup.find("meta", attrs={"itemprop": "price"}, mode="first"):
            self.highlight_element(driver, "div[class=ui-pdp-price__second-line]")
            preço = getattr(preço, "attrs", {}).get("content")

        if estoque := soup.find(
            "span", attrs={"class": "quantity__available"}, mode="first"
        ):
            self.highlight_element(
                driver, "span[class=ui-pdp-buybox__quantity__available]"
            )
            estoque = estoque.strip().split(" ")[0].replace("(", "")

        if vendedor := soup.find(
            "div", attrs={"class": "ui-pdp-seller__header"}, mode="first"
        ):
            self.highlight_element(driver, "div[class=ui-pdp-seller__header__title]")
            vendedor = vendedor.strip()

        if soup.find("button", attrs={"data-testid": "action-collapsable-target"}):
            driver.uc_click("button[data-testid=action-collapsable-target]")

        if soup.find("a", attrs={"data-testid": "action-collapsable-target"}):
            driver.uc_click("a[data-testid=action-collapsable-target]")

        marca, modelo, ean, certificado = None, None, None, None
        if características := soup.find(
            "div",
            attrs={"class": "ui-vpp-highlighted-specs__striped-specs"},
            mode="first",
        ):
            self.highlight_element(
                driver, "div[class=ui-vpp-highlighted-specs__striped-specs]"
            )
            características = self.parse_specs(características)
            marca = características.get("Marca")
            modelo = características.get("Modelo")
            ean = self.extrair_ean(características)
            certificado = self.extrair_certificado(características)

        if descrição := soup.find(
            "p", attrs={"class": "ui-pdp-description__content"}, mode="first"
        ):
            self.highlight_element(driver, "p[class=ui-pdp-description__content]")
            descrição = descrição.strip()

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
            "product_id": driver.current_url.split("/")[-1],
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def input_search_params(self, driver, keyword):
        if department := CATEGORIES.get(keyword):
            driver.uc_open_with_reconnect(department, reconnect_time=RECONNECT)
        self.highlight_element(driver, self.input_field)
        driver.type(self.input_field, keyword + "\n", timeout=TIMEOUT)
