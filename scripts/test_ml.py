import sys
from fastcore.xtras import Path


sys.path.append(str(Path(__file__).parent.parent))
from espatula.constantes import FOLDER
from espatula.spiders import MercadoLivreScraper

ml = MercadoLivreScraper(headless=False)
ml.search("drone")
