# callbacks.py
from fastcore.xtras import Path
from .callbacks import SCRAPERS


def set_keyword(STATE):
    STATE.keyword = STATE._keyword.strip()


def set_folder(STATE):
    if Path(STATE._folder).is_dir():
        STATE.folder = STATE._folder


def set_cloud(STATE):
    if STATE._cloud is not None and Path(STATE._cloud).is_dir():
        STATE.cloud = STATE._cloud


@st.fragment
def set_cached_links(STATE):
    # Callback function to save the keyword selection to Session State
    scraper = SCRAPERS[STATE.mkplc](path=STATE.folder)
    STATE.cached_links = scraper.get_links(STATE.keyword)


@st.fragment
def set_cached_pages(STATE):
    scraper = SCRAPERS[STATE.mkplc](path=STATE.folder)
    STATE.cached_pages = scraper.get_pages(STATE.keyword)


# Other callbacks as necessary...
