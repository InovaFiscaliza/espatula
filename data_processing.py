# data_processing.py
import shutil
from datetime import datetime
import pandas as pd
from gradio_client import handle_file
from gradio_client.exceptions import AppError

from fastcore.xtras import Path
from config import COLUNAS, SCRAPERS


def request_table(state, json_path: Path) -> pd.DataFrame | None:
    try:
        result = state.client.predict(
            json_file=handle_file(str(json_path)), api_name="/process_to_table"
        )
        df = pd.DataFrame(
            result["data"], columns=result["headers"], dtype="string"
        ).astype(COLUNAS)
        return df
    except AppError:
        return None


def save_table(state: dict):
    scraper = SCRAPERS[state.mkplc](path=state.folder)
    try:
        if (df := state.processed_pages) is not None:
            output_table = scraper.pages_file(state.keyword).with_suffix(".xlsx")
            df["marketplace"] = state.mkplc
            df.loc[df["passível?"] == "True"].to_excel(output_table, index=False)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cloud_output = (
                f"{state.cloud}/{output_table.stem}_{timestamp}{output_table.suffix}"
            )
            shutil.copy(str(output_table), str(cloud_output))

    except Exception as e:
        print(e)


def process_data(state, pages_file: Path) -> None:
    state.processed_pages = None
    if len(pages_file.read_json()) == 0:
        pages_file.unlink(missing_ok=True)
    elif (df := request_table(state, pages_file)) is not None:
        df["probabilidade"] *= 100
        df.sort_values(
            by=["modelo_score", "nome_score", "passível?", "probabilidade"],
            ascending=False,
            inplace=True,
        )

        state.processed_pages = df
        save_table(state)


def update_processed_pages(state, output_df_key):
    edited = state[output_df_key]["edited_rows"]
    for index, row in edited.items():
        for column, value in row.items():
            state.processed_pages.loc[index, column] = str(value)
