# callbacks.py
from fastcore.xtras import Path
import pandas as pd
from gradio_client import Client

from config import SCRAPERS, COLUNAS, CACHE
from data_processing import process_data


def _set_client(state):
    state.client = Client("ronaldokun/ecomproc")


def _set_folder(state):
    if folder := state.get("_folder"):
        if Path(folder).is_dir():
            state.folder = folder


def _set_cloud(state):
    if cloud := state.get("_cloud"):
        if Path(cloud).is_dir():
            state.cloud = cloud


def _set_cached_links(state):
    # Callback function to save the keyword selection to Session state
    scraper = SCRAPERS[state.mkplc](path=state.folder)
    state.cached_links = scraper.get_links(state.keyword)


def _set_cached_pages(state):
    scraper = SCRAPERS[state.mkplc](path=state.folder)
    state.cached_pages = scraper.get_pages(state.keyword)


def _set_processed_pages(state):
    scraper = SCRAPERS[state.mkplc](path=state.folder)
    json_file = scraper.pages_file(state.keyword)
    excel_file = json_file.with_suffix(".xlsx")

    state.processed_pages = None
    need_processing = True

    if excel_file.is_file():
        try:
            df = pd.read_excel(excel_file, dtype="string").astype(COLUNAS)
            df.sort_values(
                by=["passível?", "probabilidade", "modelo_score", "nome_score"],
                ascending=False,
                inplace=True,
                ignore_index=True,
            )
            state.processed_pages = df
            need_processing = False
        except Exception:
            pass

    if need_processing and json_file.is_file():
        process_data(state, json_file)
        need_processing = False

    if (
        not need_processing
        and state.cached_pages is not None
        and state.processed_pages is not None
    ):
        processed_urls = set(state.processed_pages["url"].to_list())
        cached_urls = set(state.cached_pages.keys())
        if cached_urls.difference(processed_urls):
            process_data(state, json_file)
