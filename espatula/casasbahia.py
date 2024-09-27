from dataclasses import dataclass
from datetime import datetime

from markdownify import markdownify as md

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
        return 'button[aria-label*="Próxima página"]'

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

        if imagem := produto.select_one('img[class*="product-card__image"]'):
            imagem = imagem.get("src")

        if not all([name, price_lower, imagem, url]):
            return None
        return {
            "nome": name,
            "preço": price_lower,
            "avaliações": evals,
            "imagem": imagem,
            "url": url,
            "data": datetime.now().astimezone(TIMEZONE).strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def discover_product_urls(self, soup, keyword):
        results = {}
        for item in soup.select('div[id^="product-card"]'):
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

        if preço := get_selector("p#product-price"):
            if preço := preço.select_one("span[aria-hidden*='true']"):
                preço = (
                    preço.get_text()
                    .strip()
                    .replace("R$", "")
                    .replace(".", "")
                    .replace(",", ".")
                ).strip()

        if not all([categoria, nome, preço]):
            return {}

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

        if vendedor := get_selector("p[data-testid*='sold-by']"):
            if vendedor := vendedor.select_one("a"):
                vendedor = vendedor.text.strip()

        if descrição := get_selector('div[id="product-description"]'):
            descrição = md(str(descrição))

        características, modelo, certificado, ean = {}, None, None, None
        try:
            tag = 'svg[data-testid="Características"]'
            self.uc_click(driver, tag, timeout=self.timeout)
            soup = driver.get_beautiful_soup()
            características.update(self.parse_tables(soup, "Características"))
            self.uc_click(driver, 'button[aria-label="Fechar"]', timeout=self.timeout)
        except Exception as e:
            if not self.headless:
                driver.post_message(e)
        try:
            tag = 'svg[data-testid="Especificações-Técnicas"]'
            self.uc_click(driver, tag, timeout=self.timeout)
            soup = driver.get_beautiful_soup()
            características.update(self.parse_tables(soup, "Especificações Técnicas"))
            self.uc_click(driver, 'button[aria-label="Fechar"]', timeout=self.timeout)

        except Exception as e:
            if not self.headless:
                driver.post_message(e)

        if características:
            modelo, certificado, ean = (
                características.get("Código de Referência"),
                self.extrair_certificado(características),
                self.extrair_ean(características),
            )
        elif descrição:
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
            "vendedor": vendedor,
        }

    def parse_tables(self, soup, id_) -> dict:
        # Extrai o conteúdo da tabela com dados do produto e transforma em um dict
        variant_data = {}
        if table := soup.select_one(f'div[id*="{id_}"]'):
            for key in table.select("p"):
                if value := getattr(key, "next_sibling", None):
                    variant_data[key.get_text().strip()] = value.get_text().strip()
        return variant_data
