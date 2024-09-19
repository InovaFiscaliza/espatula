# Configurable default values

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
    # "probabilidade": "float32",
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
