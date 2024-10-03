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
    "probabilidade": "float",
    "passível?": "bool",
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
FOLDER = "Pasta Local de Trabalho"
CLOUD = "Pasta do Onedrive (DataHub - POST/Regulatron)"
RECONNECT = "Tempo de espera para conectar-se ao navegador (seg)"
TIMEOUT = "Tempo limite ao carregar os elementos da página (seg)"
SEARCH_PARAMETERS = "Parâmetros - Busca de Links"
MAX_SEARCH = "Nº de Páginas de Busca a Navegar"
MAX_PAGES = "Nº de Páginas de Produtos a Capturar"
SHUFFLE = "Amostrar Páginas Aleatoriamente"
SCREENSHOT = "Capturar Tela do Anúncio"
USER_PROFILE = "Criar/Carregar Perfil de Usuário no Chrome"
SHOW_BROWSER = "Mostrar o Navegador?"
START = "🚀 Iniciar 🚀"

KEYS = {
    "keyword": KEYWORD,
    "folder": FOLDER,
    "cloud": CLOUD,
    "use_cache": CACHE[0],
    "max_search": MAX_SEARCH,
    "max_pages": MAX_PAGES,
    "shuffle": SHUFFLE,
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
                    if (folder := CONFIG.get(KEYS[key])) and Path(folder).is_dir():
                        folder = Path(folder)
                    else:
                        folder = Path(__file__).parent / "data"
                    folder.mkdir(parents=True, exist_ok=True)
                    STATE[key] = rf"{folder}"
                case "cloud":
                    STATE[key] = CONFIG.get(KEYS[key]) or setup_base_cloud()
                case "use_cache":
                    STATE[key] = CACHE[0] if CONFIG.get(KEYS[key]) else CACHE[1]
                case _:
                    STATE[key] = CONFIG.get(KEYS.get(key))


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


def save_config(state) -> None:
    config = {KEYS[key]: state[key] for key in KEYS if key in state}
    json.dump(
        config, CONFIG_FILE.open("w", encoding="utf-8"), ensure_ascii=False, indent=4
    )


CLOUD_PATH = "https://anatel365.sharepoint.com/sites/InovaFiscaliza/DataHub%20%20POST%2FRegulatron%2Fscreenshots"
