# Configurable default values
import os
from fastcore.xtras import Path
import json

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
    "Carrefour": "images/carrefour.svg",
}

# Constants for string literals
MARKETPLACE = "**Marketplace**"
KEYWORD = "Palavra-Chave🔎"
TITLE = "🤖 Regulatron"
BASE = "INÍCIO"
CACHE = ("Utilizar Resultados de Busca", "Efetuar Nova Pesquisa")
FOLDER = "Pasta local de Trabalho"
CLOUD = "Pasta do Onedrive (DataHub - POST/Regulatron)"
RECONNECT = "Tempo de espera para conectar ao navegador (seg)"
TIMEOUT = "Tempo de espera para carregamento da página (seg)"
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
    "show_browser": SHOW_BROWSER,
    "marketplace": MARKETPLACE,
    "max_pages": MAX_PAGES,
    "max_search": MAX_SEARCH,
    "reconnect": RECONNECT,
    "screenshot": SCREENSHOT,
    "shuffle": SHUFFLE,
    "timeout": TIMEOUT,
    "title": TITLE,
    "logos": LOGOS,
    "load_user_profile": USER_PROFILE,
}


def load_config() -> dict:
    if (config_file := Path(__file__).parent / "config.json").exists():
        return config_file.read_json()
    return {}


def init_session_state(STATE: dict, CONFIG: dict, KEYS: dict) -> None:
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
    ]:
        if key not in STATE:
            if key == "keyword":
                STATE[key] = CONFIG.get(KEYS[key], "")
            elif key == "folder":
                folder = (Path(__file__).parent / "data").resolve()
                if not folder.is_dir():
                    folder.mkdir(parents=True, exist_ok=True)
                STATE[key] = rf"{folder}"
            elif key == "cloud":
                cloud = CONFIG.get(KEYS[key])
                if not cloud:
                    cloud = setup_base_cloud()
                STATE[key] = cloud
            elif key == "use_cache":
                STATE[key] = CACHE[0] if CONFIG.get(KEYS[key]) else CACHE[1]
            else:
                STATE[key] = {}


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


def save_config(config: dict, config_file: Path) -> None:
    json.dump(config, config_file.open("w", encoding="utf-8"), ensure_ascii=False)


# Other utility functions and configuration-related logic can go here...
