import os
import base64
import json
import platform
import re
from contextlib import contextmanager
from dataclasses import dataclass
from io import BytesIO
from typing import Generator
from zoneinfo import ZoneInfo


import requests
from fastcore.foundation import L
from fastcore.xtras import Path, loads

from seleniumbase import SB
from seleniumbase.common.exceptions import (
    ElementNotVisibleException,
    NoSuchElementException,
)


TIMEZONE = ZoneInfo("America/Sao_Paulo")
CERTIFICADO = re.compile(
    r"""
    (?ix)                  # Case-insensitive and verbose mode
    ^                      # Start of the string
    (Anatel[:\s]*)?        # Optional "Anatel" followed by colon or spaces
    (                      # Start of main capturing group
        (\d[-\s]*)+        # One or more digits, each optionally followed by hyphen or spaces
    )
""",
    re.VERBOSE,
)

if platform.system() == "Windows":
    if local_app_data := os.environ.get("LOCALAPPDATA"):
        CHROME_DATA_DIR = f"{Path(local_app_data)}/Google/Chrome/User Data"
    else:
        CHROME_DATA_DIR = None
elif platform.system() == "Darwin":  # macOS
    CHROME_DATA_DIR = f"{Path.home()}/Library/Application Support/Google/Chrome"
elif platform.system() == "Linux":
    CHROME_DATA_DIR = f"{Path.home()}/.config/google-chrome"
else:
    CHROME_DATA_DIR = None


@dataclass
class BaseScraper:
    headless: bool = False
    path: Path = Path(os.environ.get("FOLDER", f"{Path(__file__).parent}/data"))
    reconnect: int = int(os.environ.get("RECONNECT", 10))
    timeout: int = int(os.environ.get("TIMEOUT", 5))
    retries: int = int(os.environ.get("RETRIES", 3))
    load_user_profile: bool = False
    demo: bool = False
    guest_mode: bool = True
    incognito: bool = False
    do_not_track: bool = True
    handle_captcha: bool = False

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
        folder = Path(self.path) / self.name
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def links_file(self, keyword: str) -> Path:
        return (
            self.folder / f"{self.name}_{keyword.lower().replace(' ', '_')}_links.json"
        )

    def pages_file(self, keyword: str) -> Path:
        stem = self.links_file(keyword).stem.replace("_links", "_pages")
        return self.links_file(keyword).with_stem(stem)

    def get_links(self, keyword: str) -> dict:
        links_file = self.links_file(keyword)
        if not links_file.is_file():
            return {}
        return loads(links_file.read_text(encoding="utf-8"))

    def get_pages(self, keyword: str) -> dict:
        pages_file = self.pages_file(keyword)
        if not pages_file.is_file():
            return {}
        return loads(pages_file.read_text(encoding="utf-8"))

    def click_captcha(self, driver):
        driver.uc_gui_click_captcha(retry=True)

    @contextmanager
    def browser(self):
        if self.load_user_profile:
            os.environ["ESPATULA_PROFILE_DIR"] = self.name.title()
            user_data_dir = CHROME_DATA_DIR
        else:
            user_data_dir = None
        with SB(
            uc=True,  # Always true
            incognito=self.incognito,
            headless2=self.headless,
            guest_mode=self.guest_mode,
            do_not_track=self.do_not_track,
            user_data_dir=user_data_dir,
        ) as sb:
            sb.driver.maximize_window()
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
        if self.demo:
            try:
                driver.highlight(element, timeout=self.timeout // 2)
            except (NoSuchElementException, ElementNotVisibleException):
                pass

    def get_selector(self, driver, soup, selector):
        self.highlight_element(driver, selector)
        return soup.select_one(selector)

    def uc_click(self, driver, selector, timeout=None):
        self.highlight_element(driver, selector)
        if timeout is None:
            timeout = self.reconnect
        driver.uc_click(selector, timeout=timeout, reconnect_time=timeout)

    def _save_screenshot(self, driver: SB, filename: str):
        folder = self.folder / "screenshots"
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
        if product_id := result_page.get("product_id"):
            return f"{self.name}_{product_id}.pdf"
        return f"{self.name}_{i}.pdf"

    def save_sampled_pages(self, keyword: str, sampled_pages: dict):
        json.dump(
            self.get_pages(keyword) | sampled_pages,
            self.pages_file(keyword).open("w", encoding="utf-8"),
            ensure_ascii=False,
        )

    def process_url(self, driver: SB, url: str) -> dict:
        driver.uc_open_with_reconnect(url, reconnect_time=self.reconnect)
        if result_page := self.extract_item_data(driver):
            if not result_page.get("categoria"):
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
    ) -> Generator[dict, None, None]:
        links = self.get_links(keyword)
        keys = L((i, k) for i, k in enumerate(links.keys()))
        if shuffle:
            keys = keys.shuffle()
        sampled_pages = {}

        with self.browser() as driver:
            driver.set_messenger_theme(location="top_center")
            try:
                for i, url in keys:
                    if not (result_page := self.process_url(driver, url)):
                        del links[url]
                        continue

                    if screenshot:
                        self.save_screenshot(driver, result_page, i)
                    else:
                        result_page["screenshot"] = ""

                    result_page["palavra_busca"] = keyword
                    result_page["indice"] = i
                    output = {**links[url], **result_page}
                    sampled_pages[result_page["url"]] = output
                    yield output
                    if sample and len(sampled_pages) >= sample:
                        break
            finally:
                self.save_sampled_pages(keyword, sampled_pages)
                json.dump(
                    links,
                    self.links_file(keyword).open("w", encoding="utf-8"),
                    ensure_ascii=False,
                )

    def input_search_params(self, driver: SB, keyword: str):
        driver.uc_open_with_reconnect(self.url, reconnect_time=self.reconnect)
        self.highlight_element(driver, self.input_field)
        for attempt in range(self.retries):
            try:
                driver.type(self.input_field, keyword + "\n", timeout=self.timeout)
                break  # Success, exit the function
            except (NoSuchElementException, ElementNotVisibleException):
                if attempt < self.retries - 1:  # if it's not the last attempt
                    driver.post_message(f"Attempt {attempt + 1} failed. Retrying...")
                    driver.sleep(2)  # Wait for 1 second before retrying
                else:
                    print(
                        f"Error: Could not find search input field '{self.input_field}' after {self.retries} attempts"
                    )
                    raise  # Re-raise the last exception

    def go_to_next_page(self, driver):
        for attempt in range(self.retries):
            try:
                if not driver.is_element_present(self.next_page_button):
                    return False
                self.highlight_element(driver, self.next_page_button)
                driver.uc_click(self.next_page_button, timeout=self.timeout)
                return True
            except (NoSuchElementException, ElementNotVisibleException):
                if attempt < self.retries - 1:
                    driver.post_message(
                        f"Attempt {attempt + 1} failed. Retrying to go to next page..."
                    )
                    driver.sleep(1)
                else:
                    print(
                        f"Error: Could not find or click next page button after {self.retries} attempts"
                    )
                    return False
        return False

    def search(
        self, keyword: str, max_pages: int = 10, overwrite: bool = False
    ) -> Generator[dict, None, None]:
        links = {} if overwrite else self.get_links(keyword)
        results = {}
        page = 1
        with self.browser() as driver:
            try:
                self.input_search_params(driver, keyword)
                driver.set_messenger_theme(location="top_center")
                while True:
                    soup = driver.get_beautiful_soup()
                    products = self.discover_product_urls(soup, keyword)
                    if not self.headless:
                        driver.post_message(f"🕷️ Links da página {page} coletados! 🕸️")
                    for url, link_data in products.items():
                        link_data["página_de_busca"] = page
                        results[url] = link_data
                    yield products
                    page += 1
                    if page > max_pages:
                        if not self.headless:
                            driver.post_message(
                                f"Número máximo de páginas atingido - #{max_pages}"
                            )
                        break
                    if not self.go_to_next_page(driver):
                        break
            finally:
                links.update(results)
                json.dump(
                    links,
                    self.links_file(keyword).open("w", encoding="utf-8"),
                    ensure_ascii=False,
                )
