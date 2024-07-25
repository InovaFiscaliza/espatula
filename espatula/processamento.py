import pandas as pd
from functools import cached_property
from fastcore.xtras import Path
from rich import print
from .constantes import FOLDER, DISCARD, SUBCATEGORIES, COUNT
from .certificacao import merge_to_sch

COLUNAS = [
    "index",
    "página_de_busca",
    "palavra_busca",
    "data",
    "screenshot",
    "subcategoria",
    "nome",
    "fabricante",
    "modelo",
    "certificado",
    "ean_gtin",
    "nome_sch",
    "fabricante_sch",
    "modelo_sch",
    "tipo_sch",
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
                print(f"Deleting {file} from incomplete row")
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

    # def write_excel(self):
    #     self.df["data"] = pd.to_datetime(self.df["data"], format="mixed").dt.strftime(
    #         "%d/%m/%Y"
    #     )
    #     df = df[COLUNAS]
    #     writer = pd.ExcelWriter(
    #         output_file,
    #         engine="xlsxwriter",
    #         engine_kwargs={"options": {"strings_to_urls": True}},
    #     )
    #     df.to_excel(writer, sheet_name=sheet_name, engine="xlsxwriter", index=False)
    #     worksheet = writer.sheets[sheet_name]
    #     # Make the columns wider for clarity.
    #     worksheet.autofit()
    #     worksheet.set_default_row(hide_unused_rows=True)
    #     # Freeze the first row
    #     worksheet.freeze_panes(1, 0)
    #     for i, link in enumerate(df["Arquivo"], start=2):
    #         pdf = PREFIX + link
    #         worksheet.write_url(f"D{i}", pdf, string=link)
    #     writer.close()

    def process(
        self, update_sch: bool = False, tipo_sch: str = "Telefone Móvel Celular"
    ):
        self.drop_incomplete_rows()
        self.split_categories()
        self.filter_subcategories()
        df = merge_to_sch(self.df, update=update_sch, tipo_sch=tipo_sch)
        self.df = df.loc[:, COLUNAS]
