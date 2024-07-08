from datetime import datetime
from dataclasses import dataclass
from gazpacho import Soup

from base import BaseScraper, TIMEZONE


@dataclass
class AmericanasScraper(BaseScraper):
    name: str = "americanas"
    url: str = "https://www.americanas.com.br"
    input_field: str = 'input[placeholder="busque aqui seu produto"]'
    next_page_button: str = 'svg[class="src__ArrowRotate-sc-82ugau-2 hWXbQX"]'

    def extract_search_data(self, produto):
        if relative_url := produto.find("a"):
            relative_url = relative_url.attrs.get("href")
        if nome := produto.find("h3", mode="first"):
            nome = nome.strip()
        if avaliações := produto.find(
            "span", attrs={"class": "src__Count-sc-r5o9d7-1 eDRxIY"}, mode="first"
        ):
            avaliações = avaliações.strip()
        if preço := produto.find("span", {"class": "list-price"}, mode="first"):
            preço = preço.strip()

        if preço_original := produto.find(
            "span", {"class": "sales-price"}, mode="first"
        ):
            preço_original = preço_original.strip()

        if hasattr(
            imagens := produto.find("img", mode="first"),
            "attrs",
        ):
            imagens = imagens.attrs.get("src")
        return {
            "nome": nome,
            "preço": preço,
            "preço_Original": preço_original,
            "avaliações": avaliações,
            "imagem": imagens,
            "url": self.url + relative_url,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, soup, keyword):
        results = {}
        for item in soup.find(
            "div",
            attrs={
                "class": "col__StyledCol-sc-1snw5v3-0 ehOuCD theme-grid-col src__ColGridItem-sc-122lblh-1 cJnBan"
            },
            partial=True,
            mode="all",
        ):
            if product_data := self.extract_search_data(item):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def extract_item_data(self, driver):
        soup = Soup(driver.get_page_source())

        if categoria := soup.find(
            "div", attrs={"data-testid": "breadcrumb"}, mode="first", partial=False
        ):
            self.highlight_element(driver, "div:contains(breadcrumb)")
            categoria = " | ".join(
                i.strip()
                for i in categoria.find("a", mode="all")
                if hasattr(i, "strip") and i.strip()
            )

        if nome := soup.find("h1", attrs={"class": "product-title"}, mode="first"):
            self.highlight_element(driver, 'h1:contains("product-title")')
            nome = nome.strip()

        # if imagens := soup.find("div", {"class": "Gallery"}, mode="first"):
        #     self.highlight_element(driver, 'div:contains("Gallery")')
        #     imagens = [
        #         getattr(i, "attrs", {}).get("src")
        #         for i in imagens.find("img", mode="all")
        #     ]

        # nota, avaliações = None, None
        # if popularidade := soup.find(
        #     "div", attrs={"data-testid": "mod-row"}, mode="first"
        # ):
        #     self.highlight_element(driver, "div[data-testid=mod-row]")
        #     if popularidade := popularidade.find(
        #         "span", attrs={"format": "score-count"}, mode="first"
        #     ):
        #         nota, avaliações = popularidade.text.strip().split(" ")
        #         avaliações = avaliações.replace("(", "").replace(")", "")

        if preço := soup.find("div", attrs={"class": "priceSales"}, mode="first"):
            # self.highlight_element(driver, "div[data-testid=mod-productprice]")
            preço.text.strip().replace("R$", "").replace(".", "").replace(",", ".")

        else:
            preço = None

        # if descrição := soup.find(
        #     "div", attrs={"data-testid": "rich-content-container"}, mode="first"
        # ):
        #     self.highlight_element(driver, "div[data-testid=rich-content-container]")
        #     descrição = descrição.text.strip()

        marca, modelo, certificado, ean, product_id = None, None, None, None, None
        if características := self.parse_tables(soup):
            marca, modelo, certificado, ean = (
                características.get("Marca"),
                características.get("Modelo"),
                self.extrair_certificado(características),
                características.get("EAN"),
                características.get("Código"),
            )

        return {
            "nome": nome,
            "categoria": categoria,
            "preço": preço,
            # "nota": nota,
            # "avaliações": avaliações,
            # "imagens": imagens,
            # "descrição": descrição,
            "marca": marca,
            "modelo": modelo,
            "certificado": certificado,
            "ean_gtin": ean,
            "características": características,
            "product_id": product_id,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def parse_tables(self, soup) -> dict:
        # Extrai o conteúdo da tabela com dados do produto e transforma em um dict
        variant_data = {}
        for table in soup.find("table", mode="all"):
            if rows := table.find("td", mode="all"):
                if rows[0].strip() == "Informações complementares":
                    continue
                variant_data.update(
                    {
                        k.strip(): v.strip()
                        for k, v in zip(rows[::2], rows[1::2])
                        if ("R$" not in k.strip() and "R$" not in v.strip())
                    }
                )
        return variant_data
