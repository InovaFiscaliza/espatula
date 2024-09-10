from dataclasses import dataclass
from datetime import datetime

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

    def extract_search_data(self, produto):
        if title := produto.select_one('h3[class*="product-card__title"]'):
            if url := title.select_one("a"):
                url = url.get("href")
            if name := title.select_one("span"):
                name = name.text.strip()

        if evals := produto.select_one(
            'span[class*="product-card__reviews-count-text"]'
        ):
            evals = evals.text.strip()

        if nota := produto.select_one('span[data-testid="product-card-rating"]'):
            nota = nota.text.strip()

        if price_lower := produto.select_one(
            'div[class*="product-card__highlight-price"]'
        ):
            price_lower = price_lower.text.strip()

        if price_higher := produto.select_one(
            'div[class*="product-card__installment-text"]'
        ):
            price_higher = price_higher.text.strip()

        if imagem := produto.select_one('img[class*="product-card__image"]'):
            imagem = imagem.get("src")

        if not all([name, price_lower, imagem, url]):
            return None
        return {
            "nome": name,
            "preço": price_lower,
            "preço_original": price_higher,
            "avaliações": evals,
            "imagem": imagem,
            "url": url,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, soup, keyword):
        results = {}
        for item in soup.select('div[class*="css-1enexmx"]'):
            if product_data := self.extract_search_data(item):
                product_data["palavra_busca"] = keyword
                results[product_data["url"]] = product_data
        return results

    def extract_item_data(self, driver):
        soup = driver.get_beautiful_soup()

        def get_selector(selector):
            self.highlight_element(driver, selector)
            return soup.select_one(selector)

        categoria = ""
        if cat := get_selector('div[class*="breadcrumb"]'):
            for a in cat.select("a"):
                if hasattr(a, "get_text") and a.get_text().strip():
                    categoria += f"|{a.get_text().strip()}"

        if nome := get_selector('h1[class*="heading"]'):
            nome = nome.text.strip()

        product_id, marca = None, None
        if origem := get_selector("div.dsvia-flex.css-uoygdh"):
            if product_id := origem.select_one("p"):
                product_id = "".join(
                    d for d in product_id.get_text().strip() if d.isdigit()
                )
            if marca := origem.select_one("a"):
                marca = marca.text.strip()

        if imagens := get_selector('div[class*="Gallery"]'):
            imagens = [img.get("src") for img in imagens.select("img")]

        nota, avaliações = None, None
        if popularidade := get_selector("div[data-testid*='star-rating']"):
            if nota := popularidade.select_one(
                "p[data-testid*='product-rating-value']"
            ):
                nota = nota.text.strip()
            if avaliações := popularidade.select_one(
                "p[data-testid*='product-rating-count']"
            ):
                avaliações = avaliações.text.strip()

        if preço := get_selector("p#product-price"):
            if preço := preço.select_one("span[aria-hidden*='true']"):
                preço = (
                    preço.get_text()
                    .strip()
                    .replace("R$", "")
                    .replace(".", "")
                    .replace(",", ".")
                )

        if vendedor := get_selector("p[data-testid*='sold-by']"):
            if vendedor := vendedor.select_one("a"):
                vendedor = vendedor.text.strip()

        if descrição := get_selector('div[data-testid*="rich-content-container"]'):
            descrição = descrição.text.strip()

        características, modelo, certificado, ean = {}, None, None, None
        try:
            tag = 'p:contains("Características")'
            get_selector(tag)
            driver.uc_click(tag)
            características.update(self.parse_tables(soup, "Características"))
            driver.uc_click('button[aria-label="Fechar"]')
        except Exception as e:
            print(e)
        try:
            tag = 'p:contains("Especificações Técnicas")'
            get_selector(tag)
            driver.uc_click(tag)
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
            "imagens": imagens,
            "descrição": descrição,
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
        if table := soup.select_one(f'div[id*="{id}"'):
            for key in table.select("p"):
                if value := getattr(key, "next_sibling", None):
                    variant_data[key.get_text().strip()] = value.get_text().strip()
        return variant_data
