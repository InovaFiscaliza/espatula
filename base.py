import re
import json
from dataclasses import dataclass
import base64
from pprint import pprint

import requests
from fastcore.xtras import Path
from fastcore.parallel import parallel
from gazpacho import Soup
from seleniumbase import Driver
from tqdm.auto import tqdm

RECONNECT = 5
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

SMARTPHONES = [
    "Galaxy M33 5G",
    "Z Flip5 (256GB)",
    "A03",
    "A03 Core",
    "A03 Core (New colors)",
    "A03s",
    "A04",
    "A04e",
    "A04s",
    "A05 (128GB)",
    "A05s (128GB)",
    "A12",
    "A13",
    "A13 EE",
    "A14 (128GB)",
    "A14 (64GB)",
    "A14 5G (128GB)",
    "A14 5G (64GB)",
    "A14 EE (128GB)",
    "A15 (128GB)",
    "A15 (256GB)",
    "A15 5G (128GB)",
    "A15 5G (128GB) EE",
    "A15 5G (256GB)",
    "A22",
    "A22 5G",
    "A23",
    "A23 5G",
    "A24",
    "A25 5G (128GB)",
    "A25 5G (256GB)",
    "A32",
    "A32 5G",
    "A32 EE",
    "A33 5G",
    "A33 5G EE",
    "A34 5G (128GB)",
    "A34 5G (256GB)",
    "A34 5G EE (128GB)",
    "A34 5G EE (256GB)",
    "A35 5G (128GB)",
    "A35 5G (256GB)",
    "A35 5G EE (256GB)",
    "A52",
    "A52 5G",
    "A52s 5G",
    "A52s 5G (new)",
    "A53 5G",
    "A54 5G (128GB)",
    "A54 5G (256GB)",
    "A54 5G EE (128GB)",
    "A54 5G EE (256GB)",
    "A55 5G (128GB)",
    "A55 5G (256GB)",
    "A55 5G EE (256GB)",
    "A72",
    "A73 5G",
    "Antagus Ex Phone A9",
    "B3",
    "B6",
    "B9",
    "BCE01",
    "BCE03",
    "Blade A3",
    "Blade V50 Design",
    "C66",
    "CA11",
    "CF550",
    "CT30 XP",
    "CT40 XP",
    "CX-906",
    "Camon 19 Neo",
    "Dolphin CN80",
    "Dolphin CN85",
    "Dolphin CT60",
    "EF501R",
    "F MAX 2",
    "FLIP VITA 4G",
    "FLIP VITA DUO",
    "FLIP VITA LITE",
    "Flip Vita 3G",
    "Galaxy A13 5G",
    "Galaxy S24+ ",
    "HOT 11 PLAY",
    "HOT 20 5G",
    "HOT 30",
    "HOT 30i",
    "HOT 40i",
    "HT-705 3G Kids",
    "HT-705G Go",
    "Infinix HOT 20i",
    "KG5K",
    "M12",
    "M13",
    "M14 5G",
    "M15 5G (128GB)",
    "M22",
    "M23",
    "M23 5G",
    "M23 Lite",
    "M23 Pro",
    "M30",
    "M32",
    "M34 5G (128GB)",
    "M50",
    "M52 5G",
    "M53 5G",
    "M54 5G (128GB)",
    "M54 5G (256GB)",
    "M55 5G (256GB)",
    "M62",
    "Motorola Edge 30",
    "Motorola Edge 30 Fusion",
    "Motorola Edge 30 Neo",
    "Motorola Edge 40 ",
    "Motorola Edge 40 Neo",
    "Motorola Moto E13",
    "Motorola Moto g52",
    "Motorola Razr 40",
    "Motorola Razr 40 Ultra",
    "Motorola edge 30 Ultra",
    "Motorola moto G04s",
    "Motorola moto G24 Power",
    "Motorola moto G34 5G",
    "Motorola moto G84 5G",
    "Motorola moto e22",
    "Motorola moto e32",
    "Motorola moto g04",
    "Motorola moto g14",
    "Motorola moto g23",
    "Motorola moto g24",
    "Motorola moto g32",
    "Motorola moto g42",
    "Motorola moto g53 5G",
    "Motorola moto g54 5G",
    "Motorola moto g73 5G",
    "Multi F 2",
    "Multi G Pro 3",
    "Multi H 5G",
    "Multi Up 4G",
    "Multilaser E 2",
    "Multilaser F Pro 2",
    "Multilaser G 3 ",
    "Multilaser G Max 2",
    "NOKIA 105",
    "NOKIA C01 Plus",
    "NOTE 12",
    "NOTE 30 5G",
    "NT-1714G",
    "Nokia 105 4G",
    "Nokia 110 4G",
    "Nokia 2660 Flip",
    "Nokia C12",
    "Nokia C2 2nd edition",
    "Nokia C21 Plus",
    "Nokia G11 Plus",
    "Nokia G21",
    "Nokia G60 5G",
    "Note 12 Pro",
    "Note20 (new)",
    "Note20 Ultra (new)",
    "P26",
    "P28",
    "P38",
    "PCE01",
    "PCS02P HIT MAX",
    "PCS02P HIT PLUS",
    "PCS02RG HIT MAX",
    "PCS02SG HIT MAX",
    "POCO C40",
    "POCO M4 5G",
    "POCO X5 5G",
    "POCO X5 PRO 5G",
    "POCO X6 5G",
    "POCO X6 PRO 5G",
    "POP 7",
    "POSITIVO P41",
    "POSITIVO P51",
    "Poco C65",
    "Poco X3 Pro",
    "Positivo Q20",
    "Pova Neo 2",
    "Pova4",
    "REDMI A3",
    "ROG PHONE 6",
    "ROG PHONE 6 PRO",
    "ROG Phone 5",
    "ROG Phone 5s",
    "ROG Phone 6D",
    "ROG Phone 7",
    "ROG Phone 7 PRO",
    "Redmi 10 5G",
    "Redmi 10C",
    "Redmi 12 5G",
    "Redmi 12C",
    "Redmi 13 C",
    "Redmi 9",
    "Redmi 9A",
    "Redmi Note 10 Pro",
    "Redmi Note 10S",
    "Redmi Note 11S",
    "Redmi Note 12",
    "Redmi Note 12 5G",
    "Redmi Note 12 Pro",
    "Redmi Note 13",
    "Redmi Note 13 5G",
    "Redmi Note 13 Pro 5G",
    "Rog Phone 8",
    "S20 FE (128GB)",
    "S20 FE (256GB)",
    "S20 FE 5G",
    "S21 5G",
    "S21 FE 5G (128GB) - Carregador",
    "S21 FE 5G (256GB)",
    "S21 FE 5G (256GB) - Carregador",
    "S21 FE 5G 128GB",
    "S21 FE 5G EE",
    "S21 FE 5G EE (128GB) - Carregador",
    "S21 FE 5G EE (256GB) - Carregador",
    "S21 Ultra 5G (256)",
    "S21 Ultra 5G (512)",
    "S21+ 5G (128)",
    "S21+ 5G (256)",
    "S22 5G (128GB)",
    "S22 5G (128GB) - Carregador",
    "S22 5G (256GB)",
    "S22 5G (256GB) - Carregador",
    "S22 5G EE",
    "S22 5G EE (128GB) - Carregador",
    "S22 Ultra 5G (256GB)",
    "S22 Ultra 5G (512GB)",
    "S22+ 5G (128GB)",
    "S22+ 5G (256GB)",
    "S23 5G (128GB)",
    "S23 5G (256GB)",
    "S23 5G (512GB)",
    "S23 5G EE",
    "S23 5G EE (256GB)",
    "S23 FE (128GB)",
    "S23 FE (256GB)",
    "S23 FE (256GB) EE",
    "S23 Ultra 5G (1TB)",
    "S23 Ultra 5G (256GB)",
    "S23 Ultra 5G (512GB)",
    "S23+ 5G (256GB)",
    "S23+ 5G (512GB)",
    "S24 (128GB)",
    "S24 (128GB) Exclusive",
    "S24 (256GB)",
    "S24 (256GB) ",
    "S24 (256GB) EE",
    "S24 (256GB) Exclusive",
    "S24 (512GB)",
    "S24 (512GB) Exclusive",
    "S24 Ultra (1TB)",
    "S24 Ultra (1TB) Exclusive",
    "S24 Ultra (256GB)",
    "S24 Ultra (256GB) Exclusive",
    "S24 Ultra (512GB)",
    "S24 Ultra (512GB) EE",
    "S24 Ultra (512GB) Exclusive",
    "S24+ (256GB)",
    "S24+ (256GB) Exclusive",
    "S24+ (512GB)",
    "S24+ (512GB) Exclusive",
    "SF650",
    "SMART 6",
    "SPARK 10 5G",
    "SPARK 10 C",
    "SPARK 10 Pro",
    "SPARK Go 2023",
    "ScanPal EDA57",
    "Smart 6",
    "Smart 7",
    "Smart 8 Pro",
    "Spark 20 Pro",
    "Spark 8C",
    "Spark GO 2024",
    "T612B",
    "T771K",
    "TCL 30 5G",
    "TCL 30 SE",
    "TCL 305i",
    "TCL 40 R 5G",
    "TCL 40 SE",
    "TCL 405",
    "Tab A7 Lite",
    "Tab A9 EE",
    "Tab Active3",
    "Tab Active5",
    "ThinkPhone by Motorola",
    "Twist 5",
    "Twist 5 Max",
    "Twist 5 Pro",
    "Twist SE",
    "UP PLAY",
    "VIBE.205D",
    "VIBE.205P",
    "VITA 3G",
    "X3",
    "X50",
    "X8a",
    "XCover 7 5G (128GB)",
    "Xcover Pro",
    "Xcover Pro (new)",
    "Xiaomi 12 Lite",
    "Xiaomi 13 Lite",
    "Z Flip",
    "Z Flip3 5G 128GB",
    "Z Flip3 5G 128GB (new)",
    "Z Flip3 5G 256GB",
    "Z Flip3 5G 256GB (new)",
    "Z Flip4 5G (128GB)",
    "Z Flip4 5G (256GB)",
    "Z Flip5  (512GB)",
    "Z Flip5 (256GB)",
    "Z Fold2",
    "Z Fold3 5G 256GB",
    "Z Fold3 5G 512GB",
    "Z Fold4 5G (1TB)",
    "Z Fold4 5G (256GB)",
    "Z Fold4 5G (512GB)",
    "Z Fold5  (1TB)",
    "Z Fold5 (512GB)",
    "ZAPP",
    "ZERO 5G",
    "Zenfone 10",
    "Zenfone 11",
    "Zenfone 9",
    "Zenfone Max Pro M2",
    "iPhone 11",
    "iPhone 12",
    "iPhone 12 Mini",
    "iPhone 12 Pro",
    "iPhone 12 Pro Max",
    "iPhone 13",
    "iPhone 13 Pro",
    "iPhone 13 Pro Max",
    "iPhone 13 mini",
    "iPhone 14",
    "iPhone 14 Plus",
    "iPhone 14 Pro",
    "iPhone 14 Pro Max",
    "iPhone 15",
    "iPhone 15 Plus",
    "iPhone 15 Pro",
    "iPhone 15 Pro Max",
    "iPhone SE",
]


CERTIFICADO = re.compile(r"(?i)^(Anatel[:\s]*)?((\d[-\s]*){12})$")


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
            incognito=False,
            do_not_track=True,
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
        folder = Path.cwd() / "data" / self.name
        folder.mkdir(parents=True, exist_ok=True)
        output_file = folder / f"{self.name}_{keyword.lower().replace(" ", "_")}.json"
        if not output_file.is_file():
            links = {}
        else:
            links = json.loads(output_file.read_text())
        driver = self.init_driver()
        driver.uc_open_with_reconnect(self.url, reconnect_time=RECONNECT)
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
            driver.uc_open_with_reconnect(self.url, reconnect_time=RECONNECT)
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
