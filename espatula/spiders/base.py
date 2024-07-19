import base64
import json
import os
import re
from io import BytesIO
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


import requests
from dotenv import find_dotenv, load_dotenv
from fastcore.foundation import L
from fastcore.xtras import Path, loads
from rich import progress, print
from seleniumbase import SB
from seleniumbase.common.exceptions import (
    ElementNotVisibleException,
    NoSuchElementException,
)
from pypdf import PdfReader, PdfWriter


load_dotenv(find_dotenv(), override=True)

RECONNECT = int(os.environ.get("RECONNECT", 5))
TIMEOUT = int(os.environ.get("TIMEOUT", 10))
FOLDER = Path(os.environ.get("FOLDER", f"{Path(__file__)}/data"))
TIMEZONE = ZoneInfo(os.environ.get("TIMEZONE", "America/Sao_Paulo"))
TODAY = datetime.today().astimezone(TIMEZONE).strftime("%Y%m%d")
CERTIFICADO = re.compile(
    r"""
    (?ix)                  # Case-insensitive and verbose mode
    ^                      # Start of the string
    (Anatel[:\s]*)?        # Optional "Anatel" followed by colon or spaces
    (                      # Start of main capturing group
        (\d[-\s]*)+        # One or more digits, each optionally followed by hyphen or spaces
    )
    $                      # End of the string
""",
    re.VERBOSE,
)

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
        return self.folder / f"{self.name}_{keyword.lower().replace(' ', '_')}.json"

    def get_links(self, keyword: str) -> dict:
        links_file = self.links_file(keyword)
        if not links_file.is_file():
            print(f"Não foram encontrados links de busca para {self.name} - {keyword}")
            print("A coleta de links será efetuada primeiro com as opções padrão")
            self.search(keyword)
            return self.get_links(keyword)
        return loads(links_file.read_text())

    @staticmethod
    def click_turnstile_and_verify(driver):
        try:
            driver.switch_to_frame("iframe")
            driver.uc_click("span.mark")
        except Exception:
            pass

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
            None,
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
            driver.highlight(element)
        except (NoSuchElementException, ElementNotVisibleException):
            pass

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

        with BytesIO() as bytes_stream:
            writer.write(bytes_stream)

        return bytes_stream.getvalue()

    def take_screenshot(self, driver, filename):
        folder = FOLDER / "screenshots"
        folder.mkdir(parents=True, exist_ok=True)
        screenshot = self.capture_full_page_screenshot(driver)
        screenshot = self.compress_images(BytesIO(screenshot))
        with open(folder / filename, "wb") as f:
            f.write(screenshot)

    def save_screenshot(self, driver, result_page, i):
        filename = self.generate_filename(result_page, i)
        self.take_screenshot(driver, filename)
        result_page["screenshot"] = filename

    def generate_filename(self, result_page, i):
        base_filename = f"{self.name}_{TODAY}"
        if product_id := result_page.get("product_id"):
            return f"{base_filename}_{product_id}.pdf"
        return f"{base_filename}_{i}.pdf"

    def save_sampled_pages(self, keyword, sampled_pages):
        output_file = self.links_file(keyword).with_name(
            f"{self.name}_{TODAY}_{keyword.lower().replace(' ', '_')}.json"
        )
        if output_file.is_file():
            old_links = output_file.read_json()
            old_links.update(sampled_pages)
            sampled_pages = old_links

        json.dump(
            sampled_pages,
            output_file.open("w"),
            ensure_ascii=False,
        )

    def process_url(self, driver, url):
        driver.uc_open_with_reconnect(url, reconnect_time=RECONNECT)
        if result_page := self.extract_item_data(driver):
            if not result_page.get("categoria"):
                print(f"{url} inválida - sem categoria - 🚮")
                driver.post_message("Anúncio sem categoria - 🚮")
                return False

        return result_page

    def inspect_pages(
        self,
        keyword: str,
        screenshot: bool = False,
        shuffle: bool = True,
        sample: int = 65,
    ) -> Path:
        links = self.get_links(keyword)
        keys = L((i, k) for i, k in enumerate(links.keys()))
        if shuffle:
            keys = keys.shuffle()
        sampled_pages = {}

        with self.browser() as driver:
            driver.set_messenger_theme(location="center")
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
                    sampled_pages[url] = result_page

                    if sample and len(sampled_pages) >= sample:
                        break

            finally:
                self.save_sampled_pages(keyword, sampled_pages)
                json.dump(
                    links,
                    self.links_file(keyword).open("w"),
                    ensure_ascii=False,
                )

    def input_search_params(self, driver, keyword):
        self.highlight_element(driver, self.input_field)
        driver.type(self.input_field, keyword + "\n", timeout=TIMEOUT)

    def search(self, keyword: str, max_pages: int = 10):
        links = self.get_links(keyword)
        results = {}
        page = 1
        with self.browser() as driver:
            try:
                self.input_search_params(driver, keyword)
                driver.set_messenger_theme(location="bottom_center")
                while True:
                    driver.sleep(TIMEOUT)
                    products = self.discover_product_urls(driver, keyword)
                    print(f"Navegando página {page} da busca '{keyword}'...")
                    driver.post_message(f"🕷️ Links da página {page} coletados! 🕸️")
                    for k, v in products.items():
                        v["página_de_busca"] = page
                        results[k] = v
                    if page >= max_pages:
                        driver.post_message(
                            f"Número máximo de páginas atingido - {max_pages}!"
                        )
                        driver.sleep(TIMEOUT)
                        break
                    if not driver.is_element_present(self.next_page_button):
                        break
                    self.highlight_element(driver, self.next_page_button)
                    driver.uc_click(self.next_page_button, timeout=TIMEOUT)
                    page += 1
            finally:
                links.update(results)
                json.dump(
                    links,
                    self.links_file(keyword).open("w"),
                    ensure_ascii=False,
                )
                return results
