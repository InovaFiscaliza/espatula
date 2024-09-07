from dataclasses import dataclass
from datetime import datetime

from bs4 import BeautifulSoup

from .base import TIMEZONE, BaseScraper


@dataclass
class CasasBahiaScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "casasbahia"

    @property
    def url(self) -> str:
        return "https://www.casasbahia.com.br"

    @property
    def input_field(self) -> str:
        return 'input[id="search-form-input"]'

    @property
    def next_page_button(self) -> str:
        return 'a[aria-label="Próxima página"]'

    def extract_product_data(self, produto):
        title = produto.select_one("h3.product-card__title")
        if title:
            relative_url = title.select_one("a")
            relative_url = relative_url["href"] if relative_url else None
            name = title.select_one("span")
            name = name.text.strip() if name else None
        
        evals = produto.select_one("span.product-card__reviews-count-text")
        evals = evals.text.strip() if evals else None
        
        nota = produto.select_one("span[data-testid='product-card-rating']")
        nota = nota.text.strip() if nota else None
        
        price_lower = produto.select_one("div.product-card__highlight-price")
        price_lower = price_lower.text.strip() if price_lower else None
        
        price_higher = produto.select_one("div.product-card__installment-text")
        price_higher = price_higher.text.strip() if price_higher else None
        
        imgs = produto.select_one("img.product-card__image")
        imgs = imgs["src"] if imgs else None
        if not all([name, price_lower, imgs, relative_url]):
            return None
        return {
            "nome": name,
            "preço": price_lower,
            "preço_original": price_higher,
            "avaliações": evals,
            "imagem": imgs,
            "url": relative_url,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, driver, keyword):
        soup = BeautifulSoup(driver.get_page_source(), 'html.parser')
        results = {}
        for item in soup.select("div.css-1enexmx"):
            if product_data := self.extract_product_data(item):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def extract_item_data(self, driver):
        soup = BeautifulSoup(driver.get_page_source(), 'html.parser')
        categoria = soup.select_one("div.breadcrumb")
        if categoria:
            categoria = " | ".join(
                a.text.strip() for a in categoria.select("a") if a.text.strip()
            )

        nome = soup.select_one("h1.heading")
        nome = nome.text.strip() if nome else None
        if not all([nome, categoria]):
            return None

        product_id, marca = None, None
        origem = soup.select_one("div.dsvia-flex.css-uoygdh")
        if origem:
            product_id = origem.select_one("p")
            product_id = "".join(d for d in product_id.text.strip() if d.isdigit()) if product_id else None
            marca = origem.select_one("a")
            marca = marca.text.strip() if marca else None

        # if imagens := soup.find("div", {"class": "Gallery"}, mode="first"):
        #     self.highlight_element(driver, 'div:contains("Gallery")')
        #     imagens = [
        #         getattr(i, "attrs", {}).get("src")
        #         for i in imagens.find("img", mode="all")
        #     ]

        nota, avaliações = None, None
        if popularidade := soup.find(
            "div", attrs={"data-testid": "star-rating"}, mode="first"
        ):
            # self.highlight_element(driver, "div[data-testid=mod-row]")
            if nota := popularidade.find(
                "p", attrs={"data-testid": "product-rating-value"}, mode="first"
            ):
                nota = nota.strip()
            # if avaliações := popularidade.find(
            #     "p", attrs={"data-testid": "product-rating-count"}, mode="first"
            # ):
            #     avaliações = avaliações.strip()

        if preço := soup.find("p", attrs={"id": "product-price"}, mode="first"):
            # self.highlight_element(driver, "div[data-testid=mod-productprice]")
            if preço := preço.find("span", attrs={"aria-hidden": "true"}, mode="first"):
                preço = (
                    preço.strip().replace("R$", "").replace(".", "").replace(",", ".")
                )
            else:
                preço = None

        else:
            preço = None

        if vendedor := soup.find("p", attrs={"data-testid": "sold-by"}, mode="first"):
            if vendedor := vendedor.find("a", mode="first"):
                vendedor = vendedor.strip()
            else:
                vendedor = None

        # if descrição := soup.find(
        #     "div", attrs={"data-testid": "rich-content-container"}, mode="first"
        # ):
        #     self.highlight_element(driver, "div[data-testid=rich-content-container]")
        #     descrição = descrição.text.strip()

        características, modelo, certificado, ean = {}, None, None, None
        try:
            tag = 'p:contains("Características")'
            self.highlight_element(driver, tag)
            driver.uc_click(tag)
            soup = BeautifulSoup(driver.get_page_source(), 'html.parser')
            características.update(self.parse_tables(soup, "Características"))
            driver.uc_click('button[aria-label="Fechar"]')
        except Exception as e:
            print(e)
        try:
            tag = 'p:contains("Especificações Técnicas")'
            self.highlight_element(driver, tag)
            driver.uc_click(tag)
            soup = BeautifulSoup(driver.get_page_source(), 'html.parser')
            características.update(self.parse_tables(soup, "Especificações Técnicas"))

        except Exception as e:
            print(e)

        if características:
            modelo, certificado, ean = (
                características.get("Código de Referência"),
                self.extrair_certificado(características),
                self.extrair_ean(características),
            )

        return {
            "nome": nome,
            "categoria": categoria,
            "preço": preço,
            "nota": nota,
            "avaliações": avaliações,
            # "imagens": imagens,
            # "descrição": descrição,
            "vendedor": vendedor,
            "marca": marca,
            "modelo": modelo,
            "certificado": certificado,
            "ean_gtin": ean,
            "características": características,
            "product_id": product_id,
            "url": driver.get_current_url(),
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def parse_tables(self, soup, id) -> dict:
        # Extrai o conteúdo da tabela com dados do produto e transforma em um dict
        variant_data = {}
        if table := soup.find("div", attrs={"id": id}, mode="first"):
            for rows in table.find("div", attrs={"class": "css-cs5a0t"}, mode="all"):
                if (key := rows.find("p", mode="first")) and (
                    value := rows.find("span", mode="first")
                ):
                    key = key.strip()
                    value = value.strip()
                    variant_data[key] = value
        return variant_data
