import os
import string
from functools import cached_property
from typing import List, Union

import nltk
import pandas as pd
from fastcore.xtras import Path, listify
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from rich import print

from .certificacao import merge_to_sch
from .constantes import FOLDER, SUBCATEGORIES

nltk.download("stopwords")
nltk.download("punkt")


COLUNAS = [
    "nome",
    "fabricante",
    "modelo",
    "certificado",
    "ean_gtin",
    "nome_sch",
    "fabricante_sch",
    "modelo_sch",
    "tipo_sch",
    "preço",
    "subcategoria",
    "index",
    "página_de_busca",
    "palavra_busca",
    "data",
    "screenshot",
    "url",
]


def preprocess_text(
    text: str,
    tokenize: bool = True,
    remove_punctuation: bool = True,
    remove_stopwords: bool = False,
    join_tokens: bool = False,
) -> Union[str, List]:
    """Preprocess text by tokenizing, removing punctuation and stopwords.

    Args:
        text (str): The text to preprocess.
        tokenize (bool): Whether to tokenize the text. Default True.
        remove_punctuation (bool): Whether to remove punctuation. Default True.
        remove_stopwords (bool): Whether to remove stopwords. Default True.
        join_tokens (bool): Whether to join the tokens into a string.
            Default True, otherwise returns a list of tokens.

    Returns:
        Union[str, List]: The preprocessed text, either as a string or list of tokens.
    """
    # Convert to lowercase
    text_out = text.lower()

    if tokenize:
        # Tokenize the text
        tokens = word_tokenize(text_out, language="portuguese")

        if remove_punctuation:
            # Remove punctuation from each token
            table = str.maketrans("", "", string.punctuation)
            tokens = [token.translate(table) for token in tokens]

        if remove_stopwords:
            # Filter out stop words
            stop_words = set(stopwords.words("portuguese"))
            tokens = [w for w in tokens if w not in stop_words]

        text_out = " ".join(tokens) if join_tokens else tokens

    return listify(text_out)


class Table:
    def __init__(self, name: str, json_source: Path):
        self.name = name
        self.source = FOLDER / name / json_source

    @cached_property
    def df(self):
        return pd.DataFrame(self.source.read_json().values(), dtype="string")

    def delete_files(self, filter: pd.Series) -> None:
        for row in self.df.loc[filter].itertuples():
            if (file := FOLDER / "screenshots" / f"{row.screenshot}").is_file():
                print(f"Deleting {file} from discarded row")
                # file.unlink()

    def drop_incomplete_rows(self):
        for column in ["nome", "categoria", "url"]:
            self.delete_files(self.df[column].isna())
            self.df = self.df.dropna(subset=column).reset_index(drop=True)
        for row in self.df.itertuples():
            if not (FOLDER / "screenshots" / f"{row.screenshot}").is_file():
                self.df = self.df.drop(index=row.Index)

    def split_categories(self):
        categories = self.df["categoria"].str.split("|", expand=True)
        categories.columns = [f"categoria_{c}" for c in categories.columns]
        for cat in categories:
            categories[cat] = categories[cat].str.strip()
        self.df = pd.concat([self.df, categories], axis=1)
        for cat in categories.columns:
            condition = self.df[cat].notna()
            self.df.loc[condition, "subcategoria"] = self.df.loc[condition, cat]

    def filter_subcategories(self):
        if self.name not in SUBCATEGORIES:
            print(f"{self.name} has no subcategories defined, table unchanged!")
            return
        irrelevant = self.df["subcategoria"].isin(SUBCATEGORIES[self.name])
        self.delete_files(~irrelevant)
        self.df = self.df.loc[irrelevant].reset_index(drop=True)

    def clean(self):
        self.df["preço"] = (
            self.df["preço"].str.strip().str.extract(r"(\d+\.{0,1}\d{0,2})")
        )

    def write_excel(self):
        self.df["data"] = pd.to_datetime(self.df["data"], format="mixed").dt.strftime(
            "%d/%m/%Y"
        )
        df = self.df.loc[:, COLUNAS]

        writer = pd.ExcelWriter(
            self.source.with_suffix(".xlsx"),
            engine="xlsxwriter",
            engine_kwargs={
                "options": {
                    "strings_to_urls": True,
                }
            },
        )
        df.to_excel(writer, sheet_name=self.name, engine="xlsxwriter", index=False)
        worksheet = writer.sheets[self.name]
        worksheet.set_default_row(hide_unused_rows=True)
        # Freeze the first row
        worksheet.freeze_panes(1, 0)
        if prefix := os.environ.get("PREFIX"):
            for i, link in enumerate(df["screenshot"], start=2):
                worksheet.write_url(f"P{i}", prefix + link)
        for i, row in enumerate(
            df.itertuples(), start=2
        ):  # Note I'm iterating over self.df not df
            worksheet.write_url(f"Q{i}", row.url)
        # Make the columns wider for clarity.
        worksheet.autofit()
        # # Create a format for the font size
        # cell_format = writer.book.add_format({"font_size": 9})

        # # Apply the format to columns A and B
        # worksheet.set_column("P:P", None, cell_format)
        # worksheet.set_column("Q:Q", None, cell_format)
        # Set font size 9 for column A and B
        writer.close()

    def process(self, update_sch: bool = False, tipo_sch: str = None):
        self.drop_incomplete_rows()
        self.split_categories()
        self.filter_subcategories()
        self.clean()
        self.df = merge_to_sch(self.df, update=update_sch, tipo_sch=tipo_sch)
