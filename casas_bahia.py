from dataclasses import dataclass
from datetime import datetime

from gazpacho import Soup
from base import TIMEZONE, BaseScraper


@dataclass
class CasasBahiaScraper(BaseScraper):
    name: str = "casas_bahia"
    url: str = "https://www.casasbahia.com.br"
    input_field: str = 'input[id="search-form-input"]'
    next_page_button: str = 'a[aria-label="Próxima página"]'

    def extract_product_data(self, produto):
        if title := produto.find("h3", attrs={"class": "product-card__title"}):
            if relative_url := title.find("a"):
                relative_url = relative_url.attrs.get("href")
            if name := title.find("span", mode="first"):
                name = name.strip()
        if evals := produto.find(
            "span", attrs={"class": "product-card__reviews-count-text"}, mode="first"
        ):
            evals = evals.strip()
        if nota := produto.find(
            "span", attrs={"data-testid": "product-card-rating"}, mode="first"
        ):
            nota = nota.strip()
        if price_lower := produto.find(
            "div", {"class": "product-card__highlight-price"}, mode="first"
        ):
            price_lower = price_lower.strip()

        if price_higher := produto.find(
            "div", {"class": "product-card__installment-text"}, mode="first"
        ):
            price_higher = price_higher.strip()

        if hasattr(
            imgs := produto.find(
                "img", attrs={"class": "product-card__image"}, mode="first"
            ),
            "attrs",
        ):
            imgs = imgs.attrs.get("src")
        if not all([name, price_lower, imgs, relative_url]):
            return None
        return {
            "nome": name,
            "preço": price_lower,
            "preço_original": price_higher,
            "avaliações": evals,
            "imagem": imgs,
            "url": self.url + relative_url,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, soup, keyword):
        results = {}
        for item in soup.find(
            "div",
            attrs={"class": "css-1enexmx"},
            partial=True,
            mode="all",
        ):
            if product_data := self.extract_product_data(item):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def extract_item_data(self, driver):
        soup = Soup(driver.get_page_source())
        if categoria := soup.find(
            "div", attrs={"class": "breadcrumb"}, mode="first", partial=True
        ):
            # self.highlight_element(driver, "div:contains(breadcrumb)")
            categoria = " | ".join(
                i.strip()
                for i in categoria.find("a", mode="all")
                if hasattr(i, "strip") and i.strip()
            )

        if nome := soup.find("h1", attrs={"class": "heading"}, mode="first"):
            # self.highlight_element(driver, 'h1:contains("product-title")')
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

        # if descrição := soup.find(
        #     "div", attrs={"data-testid": "rich-content-container"}, mode="first"
        # ):
        #     self.highlight_element(driver, "div[data-testid=rich-content-container]")
        #     descrição = descrição.text.strip()

        try:
            driver.uc_click('svg[data-testid="Especificações Técnicas"]')
        except:
            pass

        marca, modelo, certificado, ean, product_id = None, None, None, None, None
        if características := self.parse_tables(soup):
            marca, modelo, certificado, ean, product_id = (
                características.get("Marca"),
                características.get("Modelo"),
                self.extrair_certificado(características),
                self.extrair_ean(características),
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
        if table := soup.find(
            "div", attrs={"id": "Especificações Técnicas"}, mode="first"
        ):
            if rows := table.find(
                "div", attrs={"data-testid": "dsvia-base-div"}, mode="all"
            ):
                variant_data.update(
                    {row.find("p").strip(): row.find("span").strip() for row in rows}
                )
        return variant_data
