from datetime import datetime
from dataclasses import dataclass
from markdownify import markdownify as md

from .base import TIMEZONE, BaseScraper


@dataclass
class AmericanasScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "americanas"

    @property
    def url(self) -> str:
        return "https://www.americanas.com.br"

    @property
    def input_field(self) -> str:
        return 'input[placeholder="busque aqui seu produto"]'

    @property
    def next_page_button(self) -> str:
        return 'svg[class="src__ArrowRotate-sc-82ugau-2 hWXbQX"]'

    def extract_search_data(self, produto):
        if url := produto.select_one("a"):
            url = self.url + url.get("href")

        if nome := produto.select_one("h3"):
            nome = nome.get_text().strip()

        if avaliações := produto.select_one(
            'span[class*="src__Count-sc-r5o9d7-1.eDRxIY"]'
        ):
            avaliações = avaliações.get_text().strip()

        if imagem := produto.select_one("img"):
            imagem = imagem["src"]

        if preço := produto.select_one('span[class*="list-price"]'):
            preço = preço.get_text().strip()

        if preço_original := produto.select_one('span[class*="sales-price"]'):
            preço_original = preço_original.get_text().strip()

        if not all([nome, preço, imagem, url]):
            return None

        return {
            "nome": nome,
            "preço": preço,
            "preço_Original": preço_original,
            "avaliações": avaliações,
            "imagem": imagem,
            "url": url,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, soup, keyword):
        results = {}
        for item in soup.select('div[class*="ColGridItem"]'):
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

        if nome := get_selector('h1[class*="product-title"]'):
            nome = nome.get_text().strip()

        if preço := get_selector('div[class*="PriceText"]'):
            preço = (
                preço.get_text()
                .strip()
                .replace("R$", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )

        if not all([nome, categoria, preço]):
            return {}

        imagens = []
        if gallery := get_selector('div[class*="Gallery"]'):
            for img in gallery.select("img"):
                if img.get("src"):
                    imagens.append(img.get("src"))

        if avaliações := get_selector('div[class*="Count"]'):
            avaliações = avaliações.get_text().strip("()")

        if nota := get_selector('div[class*="Rating"]'):
            nota = nota.get_text().strip()

        try:
            driver.click_visible_elements(
                'button[class*="accordion-box-expand-button"]',
                timeout=self.timeout,
            )
        except Exception as e:
            print(e)

        if descrição := get_selector('div[data-testid="rich-content-container"]'):
            descrição = md(str(descrição))

        marca, modelo, certificado, ean, product_id = None, None, None, None, None
        if características := self.parse_tables(soup):
            self.uc_click(driver, 'button[aria-expanded="false"]')
            marca = características.get("Marca")
            modelo = características.get("Modelo")
            certificado = self.extrair_certificado(características)
            ean = self.extrair_ean(características)
            product_id = características.get("Código")
        elif descrição:
            if certificado is None:
                certificado = self.match_certificado(descrição)
            if ean is None:
                ean = self.match_ean(descrição)

        return {
            "avaliações": avaliações,
            "categoria": categoria,
            "certificado": certificado,
            "caracterí­sticas": características,
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
            "product_id": product_id,
            "url": driver.get_current_url(),
            "vendas": None,
            "vendedor": None,
        }

    def parse_tables(self, soup) -> dict:
        # Extrai o conteúdo da tabela com dados do produto e transforma em um dict
        variant_data = {}
        for table in soup.select("table"):
            for row in table.select("tr:has(> td:nth-child(2):last-child)"):
                left = row.select_one("td:nth-of-type(1)")
                right = row.select_one("td:nth-of-type(2)")
                if "Informações complementares" in left.get_text():
                    continue
                if "R$" in left.get_text() or "R$" in right.get_text():
                    continue
                variant_data[left.get_text().strip()] = right.get_text().strip()
        return variant_data
