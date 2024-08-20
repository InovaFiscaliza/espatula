import os
import base64
import json
import re
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass
from io import BytesIO
from zoneinfo import ZoneInfo


import requests
from dotenv import find_dotenv, load_dotenv
from fastcore.foundation import L
from fastcore.xtras import Path, loads
from pypdf import PdfReader, PdfWriter
from rich import print, progress
from seleniumbase import SB
from seleniumbase.common.exceptions import (
    ElementNotVisibleException,
    NoSuchElementException,
)

from espatula.constantes import (
    CERTIFICADO,
)

load_dotenv(find_dotenv(), override=True)
TIMEZONE = ZoneInfo("America/Sao_Paulo")
TODAY = datetime.today().astimezone(TIMEZONE).strftime("%Y%m%d")
FOLDER = Path(os.environ.get("FOLDER", f"{Path(__file__)}/data"))
RECONNECT = int(os.environ.get("RECONNECT", 10))
TIMEOUT = int(os.environ.get("TIMEOUT", 5))


@dataclass
class BaseScraper:
    headless: bool = True
    ad_block_on: bool = True
    incognito: bool = False
    do_not_track: bool = True
    turnstile: bool = False

    @property
    def name(self):
        raise NotImplementedError

    @property
    def url(self):
        raise NotImplementedError

    @property
    def input_field(self):
        raise NotImplementedError

    @property
    def next_page_button(self):
        raise NotImplementedError

    @property
    def folder(self) -> Path:
        folder = FOLDER / self.name
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def links_file(self, keyword: str) -> Path:
        return (
            self.folder / f"{self.name}_{keyword.lower().replace(' ', '_')}_links.json"
        )

    def get_links(self, keyword: str) -> dict:
        links_file = self.links_file(keyword)
        if not links_file.is_file():
            print(f"Não foram encontrados links de busca para {self.name} - {keyword}")
            print(
                "Execute primeiramente a busca de links pelo método 'search(keyword)'"
            )
            raise FileNotFoundError(f"Arquivo {links_file} não encontrado")
        return loads(links_file.read_text())

    @staticmethod
    def click_turnstile_and_verify(sb):
        try:
            sb.switch_to_frame("iframe")
            sb.uc_click("span.mark")
        except Exception as e:
            print(e)

    @contextmanager
    def browser(self):
        with SB(
            headless=self.headless,
            uc=True,  # Always true
            ad_block_on=self.ad_block_on,
            incognito=self.incognito,
            do_not_track=self.do_not_track,
        ) as sb:
            sb.driver.maximize_window()
            sb.uc_open_with_reconnect(self.url, reconnect_time=RECONNECT)
            if self.turnstile:
                self.click_turnstile_and_verify(sb)
            yield sb

    @staticmethod
    # https://chromedevtools.github.io/devtools-protocol/tot/Page#method-printToPDF
    def capture_full_page_screenshot(driver) -> bytes:
        """Gets full page screenshot as a pdf searchable."""
        url = f"{driver.command_executor._url}/session/{driver.session_id}/chromium/send_command_and_get_result"
        params = {
            "displayHeaderFooter": True,
            "printBackground": True,
            "preferCSSPageSize": False,
            "scale": 1,
        }

        body = json.dumps({"cmd": "Page.printToPDF", "params": params})
        response = driver.command_executor._request("POST", url, body).get("value")
        return base64.b64decode(
            response.get("data"),
            validate=True,
        )

    @staticmethod
    def get_md_from_url(url):
        url = "https://r.jina.ai/" + url
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return None

    @staticmethod
    def extrair_certificado(caracteristicas: dict) -> str | None:
        certificado = next(
            (
                caracteristicas.get(k, "")
                for k in caracteristicas
                if any(s in k.lower() for s in ("certifica", "homologa", "anatel"))
            ),
            "",
        )
        if match := re.search(CERTIFICADO, certificado):
            # Remove all non-digit characters
            return re.sub(r"\D", "", match[2]).zfill(12)
        return None

    @staticmethod
    def extrair_ean(caracteristicas: dict) -> str:
        return next(
            (
                caracteristicas.get(k, "")
                for k in caracteristicas
                if any(s in k.lower() for s in ("ean", "gtin", "digo de barras"))
            ),
            None,
        )

    def extract_item_data(self, driver):
        raise NotImplementedError

    def discover_product_urls(self, driver, keyword):
        raise NotImplementedError

    def highlight_element(self, driver, element):
        if self.headless:
            return
        try:
            driver.highlight(element, timeout=TIMEOUT // 2)
        except (NoSuchElementException, ElementNotVisibleException) as e:
            print(e)

    @staticmethod
    def compress_images(pdf_stream):
        reader = PdfReader(pdf_stream)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        if reader.metadata is not None:
            writer.add_metadata(reader.metadata)

        for page in writer.pages:
            for img in page.images:
                img.replace(img.image, quality=80)
            page.compress_content_streams(level=9)

        bytes_stream = BytesIO()
        writer.write(bytes_stream)
        return bytes_stream.getvalue()

    def _save_screenshot(self, driver: SB, filename: str):
        folder = FOLDER / "screenshots"
        folder.mkdir(parents=True, exist_ok=True)
        screenshot = self.capture_full_page_screenshot(driver)
        screenshot = self.compress_images(BytesIO(screenshot))
        with open(folder / filename, "wb") as f:
            f.write(screenshot)

    def save_screenshot(self, sb: SB, result_page: dict, i: int):
        filename = self.generate_filename(result_page, i)
        self._save_screenshot(sb.driver, filename)
        result_page["screenshot"] = filename

    def generate_filename(self, result_page: dict, i: int):
        base_filename = f"{self.name}_{TODAY}"
        if product_id := result_page.get("product_id"):
            return f"{base_filename}_{product_id}.pdf"
        return f"{base_filename}_{i}.pdf"

    def save_sampled_pages(self, keyword: str, sampled_pages: dict):
        output_file = self.links_file(keyword).with_name(
            f"{self.name}_{TODAY}_{keyword.lower().replace(' ', '_')}.json"
        )
        json.dump(
            sampled_pages,
            output_file.open("w"),
            ensure_ascii=False,
        )
        self.output_file = output_file

    def process_url(self, driver: SB, url: str) -> dict:
        driver.uc_open_with_reconnect(url, reconnect_time=RECONNECT)
        if result_page := self.extract_item_data(driver):
            if not result_page.get("categoria"):
                print(f"Falha ao navegar {url}")
                if not self.headless:
                    driver.post_message("Anúncio sem categoria - 🚮")
                return {}

        return result_page

    def inspect_pages(
        self,
        keyword: str,
        screenshot: bool = False,
        sample: int = 65,
        shuffle: bool = False,
    ) -> Path:
        links = self.get_links(keyword)
        keys = L((i, k) for i, k in enumerate(links.keys()))
        if shuffle:
            keys = keys.shuffle()
        sampled_pages = {}

        with self.browser() as driver:
            driver.set_messenger_theme(location="top_center")
            try:
                for i, url in progress.track(
                    keys, description=f"{self.name} - {keyword}"
                ):
                    if not (result_page := self.process_url(driver, url)):
                        del links[url]
                        continue

                    if screenshot:
                        self.save_screenshot(driver, result_page, i)

                    result_page["palavra_busca"] = keyword
                    result_page["index"] = i
                    sampled_pages[result_page["url"]] = result_page

                    if sample and len(sampled_pages) >= sample:
                        break
            finally:
                self.save_sampled_pages(keyword, sampled_pages)
                json.dump(
                    links,
                    self.links_file(keyword).open("w"),
                    ensure_ascii=False,
                )
        return sampled_pages

    def input_search_params(self, driver: SB, keyword: str):
        self.highlight_element(driver, self.input_field)
        driver.type(self.input_field, keyword + "\n", timeout=TIMEOUT)

    def search(self, keyword: str, max_pages: int = 10, overwrite: bool = True):
        links = {} if overwrite else self.get_links(keyword)
        results = {}
        page = 1
        with self.browser() as driver:
            try:
                self.input_search_params(driver, keyword)
                driver.set_messenger_theme(location="top_center")
                while True:
                    driver.sleep(TIMEOUT)
                    products = self.discover_product_urls(driver, keyword)
                    print(f"Navegando página {page} da busca '{keyword}'...")
                    if not self.headless:
                        driver.post_message(f"🕷️ Links da página {page} coletados! 🕸️")
                    for url, link_data in products.items():
                        link_data["página_de_busca"] = page
                        results[url] = link_data
                    if not driver.is_element_present(self.next_page_button):
                        break
                    page += 1
                    if page > max_pages:
                        if not self.headless:
                            driver.post_message(
                                f"Número máximo de páginas atingido - {max_pages}!"
                            )
                        driver.sleep(TIMEOUT)
                        break
                    self.highlight_element(driver, self.next_page_button)
                    driver.uc_click(self.next_page_button, timeout=TIMEOUT)

            finally:
                links.update(results)
                json.dump(
                    links,
                    self.links_file(keyword).open("w"),
                    ensure_ascii=False,
                )
                return results
