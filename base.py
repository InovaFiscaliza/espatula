import base64
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime

import requests
from dotenv import find_dotenv, load_dotenv
from fastcore.foundation import L
from fastcore.xtras import Path
from gazpacho import Soup
from seleniumbase import Driver
from seleniumbase.common.exceptions import (
    ElementNotVisibleException,
    NoSuchElementException,
)
from tqdm.auto import tqdm
from zoneinfo import ZoneInfo

load_dotenv(find_dotenv(), override=True)

RECONNECT = int(os.environ.get("RECONNECT", 5))
TIMEOUT = int(os.environ.get("TIMEOUT", 20))
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

CERTIFICADO = re.compile(r"(?i)^(Anatel[:\s]*)?((\d[-\s]*){12})$")
DATA = Path(os.environ.get("FOLDER", f"{Path.cwd()}/data"))
TIMEZONE = ZoneInfo(os.environ.get("TIMEZONE", "America/Sao_Paulo"))


def click_turnstile_and_verify(driver):
    driver.switch_to_frame("iframe")
    driver.uc_click("span.mark")


@dataclass
class BaseScraper:
    name: str
    url: str
    input_field: str
    next_page_button: str
    headless: bool = True
    turnstile: bool = False

    @property
    def folder(self):
        folder = DATA / self.name
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def init_driver(self):
        driver = Driver(
            headless=self.headless,
            uc=True,
            ad_block_on=True,
            incognito=False,
            do_not_track=True,
        )
        driver.maximize_window()
        driver.uc_open_with_reconnect(self.url, reconnect_time=RECONNECT)
        if self.turnstile:
            try:
                click_turnstile_and_verify(driver)
            except Exception:
                pass
        return driver

    # https://chromedevtools.github.io/devtools-protocol/tot/Page#method-printToPDF
    @staticmethod
    def capture_full_page_screenshot(driver) -> bytes:  #
        """Gets full page screenshot as a pdf searchable."""
        url = f"{driver.command_executor._url}/session/{driver.session_id}/chromium/send_command_and_get_result"
        params = {
            "displayHeaderFooter": True,
            "printBackground": True,
            "preferCSSPageSize": True,
            "scale": 0.75,
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
        chrs = caracteristicas.copy()
        certificado = next(
            (
                caracteristicas.pop(k, "")
                for k in chrs
                if any(s in k.lower() for s in ("certifica", "homologação", "anatel"))
            ),
            None,
        )
        if match := re.search(CERTIFICADO, certificado):
            # Remove all non-digit characters and check if there are exactly 12 digits
            return re.sub(r"\D", "", match[2])
        return None

    @staticmethod
    def extrair_ean(caracteristicas: dict) -> str:
        chrs = caracteristicas.copy()
        return next(
            (
                caracteristicas.pop(k, "")
                for k in chrs
                if any(s in k.lower() for s in ("ean", "gtin"))
            ),
            None,
        )

    def extract_item_data(self, driver):
        raise NotImplementedError

    def discover_product_urls(self, soup, keyword):
        raise NotImplementedError

    def highlight_element(self, driver, element):
        if self.headless:
            return
        try:
            driver.highlight(element)
        except (NoSuchElementException, ElementNotVisibleException):
            pass

    def take_screenshot(self, driver, filename):
        folder = DATA / "screenshots"
        folder.mkdir(parents=True, exist_ok=True)
        screenshot = self.capture_full_page_screenshot(driver)
        filename = folder / filename
        with open(filename, "wb") as f:
            f.write(screenshot)
        return f"{filename.parent.name}/{filename.name}"

    def inspect_pages(self, keyword: str, screenshot: bool = False, sample: int = 65):
        links_file = (
            self.folder / f"{self.name}_{keyword.lower().replace(" ", "_")}.json"
        )
        if not links_file.is_file():
            links = {}
        else:
            links = json.loads(links_file.read_text())
        driver = self.init_driver()
        sample_keys = L(links.keys()).shuffle()[:sample]
        sample_links = {k: links[k] for k in sample_keys}
        try:
            for i, (url, result) in enumerate(
                tqdm(sample_links.items(), desc=f"{self.name} - {keyword}")
            ):
                try:
                    driver.uc_open_with_reconnect(url, reconnect_time=RECONNECT)
                    if result_page := self.extract_item_data(driver):
                        if not result_page.get("categoria"):
                            del links[url]
                            continue
                        if screenshot:
                            filename = f"{self.name}_{datetime.today().astimezone(TIMEZONE).strftime("%Y%m%d")}"
                            if product_id := result_page.get("product_id"):
                                filename = f"{filename}_{product_id}.pdf"
                            else:
                                filename = f"{filename}_{url.split("/")[-1]}.pdf"
                            result_page["screenshot"] = self.take_screenshot(
                                driver, filename
                            )
                        result_page["palavra_busca"] = keyword
                        result.update(result_page)
                        sample_links[url].update(result)
                except Exception as e:
                    print(e)
                    print(f"Erro ao processar {url}")
        finally:
            json.dump(
                sample_links,
                links_file.with_name(
                    f"{self.name}_{datetime.today().astimezone(TIMEZONE).strftime("%Y%m%d")}_{keyword.lower().replace(' ', '_')}.json"
                ).open("w"),
                ensure_ascii=False,
            )
            driver.quit()

    def input_search_params(self, driver, keyword):
        self.highlight_element(driver, self.input_field)
        driver.type(self.input_field, keyword + "\n", timeout=TIMEOUT)

    def search(self, keyword: str):
        output_file = (
            self.folder / f"{self.name}_{keyword.lower().replace(" ", "_")}.json"
        )
        if not output_file.is_file():
            links = {}
        else:
            links = json.loads(output_file.read_text())
        driver = self.init_driver()
        results = {}
        page = 1
        try:
            self.input_search_params(driver, keyword)
            while True:
                driver.sleep(TIMEOUT)
                products = self.discover_product_urls(
                    Soup(driver.get_page_source()), keyword
                )
                print(f"Navegando página {page} da busca '{keyword}'...")
                # driver.set_messenger_theme(location="bottom_center")
                # driver.post_message(f"🕷️ Raspando links da página {page}! 🕸️")
                for k, v in products.items():
                    v["página_de_busca"] = page
                    results[k] = v
                if not driver.is_element_present(self.next_page_button):
                    break
                self.highlight_element(driver, self.next_page_button)
                driver.uc_click(self.next_page_button, timeout=TIMEOUT)
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
