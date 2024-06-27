import json
import random
from pprint import pprint
from datetime import datetime
from dataclasses import dataclass
from time import sleep
import base64

import requests
import typer
from fastcore.xtras import Path
from fastcore.parallel import parallel
from gazpacho import Soup
from seleniumbase import Driver
import pandas as pd
from tqdm.auto import tqdm

RECONNECT = 10
TIMEOUT = 10
SLEEP = 4
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
            ad_block_on=True,
            incognito=True,
            do_not_track=True,
        )
        if self.turnstile:
            try:
                open_the_turnstile_page(driver, self.url)
                click_turnstile_and_verify(driver)
            except Exception:
                pass
        return driver

    @staticmethod
    def capture_full_page_screenshot(driver) -> bytes:
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
                        "scale": 1,
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

    def extract_item_data(self, soup):
        raise NotImplementedError

    def discover_product_urls(self, soup, keyword):
        raise NotImplementedError

    def update_links(self, keyword: str):
        folder = Path.cwd() / "data" / self.name
        folder.mkdir(parents=True, exist_ok=True)
        output_file = folder / f"{self.name}_{keyword.lower().replace(" ", "_")}.json"
        if not output_file.is_file():
            links = {}
        else:
            links = json.loads(output_file.read_text())
        driver = self.init_driver()
        try:
            for url, result in tqdm(links.items(), desc=f"{self.name} - {keyword}"):
                driver.get(url)
                result_page = self.extract_item_data(Soup(driver.get_page_source()))
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
        folder = Path.cwd() / "data" / self.name
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
                    image_data = base64.b64decode(screenshot)
                    with open(
                        screenshot_folder / f"{self.name}_{keyword}_{page}.png", "wb"
                    ) as f:
                        f.write(image_data)

                products = self.discover_product_urls(
                    Soup(driver.get_page_source()), keyword
                )
                print(f"Navegando página {page} da busca '{keyword}'...")
                for k, v in products.items():
                    results[k] = v
                if not driver.is_element_present(self.next_page_button):
                    break
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
