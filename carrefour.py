import json
import random
from pprint import pprint
from datetime import datetime
from dataclasses import dataclass

import requests
import typer
from fastcore.xtras import Path
from gazpacho import Soup
from seleniumbase import Driver
import pandas as pd
from tqdm.auto import tqdm


RECONNECT = 10
TIMEOUT = 10
URL = "https://www.carrefour.com.br"
KEYWORDS = [
    "smartphone",
    "carregador para smartphone",
    "power bank",
    "tv box",
    "bluetooth",
    "wifi",
    "drone",
    "bateria celular",
    "reforçador sinal",
    "transmissor",
    "transceptor",
    "bloqueador sinal",
    "jammer",
    "flipper zero",
]


def open_the_turnstile_page(driver, url):
    driver.uc_open_with_reconnect(url, reconnect_time=RECONNECT)


def click_turnstile_and_verify(driver):
    driver.switch_to_frame("iframe")
    driver.uc_click("span.mark")


def extract_product_data(div):
    if hasattr(
        link := div.find(
            "a", attrs={"class": "product-summary"}, mode="first", partial=True
        ),
        "attrs",
    ):
        link = link.attrs.get("href")

    if name := div.find(
        "h2", attrs={"class": "productName"}, mode="first", partial=True
    ):
        name = name.strip()

    if hasattr(
        img := div.find(
            "img",
            attrs={"class": "product-summary"},
            mode="first",
            partial=True,
        ),
        "attrs",
    ):
        img = img.attrs.get("src")

    if price_higher := div.find(
        "span", attrs={"class": "listPrice"}, mode="first", partial=True
    ):
        price_higher = price_higher.strip()

    if price_lower := div.find(
        "span", attrs={"class": "spotPriceValue"}, mode="first", partial=True
    ):
        price_lower = price_lower.strip()

    if all([name, link, price_lower, img]):
        link = URL + link
        return {
            "Nome": name,
            "Preço_Original": price_higher,
            "Preço": price_lower,
            "Imagem": img,
            "Link": link,
            # "MD": get_md_from_url(link),
            "Data_Atualização": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }
    else:
        print(f"Missing data for product: {link}")
        return None


def get_md_from_url(url):
    url = "https://r.jina.ai/" + url
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None


def discover_product_urls(soup, keyword: str):
    results = {}
    for div in soup.find(
        "div", attrs={"class": "galleryItem"}, mode="all", partial=True
    ):
        if product_data := extract_product_data(div):
            product_data["Palavra_Chave"] = keyword
            results[product_data["Link"]] = product_data
    return results


def extract_item_data(soup):
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
        "span", attrs={"class": "product-identifier__value"}, mode="first", partial=True
    ):
        cod_produto = cod_produto.strip()

    if spec := soup.find(
        "td",
        attrs={"class": "ItemSpecifications"},
        mode="first",
        partial=True,
    ):
        spec = spec.attrs.get("data-specification")

    if imgs := soup.find("img", attrs={"class": "thumbImg"}, mode="all", partial=True):
        imgs = [i.attrs.get("src") for i in imgs if hasattr(i, "attrs")]

    table = parse_tables(soup)

    hm = ""
    for k in table:
        if "certifica" in k.lower():
            hm = table[k]
            break
        if "homologa" in k.lower():
            hm = table[k]
            break

    return {
        "Categoria": categoria,
        "Marca": marca,
        "Vendedor": vendedor,
        "Desconto": desconto,
        "Código_Produto": cod_produto,
        "Certificado_de_Homologação": hm,
        "Descrição": spec,
        "Tabela_Dados": table,
        "Imagens": imgs,
        "Data_Atualização": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }


def parse_tables(soup):
    # Extrai o conteúdo da tabela com dados do produto e transforma em um dict
    table_data = {}
    if table := soup.find("div", attrs={"class": "table_main_container"}, mode="first"):
        for rows in table.find("tr", mode="all"):
            if len(col := rows.find("th", mode="all")) == 2:
                table_data[col[0].text.strip()] = col[1].text.strip()
    return table_data


# def product_search(keyword):
#     results = []
#     with SB(
#         uc=True, maximize=True, headless=True, incognito=True, ad_block_on=True
#     ) as sb:
#         open_the_turnstile_page(sb)
#         try:
#             click_turnstile_and_verify(sb)
#         except Exception:
#             pass
#         input_field = "input[placeholder='Pesquise por produtos ou marcas']"
#         submit = "button[aria-label='Buscar produtos']"
#         sb.type(input_field, keyword)
#         sb.uc_click(submit, timeout=15)
#         results.extend(discover_product_urls(Soup(sb.get_page_source())))
#         element = "li.carrefourbr-carrefour-components-0-x-Pagination_NextButtonContainer>a>div"
#         while True:
#             try:
#                 # sb.assert_element(element)
#                 sb.highlight(element)
#                 sb.uc_click(element, timeout=15)
#                 sb.sleep(10)
#                 results.extend(discover_product_urls(Soup(sb.get_page_source())))
#             except Exception:
#                 break
#         for d in results:
#             #     sb.uc_open_with_tab(d["Link"])
#             #     sb.sleep(10)
#             #     d.update(extract_item_data(sb))
#             d.update({"Palavra_Chave": keyword})
#     return results


# def search(keyword):
#     results = product_search(keyword)
#     results = {d["Link"]: d for d in results}
#     file = Path.cwd() / "data" / f"carrefour_{keyword}.json"
#     if not file.exists():
#         output = []
#     else:
#         output = json.loads(file.read_text())
#     output.update(results)
#     json.dump(
#         output,
#         file.open("w"),
#         ensure_ascii=False,
#     )


@dataclass
class CarrefourScraper:
    name: str = "carrefour"
    url: str = "https://www.carrefour.com.br/"
    headless: bool = True

    def init_driver(self):
        driver = Driver(
            headless=self.headless,
            uc=True,
            ad_block_on=True,
            incognito=True,
            do_not_track=True,
        )
        driver.sleep(TIMEOUT)
        try:
            open_the_turnstile_page(driver, self.url)
            click_turnstile_and_verify(driver)
        except Exception:
            pass
        return driver

    def update_links(self, keyword: str):
        output_file = Path.cwd() / "data" / f"{self.name}_{keyword}.json"
        if not output_file.is_file():
            links = {}
        else:
            links = json.loads(output_file.read_text())
        driver = self.init_driver()
        try:
            for url, result in links.items():
                driver.get(url)
                result_page = extract_item_data(Soup(driver.get_page_source()))
                result_page["Palavra_Chave"] = keyword
                result.update(result_page)
                links[url].update(result)
                pprint(result)
        finally:
            json.dump(
                links,
                output_file.open("w"),
                ensure_ascii=False,
            )
            driver.quit()

    def search(self, keyword: str, screenshot: bool = False):
        output_file = Path.cwd() / "data" / f"{self.name}_{keyword}.json"
        if not output_file.is_file():
            links = {}
        else:
            links = json.loads(output_file.read_text())
        driver = self.init_driver()
        element = "li.carrefourbr-carrefour-components-0-x-Pagination_NextButtonContainer>a>div"
        page = 1
        results = {}
        try:
            while True:
                driver.get(
                    f"https://www.{self.name}.com.br/busca/{keyword}?maxItemsPerPage=60&page={page}"
                )
                driver.sleep(random.randint(5, 10))
                if screenshot:
                    screenshot_folder = output_file.parent / "screenshots"
                    screenshot_folder.mkdir(exist_ok=True)
                    driver.save_screenshot(
                        screenshot_folder / f"{self.name}_{keyword}_{page}.png"
                    )
                searched = discover_product_urls(
                    Soup(driver.get_page_source()), keyword
                )
                for k, d in searched.items():
                    results[k] = d
                if not driver.find_element(element):
                    break
                page += 1
        finally:
            links.update(results)
            json.dump(
                links,
                output_file.open("w"),
                ensure_ascii=False,
            )
            driver.quit()
            return results

    def inspect(self, links: dict) -> dict:
        driver = self.init_driver()
        try:
            for link, result in tqdm(links.items(), desc="Inspecting Products"):
                driver.get(link)
                result_page = extract_item_data(Soup(driver.get_page_source()))
                result.update(result_page)
                links[link].update(result)

        finally:
            driver.quit()
            return links

    def scrape(self, keyword: str, screenshot: bool = False):
        try:
            results = self.search(keyword, screenshot)
            links = self.inspect(results)
        finally:
            output_file = Path.cwd() / "data" / f"{self.name}_{keyword}.json"
            json.dump(links, output_file.open("w"), ensure_ascii=False)

    def main(self, keyword: str = None, screenshot: bool = False):
        try:
            if keyword is None:
                for keyword in KEYWORDS:
                    self.scrape(keyword, screenshot)
            else:
                self.scrape(keyword, screenshot)
        finally:
            jsons = (
                (Path.cwd() / "data" / self.name)
                .ls()
                .filter(lambda x: x.suffix == ".json")
            )
            dfs = jsons.map(
                lambda x: pd.DataFrame(json.loads(Path(x).read_text()).values())
            )
            df = pd.concat(dfs, ignore_index=True)
            df.sort_values("Data_Atualização", ascending=False, inplace=True)
            df.to_excel(Path.cwd() / "data" / f"{self.name}.xlsx", index=False)


if __name__ == "__main__":

    def main(keyword: str = None, headless: bool = True, screenshot: bool = False):
        scraper = CarrefourScraper(headless)
        scraper.main(keyword, screenshot)

    typer.run(main)
