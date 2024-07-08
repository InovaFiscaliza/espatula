import sys
from fastcore.xtras import Path
import typer

sys.path.append(str(Path(__file__).parent.parent))
from amazon import AmazonScraper
from mercado_livre import MercadoLivreScraper
from magalu import MagaluScraper
from americanas import AmericanasScraper
from casas_bahia import CasasBahiaScraper
from carrefour import CarrefourScraper
from base import KEYWORDS

SCRAPER = {
    "amazon": AmazonScraper,
    "mercado_livre": MercadoLivreScraper,
    "magalu": MagaluScraper,
    "americanas": AmericanasScraper,
    "casas_bahia": CasasBahiaScraper,
    "carrefour": CarrefourScraper,
}

if __name__ == "__main__":

    def main(
        scraper: str,
        search: bool = True,
        keyword: str = None,
        headless: bool = True,
        screenshot: bool = False,
        sample: int = 78,
    ):
        if scraper not in SCRAPER:
            print("Invalid scraper")
            exit()
        else:
            scraper = SCRAPER[scraper](headless=headless)

        if not keyword:
            for keyword in KEYWORDS:
                if search:
                    scraper.search(keyword)
                else:
                    scraper.inspect_pages(keyword, screenshot, sample=sample)
        else:
            if search:
                scraper.search(keyword)
            else:
                scraper.inspect_pages(keyword, screenshot, sample=sample)

    typer.run(main)
