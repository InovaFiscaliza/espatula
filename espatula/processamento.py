import string
from functools import cached_property
from typing import List, Union

import nltk
import pandas as pd
from fastcore.xtras import Path, listify
from fuzzywuzzy import fuzz
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from gradio_client import Client


from .certificacao import merge_to_sch
from .constantes import SUBCATEGORIES

nltk.download("stopwords", quiet=True)
nltk.download("punkt_tab", quiet=True)
client = Client("ronaldokun/is_telecom")


COLUNAS = [
    "nome",
    "fabricante",
    "modelo",
    "certificado",
    "ean_gtin",
    "passível?",
    "probabilidade",
    "nome_sch",
    "fabricante_sch",
    "modelo_sch",
    "nome_score",
    "modelo_score",
    "tipo_sch",
    "subcategoria",
    "indice",
    "página_de_busca",
    "palavra_busca",
    "data",
    "screenshot",
    "url",
]

COLUMN_PAIRS = [
    ("nome", "nome_sch"),
    ("modelo", "modelo_sch"),
]

COLUMN_SCORE_NAMES = [
    "nome_score",
    "modelo_score",
]


class Table:
    def __init__(self, name: str, json_source: Path = None):
        self.name = name
        self.json_source = json_source

    @cached_property
    def df(self):
        """Return the DataFrame for the table."""
        return pd.DataFrame(self.json_source.read_json().values(), dtype="string")

    @staticmethod
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

    @staticmethod
    def score_distance(str1: str, str2: str, join_tokens: bool = True) -> int:
        """
        Fuzzy matches two strings by generating a score mapping between all token combinations,
        and returns the score mapping and maximum score.

        Parameters:
        str1 (str): The first string to match.
        str2 (str): The second string to match.
        join_tokens (bool): Whether to join tokens into ngrams before matching.

        Returns:
        max_score (int): The maximum score found betweel the strings.
        """
        first_set = Table.preprocess_text(str1, join_tokens=join_tokens)
        second_set = Table.preprocess_text(str2, join_tokens=join_tokens)

        return max(
            [
                fuzz.partial_ratio(s1, s2)
                for s1 in first_set
                for s2 in second_set
                if s1 != "" and s2 != ""
            ],
            default=0,
        )

    @staticmethod
    def calculate_text_distance(row: pd.Series) -> List[Union[dict, int]]:
        """Score each row of the dataframe by comparing column pairs.

        For each column pair, get the fuzzy match score between the values.
        Return a list containing the match mapping dict and max score for each pair.
        """
        return [
            Table.score_distance(row.loc[left], row.loc[right])
            for (left, right) in COLUMN_PAIRS
        ]

    def drop_incomplete_rows(self):
        for column in ["nome", "categoria", "url"]:
            self.df = self.df.dropna(subset=column).reset_index(drop=True)

    def split_categories(self):
        categories = self.df["categoria"].str.split("|", expand=True)
        categories.columns = [f"categoria_{c}" for c in categories.columns]
        for cat in categories:
            categories[cat] = categories[cat].str.strip()
        self.df = pd.concat([self.df, categories], axis=1)
        self.df["subcategoria"] = ""
        for cat in categories.columns:
            condition = self.df[cat].notna()
            self.df.loc[condition, "subcategoria"] = self.df.loc[condition, cat]

        self.df = self.df.drop(columns="categoria")

    def filter_subcategories(self):
        if self.name not in SUBCATEGORIES:
            print(f"{self.name} has no subcategories defined, table unchanged!")
            return
        relevant = self.df["subcategoria"].isin(SUBCATEGORIES[self.name])
        self.delete_files(~relevant)
        self.df = self.df.loc[relevant].reset_index(drop=True)

    def clean(self):
        self.df["preço"] = (
            self.df["preço"].str.strip().str.extract(r"(\d+\.{0,1}\d{0,2})")
        )

    def write_excel(self):
        """Write the dataframe to an Excel file.
        prefix_link: The cloud link path to the parent folder where the spider folders are saved.
        """

        writer = pd.ExcelWriter(
            self.json_source.with_suffix(".xlsx"),
            engine="xlsxwriter",
            engine_kwargs={
                "options": {
                    "strings_to_urls": True,
                }
            },
        )

        df = self.df.loc[:, COLUNAS]
        df["data"] = pd.to_datetime(self.df["data"], format="mixed").dt.strftime(
            "%d/%m/%Y"
        )
        df.to_excel(writer, sheet_name=self.name, engine="xlsxwriter", index=False)
        self.df.to_excel(
            writer, sheet_name=f"{self.name}_bruto", engine="xlsxwriter", index=False
        )
        worksheet = writer.sheets[self.name]
        worksheet.set_default_row(hide_unused_rows=True)
        # Freeze the first row
        worksheet.freeze_panes(1, 0)
        for i, name in enumerate(df["screenshot"], start=2):
            worksheet.write_url(
                f"S{i}",
                f"screenshots/{name}",
            )
        for i, row in enumerate(df.itertuples(), start=2):
            worksheet.write_url(f"T{i}", row.url)
        # Make the columns wider for clarity.
        worksheet.autofit()
        writer.close()

    def compare_columns(self):
        self.df[COLUMN_SCORE_NAMES] = self.df.fillna("").apply(
            self.calculate_text_distance, axis=1, result_type="expand"
        )
        self.df.sort_values(
            COLUMN_SCORE_NAMES, ascending=False, inplace=True, ignore_index=True
        )
        self.df.drop_duplicates(
            subset="url", keep="first", inplace=True, ignore_index=True
        )

    def classify(self):
        response = client.predict(
            texts="\n".join(self.df["nome"].to_list()), api_name="/predict"
        )
        self.df[["passível?", "probabilidade"]] = response["data"]

    def process(self, update_sch: bool = False, tipo_sch: str = None):
        self.drop_incomplete_rows()
        self.split_categories()
        # self.filter_subcategories()
        self.clean()
        self.df = merge_to_sch(
            self.df,
            update=update_sch,
            tipo_sch=tipo_sch,
        )
        self.compare_columns()
        self.classify()
        self.write_excel()
