import re
import os
import json
from dataclasses import dataclass
import base64
from pprint import pprint

import requests
from dotenv import find_dotenv, load_dotenv
from fastcore.xtras import Path
from fastcore.parallel import parallel
from gazpacho import Soup
from seleniumbase import Driver
from tqdm.auto import tqdm

load_dotenv(find_dotenv(), override=True)

RECONNECT = int(os.environ.get("RECONNECT", 5))
TIMEOUT = 20
SLEEP = 5
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
DATA = os.environ.get("FOLDER", f"{Path.cwd()}/data")


def open_the_turnstile_page(driver, url):
    driver.uc_open_with_reconnect(url, reconnect_time=RECONNECT)


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

    def init_driver(self):
        driver = Driver(
            headless=self.headless,
            uc=True,
            ad_block_on=False,
            incognito=False,
            do_not_track=False,
        )
        driver.maximize_window()

        if self.turnstile:
            try:
                open_the_turnstile_page(driver, self.url)
                click_turnstile_and_verify(driver)
            except Exception:
                pass
        return driver

    # https://github.com/nirtal85/Selenium-Python-Example/blob/ee919911ca0837c8cb147f8b09b9a63a29215a77/tests/conftest.py#L374
    @staticmethod
    def capture_full_page_screenshot(driver) -> bytes:  #
        """Gets full page screenshot of the current window as a binary data."""
        metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
        return base64.b64decode(
            driver.execute_cdp_cmd(
                "Page.captureScreenshot",
                {
                    "clip": {
                        "x": 0,
                        "y": 0,
                        "width": metrics["contentSize"]["width"],
                        "height": metrics["contentSize"]["height"],
                        "scale": 0.75,
                    },
                    "captureBeyondViewport": True,
                },
            )["data"]
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
            "",
        )
        if match := re.search(CERTIFICADO, certificado):
            # Remove all non-digit characters and check if there are exactly 12 digits
            return re.sub(r"\D", "", match[2])
        return None

    def extract_item_data(self, soup):
        raise NotImplementedError

    def discover_product_urls(self, soup, keyword):
        raise NotImplementedError

    def inspect_pages(self, keyword: str, screenshot: bool = False):
        folder = Path(DATA) / self.name
        folder.mkdir(parents=True, exist_ok=True)
        output_file = folder / f"{self.name}_{keyword.lower().replace(" ", "_")}.json"
        if not output_file.is_file():
            links = {}
        else:
            links = json.loads(output_file.read_text())
        driver = self.init_driver()
        driver.get(self.url)
        try:
            for url, result in tqdm(links.items(), desc=f"{self.name} - {keyword}"):
                driver.uc_open_with_reconnect(url, reconnect_time=RECONNECT)
                result_page = self.extract_item_data(Soup(driver.get_page_source()))
                if screenshot and result_page:
                    result_page["screenshot"] = base64.b64encode(
                        self.capture_full_page_screenshot(driver)
                    ).decode("utf-8")
                result_page["Palavra_Chave"] = keyword
                result.update(result_page)
                links[url].update(result)
        finally:
            json.dump(
                links,
                output_file.open("w"),
                ensure_ascii=False,
            )
            driver.quit()

    def search(self, keyword: str, screenshot: bool = False, md: bool = False):
        folder = Path(DATA) / self.name
        folder.mkdir(parents=True, exist_ok=True)
        output_file = folder / f"{self.name}_{keyword.lower().replace(" ", "_")}.json"
        if not output_file.is_file():
            links = {}
        else:
            links = json.loads(output_file.read_text())
        driver = self.init_driver()
        results = {}
        page = 1
        try:
            driver.get(self.url)
            driver.type(self.input_field, keyword + "\n", timeout=TIMEOUT)
            while True:
                driver.sleep(TIMEOUT)
                if screenshot:
                    screenshot_folder = folder / "screenshots"
                    screenshot_folder.mkdir(parents=True, exist_ok=True)
                    screenshot = self.capture_full_page_screenshot(driver)
                    with open(
                        screenshot_folder / f"{self.name}_{keyword}_{page}.png", "wb"
                    ) as f:
                        f.write(screenshot)

                products = self.discover_product_urls(
                    Soup(driver.get_page_source()), keyword
                )
                print(f"Navegando página {page} da busca '{keyword}'...")
                for k, v in products.items():
                    results[k] = v
                if not driver.is_element_present(self.next_page_button):
                    break
                driver.highlight(self.next_page_button)
                driver.uc_click(self.next_page_button, timeout=TIMEOUT)
                page += 1
            if md:
                mds = parallel(
                    self.get_md_from_url,
                    results.keys(),
                    n_workers=4,
                    pause=SLEEP,
                    threadpool=True,
                    progress=True,
                )
                for i, k in enumerate(results.keys()):
                    results[k]["md"] = mds[i]

        finally:
            links.update(results)
            json.dump(
                links,
                output_file.open("w"),
                ensure_ascii=False,
            )
            driver.quit()
            return results
