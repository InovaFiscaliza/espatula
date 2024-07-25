import os
import re
from datetime import datetime

from dotenv import find_dotenv, load_dotenv
from fastcore.xtras import Path
from zoneinfo import ZoneInfo

load_dotenv(find_dotenv())

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
PREFIX = os.environ.get("PREFIX")

DISCARD = {
    "amazon": [
        "Acessórios de Carros",
        "Antenas",
        "Apoios",
        "Binóculos, Telescópios e Óptica",
        "Cabos USB",
        "Cabos de Lightning",
        "Capas Laterais",
        "Expansores e Ampliadores de Tela",
        "GPS e Acessórios",
        "Lentes",
        "Som Automotivo",
        "Suportes",
        "Suportes de Cabeceira e Mesa",
    ],
    "ml": [],
    "magalu": [],
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
