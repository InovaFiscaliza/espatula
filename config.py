from espatula.spiders import (
    AmazonScraper,
    MercadoLivreScraper,
    MagaluScraper,
    AmericanasScraper,
    CasasBahiaScraper,
    CarrefourScraper,
)

SCRAPERS = {
    "Amazon": AmazonScraper,
    "Mercado Livre": MercadoLivreScraper,
    "Magalu": MagaluScraper,
    "Americanas": AmericanasScraper,
    "Casas Bahia": CasasBahiaScraper,
    "Carrefour": CarrefourScraper,
}
