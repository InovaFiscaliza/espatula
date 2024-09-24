# Configurable default values
import os
from fastcore.xtras import Path
import json

from espatula import (
    AmazonScraper,
    AmericanasScraper,
    CarrefourScraper,
    CasasBahiaScraper,
    MagaluScraper,
    MercadoLivreScraper,
)

SCRAPERS = {
    "Amazon": AmazonScraper,
    "Mercado Livre": MercadoLivreScraper,
    "Magalu": MagaluScraper,
    "Americanas": AmericanasScraper,
    "Casas Bahia": CasasBahiaScraper,
    "Carrefour": CarrefourScraper,
}

COLUNAS = {
    "url": "string",
    "imagem": "string",
    "subcategoria": "string",
    "nome": "string",
    "fabricante": "string",
    "modelo": "string",
    "certificado": "string",
    "ean_gtin": "string",
    "nome_sch": "category",
    "tipo_sch": "category",
    "fabricante_sch": "category",
    "modelo_sch": "category",
    "modelo_score": "int8",
    "nome_score": "int8",
    "passível?": "category",
    "probabilidade": "float32",
}

# GUI Images
LOGOS = {
    "Espatula": "images/espatula.png",
    "Amazon": "images/amazon.svg",
    "Mercado Livre": "images/mercado_livre.png",
    "Magalu": "images/magalu.png",
    "Americanas": "images/americanas.png",
    "Casas Bahia": "images/casas_bahia.svg",
    "Carrefour": "images/carrefour.jpg",
}

# Constants for string literals
MARKETPLACE = "**Marketplace**"
KEYWORD = "Palavra-Chave🔎"
TITLE = "🤖 Regulatron"
BASE = "INÍCIO"
CACHE = ("Utilizar Resultados de Busca", "Efetuar Nova Pesquisa")
FOLDER = "Pasta local de Trabalho"
CLOUD = "Pasta do Onedrive (DataHub - POST/Regulatron)"
RECONNECT = "Tempo de espera para conectar-se ao navegador (seg)"
TIMEOUT = "Tempo de espera ao carregar os elementos da página (seg)"
SEARCH_PARAMETERS = "Parâmetros - Busca de Links"
MAX_SEARCH = "Nº de Páginas de Busca a Navegar"
MAX_PAGES = "Nº de Páginas de produtos a Capturar"
SHUFFLE = "Amostrar páginas aleatoriamente"
SCREENSHOT = "Capturar tela do anúncio"
USER_PROFILE = "Criar/carregar perfil de usuário no Chrome"
SHOW_BROWSER = "Mostrar o navegador?"
START = "Iniciar🚀"

KEYS = {
    "keyword": KEYWORD,
    "folder": FOLDER,
    "cloud": CLOUD,
    "use_cache": CACHE[0],
    "max_search": MAX_SEARCH,
    "max_pages": MAX_PAGES,
    "shuffle": SHUFFLE,
    "screenshot": SCREENSHOT,
    "reconnect": RECONNECT,
    "timeout": TIMEOUT,
}

CONFIG_FILE = Path(__file__).parent / "config.json"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        return CONFIG_FILE.read_json()
    return {}


def init_session_state(STATE: dict, CONFIG: dict) -> None:
    if "mkplc" not in STATE:
        STATE.mkplc = None

    for key in [
        "keyword",
        "folder",
        "cloud",
        "cached_links",
        "show_cache",
        "cached_pages",
        "processed_pages",
        "use_cache",
        "client",
    ]:
        if key not in STATE:
            match key:
                case "keyword":
                    STATE[key] = CONFIG.get(KEYS[key], "")
                case "folder":
                    folder = Path(__file__).parent / "data"
                    folder.mkdir(parents=True, exist_ok=True)
                    STATE[key] = rf"{folder}"
                case "cloud":
                    STATE[key] = CONFIG.get(KEYS[key]) or setup_base_cloud()
                case "use_cache":
                    STATE[key] = CACHE[0] if CONFIG.get(KEYS[key]) else CACHE[1]
                case _:
                    STATE[key] = None


def setup_base_cloud() -> str:
    onedrive = os.environ.get("OneDriveCommercial", "")
    cloud = None
    if onedrive:
        cloud_paths = [
            (Path(onedrive) / "DataHub - POST/Regulatron"),
            (Path.home() / "ANATEL/InovaFiscaliza - DataHub - POST/Regulatron"),
        ]
        for cloud_path in cloud_paths:
            if cloud_path.resolve().is_dir():
                cloud = rf"{cloud_path.resolve()}"
                break
    return cloud


def save_config(config: dict) -> None:
    json.dump(
        config, CONFIG_FILE.open("w", encoding="utf-8"), ensure_ascii=False, indent=4
    )


# Other utility functions and configuration-related logic can go here...
