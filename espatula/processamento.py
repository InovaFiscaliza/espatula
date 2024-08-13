import os
from functools import cached_property

import pandas as pd
from fastcore.xtras import Path
from rich import print

from .certificacao import merge_to_sch
from .constantes import FOLDER, SUBCATEGORIES

COLUNAS = [
    "screenshot",
    "nome",
    "preço",
    "fabricante",
    "modelo",
    "certificado",
    "ean_gtin",
    "subcategoria",
    "nome_sch",
    "fabricante_sch",
    "modelo_sch",
    "tipo_sch",
    "index",
    "página_de_busca",
    "palavra_busca",
    "data",
]


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
                print(f"Missing file, deleting row {row.screenshot}")
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
        filter = self.df["subcategoria"].isin(SUBCATEGORIES[self.name])
        self.delete_files(~filter)
        self.df = self.df.loc[filter].reset_index(drop=True)

    def clean(self):
        self.df["preço"] = self.df["preço"].str.strip().str.extract("(\d+\.?\d+)")

    def write_excel(self):
        self.df["data"] = pd.to_datetime(self.df["data"], format="mixed").dt.strftime(
            "%d/%m/%Y"
        )
        df = self.df.loc[:, COLUNAS]

        writer = pd.ExcelWriter(
            self.source.with_suffix(".xlsx"),
            engine="xlsxwriter",
            engine_kwargs={"options": {"strings_to_urls": True}},
        )
        df.to_excel(writer, sheet_name=self.name, engine="xlsxwriter", index=False)
        worksheet = writer.sheets[self.name]
        worksheet.set_default_row(hide_unused_rows=True)
        # Freeze the first row
        worksheet.freeze_panes(1, 0)
        if prefix := os.environ.get("PREFIX"):
            for i, link in enumerate(df["screenshot"], start=2):
                worksheet.write_url(f"A{i}", prefix + link, string=f"#{i}")
        for i, row in enumerate(
            self.df.itertuples(), start=2
        ):  # Note I'm iterating over self.df not df
            worksheet.write_url(f"B{i}", row.url, string=row.nome)
        # Make the columns wider for clarity.
        worksheet.autofit()
        writer.close()

    def process(self, update_sch: bool = False, tipo_sch: str = None):
        self.drop_incomplete_rows()
        self.split_categories()
        self.filter_subcategories()
        self.clean()
        self.df = merge_to_sch(self.df, update=update_sch, tipo_sch=tipo_sch)
