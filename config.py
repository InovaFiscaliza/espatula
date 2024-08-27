from espatula.spiders import (
    AmazonScraper,
    MercadoLivreScraper,
    MagaluScraper,
    AmericanasScraper,
    CasasBahiaScraper,
    CarrefourScraper,
)

# Constants for string literals
MARKETPLACE = "Marketplace"
HIDE_BROWSER = "Ocultar o navegador"
SEARCH_PARAMETERS = "Parâmetros da Busca"
KEYWORD = "PALAVRA CHAVE"
MAX_PAGES = "Número máximo de páginas de busca a navegar"
SEARCH_LINKS = "Verificar links🧐"
EXTRACTION_PARAMETERS = "Parâmetros da Extração de Dados"
SEARCHED_TEXT = "Texto Pesquisado"
MAX_ADS = "Número máximo de anúncios a extrair"
RANDOM_SAMPLE = "Amostrar páginas aleatoriamente"
CAPTURE_SCREENSHOT = "Capturar tela do anúncio"
NAVIGATE_ADS = "Navegar páginas dos anúncios🚀"
REDO_SEARCH = "Refazer Pesquisa de Links😵‍💫"

SCRAPERS = {
    "Amazon": AmazonScraper,
    "Mercado Livre": MercadoLivreScraper,
    "Magalu": MagaluScraper,
    "Americanas": AmericanasScraper,
    "Casas Bahia": CasasBahiaScraper,
    "Carrefour": CarrefourScraper,
}
