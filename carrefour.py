from dataclasses import dataclass
from datetime import datetime

from gazpacho import Soup
from base import TIMEZONE, BaseScraper


@dataclass
class CarrefourScraper(BaseScraper):
    name: str = "carrefour"
    url: str = "https://www.carrefour.com.br/"
    input_field: str = 'input[placeholder="Pesquise por produtos ou marcas"]'
    next_page_button: str = (
        "li.carrefourbr-carrefour-components-0-x-Pagination_NextButtonContainer>a>div"
    )
    turnstile: bool = True

    def input_search_params(self, driver, keyword):
        driver.uc_open_with_reconnect(
            self.url
            + "celulares-smartphones-e-smartwatches/smartphones#crfint=hm-tlink|celulares-e-smartphones|smartphones|1"
        )
        # self.highlight_element(driver, self.input_field)
        # driver.type(self.input_field, keyword, timeout=TIMEOUT)
        # driver.uc_click('button[aria-label="Buscar produtos"]', timeout=TIMEOUT)

    def extract_search_data(self, product_tag):
        if hasattr(
            url := product_tag.find(
                "a", attrs={"class": "product-summary"}, mode="first", partial=True
            ),
            "attrs",
        ):
            url = url.attrs.get("href")

        if nome := product_tag.find(
            "h2", attrs={"class": "productName"}, mode="first", partial=True
        ):
            nome = nome.strip()

        if hasattr(
            imagem := product_tag.find(
                "img",
                attrs={"class": "product-summary"},
                mode="first",
                partial=True,
            ),
            "attrs",
        ):
            imagem = imagem.attrs.get("src")

        if preço_original := product_tag.find(
            "span", attrs={"class": "listPrice"}, mode="first", partial=True
        ):
            preço_original = preço_original.strip()

        if preço := product_tag.find(
            "span", attrs={"class": "spotPriceValue"}, mode="first", partial=True
        ):
            preço = preço.strip()

        url = self.url + url
        return {
            "nome": nome,
            "preço_original": preço_original,
            "preço": preço,
            "imagem": imagem,
            "url": url,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, soup, keyword: str):
        results = {}
        for div in soup.find(
            "div", attrs={"class": "galleryItem"}, mode="all", partial=True
        ):
            if product_data := self.extract_search_data(div):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def extract_item_data(self, driver):
        soup = Soup(driver.get_page_source())
        if categoria := soup.find(
            "span", attrs={"class": "breadcrumb"}, mode="all", partial=True
        ):
            categoria = "|".join(i.strip() for i in categoria if i.strip() != "")
        if marca := soup.find(
            "span", attrs={"class": "productBrandName"}, mode="first", partial=True
        ):
            marca = marca.strip()

        if vendedor := soup.find(
            "span", attrs={"class": "carrefourSeller"}, mode="first", partial=True
        ):
            vendedor = vendedor.strip()

        if desconto := soup.find(
            "span", attrs={"class": "PriceSavings"}, mode="first", partial=True
        ):
            desconto = desconto.strip()

        if cod_produto := soup.find(
            "span",
            attrs={"class": "product-identifier__value"},
            mode="first",
            partial=True,
        ):
            cod_produto = cod_produto.strip()

        if descrição := soup.find(
            "td",
            attrs={"class": "ItemSpecifications"},
            mode="first",
            partial=True,
        ):
            descrição = descrição.attrs.get("data-specification")

        if imagens := soup.find(
            "img", attrs={"class": "thumbImg"}, mode="all", partial=True
        ):
            imagens = [i.attrs.get("src") for i in imagens if hasattr(i, "attrs")]

        certificado, ean = None, None
        if características := self.parse_tables(soup):
            certificado = self.extrair_certificado(características)
            ean = self.extrair_ean(características)

        return {
            "categoria": categoria,
            "marca": marca,
            "vendedor": vendedor,
            "desconto": desconto,
            "product_id": cod_produto,
            "certificado": certificado,
            "ean_gtin": ean,
            "descrição": descrição,
            "características": características,
            "imagens": imagens,
            "data": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def parse_tables(self, soup):
        # Extrai o conteúdo da tabela com dados do produto e transforma em um dict
        table_data = {}
        if table := soup.find(
            "div", attrs={"class": "table_main_container"}, mode="first"
        ):
            for rows in table.find("tr", mode="all"):
                if len(col := rows.find("th", mode="all")) == 2:
                    table_data[col[0].text.strip()] = col[1].text.strip()
        return table_data
