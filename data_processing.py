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


def save_table(state: dict, subset_df: pd.DataFrame = None) -> bool:
    scraper = SCRAPERS[state.mkplc](path=state.folder)
    try:
        if (df := state.processed_pages) is not None:
            output_table = scraper.pages_file(state.keyword).with_suffix(".xlsx")
            df["marketplace"] = state.mkplc
            df.to_excel(output_table, index=False)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cloud_output = (
                f"{state.cloud}/{output_table.stem}_{timestamp}{output_table.suffix}"
            )
            if subset_df is None:
                shutil.copy(str(output_table), str(cloud_output))
            else:
                subset_df["marketplace"] = state.mkplc
                subset_df.to_excel(cloud_output, index=False)

    except Exception as e:
        print(f"Erro ao salvar os dados processados: {e}")


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
            ignore_index=True,
        )

        state.processed_pages = df
        save_table(state)


def update_processed_pages(state, output_df_key):
    edited = state[output_df_key]["edited_rows"]
    df = state[f"df_{output_df_key}"].reset_index(drop=True)
    index, row = edited.popitem()
    column, value = row.popitem()
    df.at[index, column] = value
    # Sanity check
    assert (
        not edited and not row
    ), f"Ambos dicionários deveriam estar vazios: {edited}, {row}"
    state.processed_pages.loc[state[f"df_{output_df_key}"].index, "passível?"] = df[
        "passível?"
    ].to_list()
    state[f"df_{output_df_key}"] = df
    save_table(state, state[f"df_{output_df_key}"].loc[index].to_frame().T)
