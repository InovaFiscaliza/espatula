import os
import re
from datetime import datetime

from dotenv import find_dotenv, load_dotenv
from fastcore.xtras import Path
from zoneinfo import ZoneInfo

load_dotenv(find_dotenv())

# Raspagem de Dados
FOLDER = Path(os.environ.get("FOLDER", f"{Path(__file__)}/data"))
RECONNECT = int(os.environ.get("RECONNECT", 5))
TIMEOUT = int(os.environ.get("TIMEOUT", 5))
TIMEZONE = ZoneInfo("America/Sao_Paulo")
TODAY = datetime.today().astimezone(TIMEZONE).strftime("%Y%m%d")
CERTIFICADO = re.compile(
    r"""
    (?ix)                  # Case-insensitive and verbose mode
    ^                      # Start of the string
    (Anatel[:\s]*)?        # Optional "Anatel" followed by colon or spaces
    (                      # Start of main capturing group
        (\d[-\s]*)+        # One or more digits, each optionally followed by hyphen or spaces
    )
    $                      # End of the string
""",
    re.VERBOSE,
)

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

# Processamento dos dados de saída
PREFIX = os.environ.get("PREFIX")

COUNT = os.environ.get("COUNT", 65)
DISCARD = {
    "amazon": [
        "Acessórios de Carros",
        "Alimentos e Bebidas",
        "Antenas",
        "Apoios",
        "Bebês",
        "Beleza",
        "Binóculos, Telescópios e Óptica",
        "Brinquedos e Jogos",
        "Cabos USB",
        "Cabos de Lightning",
        "Capas Laterais",
        "CD e Vinil",
        "Cozinha",
        "DVD e Blu-ray",
        "Esporte",
        "Expansores e Ampliadores de Tela",
        "Ferramentas e Materiais de Construção",
        "GPS e Acessórios",
        "Instrumentos Musicais",
        "Jardim e Piscina",
        "Lentes",
        "Livros",
        "Moda",
        "Saúde e Bem-Estar",
        "Som Automotivo",
        "Suportes",
        "Suportes de Cabeceira e Mesa",
    ],
    "ml": [
        "Esportes e Fitness",
        "Calçados",
        "Construção",
        "Games",
        "Ferramentas",
        "Saúde",
        "Eletrodomésticos",
        "Brinquedos e Hobbies",
        "Indústria e Comércio",
        "Bebês",
        "Animais",
        "Livros",
        "Joias e Relógios",
        "Beleza e Cuidado Pessoal",
        "Mais Categorias",
        "Música",
        "Festas e Lembrancinhas",
        "Antiguidades e Coleções",
        "Alimentos e Bebidas",
        "Arte",
        "Serviços",
    ],
    "magalu": [
        "Ar e Ventilação",
        "Mercado",
        "Eletroportáteis",
        "Casa e Construção",
        "Esporte e Lazer",
        "Eletroportáteis",
        "Casa e Construção",
        "Esporte e Lazer",
        "Saúde e Cuidados Pessoais",
        "Beleza & Perfumaria",
        "Suplementos Alimentares",
        "Brinquedos",
        "Móveis",
        "Utilidades Domésticas",
        "Moda",
        "Bebê",
    ],
    "americanas": [],
    "carrefour": [],
    "casasbahia": [],
}

SUBCATEGORIES = {
    "amazon": ["Celulares e Smartphones"],
    "ml": ["Celulares e Smartphones"],
    "magalu": [
        "xiaomi",
        "celular básico",
        "galaxy",
        "smartphone",
        "motorola",
        "carregador de celular",
        "moto",
        "multilaser",
        "poco",
        "iphone",
        "positivo",
        "lg",
        "infinix",
        "nokia",
        "redmi",
        "tcl",
        "oppo",
        "asus",
        "philco",
        "lenovo",
    ],
    "carrefour": [
        "xiaomi",
        "celular básico",
        "galaxy",
        "smartphone",
        "motorola",
        "carregador de celular",
        "moto",
        "multilaser",
        "poco",
        "iphone",
        "positivo",
        "lg",
        "infinix",
        "nokia",
        "redmi",
        "tcl",
        "oppo",
        "asus",
        "philco",
        "lenovo",
        "android os",
    ],
    "americanas": [
        "xiaomi",
        "celular básico",
        "galaxy",
        "smartphone",
        "motorola",
        "carregador de celular",
        "moto",
        "multilaser",
        "poco",
        "iphone",
        "positivo",
        "lg",
        "infinix",
        "nokia",
        "redmi",
        "tcl",
        "oppo",
        "asus",
        "philco",
        "lenovo",
        "android os",
        "realme",
    ],
    "casasbahia": [
        "celulares",
        "android",
        "iphone",
    ],
}

ILLEGAL_XLSX_CHARS = {
    "\x00": "\\x00",  # 	NULL
    "\x01": "\\x01",  # 	SOH
    "\x02": "\\x02",  # 	STX
    "\x03": "\\x03",  # 	ETX
    "\x04": "\\x04",  # 	EOT
    "\x05": "\\x05",  # 	ENQ
    "\x06": "\\x06",  # 	ACK
    "\x07": "\\x07",  # 	BELL
    "\x08": "\\x08",  # 	BS
    "\x0b": "\\x0b",  # 	VT
    "\x0c": "\\x0c",  # 	FF
    "\x0e": "\\x0e",  # 	SO
    "\x0f": "\\x0f",  # 	SI
    "\x10": "\\x10",  # 	DLE
    "\x11": "\\x11",  # 	DC1
    "\x12": "\\x12",  # 	DC2
    "\x13": "\\x13",  # 	DC3
    "\x14": "\\x14",  # 	DC4
    "\x15": "\\x15",  # 	NAK
    "\x16": "\\x16",  # 	SYN
    "\x17": "\\x17",  # 	ETB
    "\x18": "\\x18",  # 	CAN
    "\x19": "\\x19",  # 	EM
    "\x1a": "\\x1a",  # 	SUB
    "\x1b": "\\x1b",  # 	ESC
    "\x1c": "\\x1c",  # 	FS
    "\x1d": "\\x1d",  # 	GS
    "\x1e": "\\x1e",  # 	RS
    "\x1f": "\\x1f",
}  # 	US
