import sys
from fastcore.xtras import Path

import typer
import pandas as pd


sys.path.append(str(Path(__file__).parent.parent))
from amazon import AmazonScraper
from mercado_livre import MercadoLivreScraper
from magalu import MagaluScraper
from americanas import AmericanasScraper

from casas_bahia import CasasBahiaScraper
from carrefour import CarrefourScraper
from base import KEYWORDS, FOLDER, TODAY

PREFIX = "https://anatel365.sharepoint.com/sites/Desenvolvimentodeappfiscalizaoe-commerce/Documentos%20Compartilhados/General/Resultados/screenshots/"


COLUNAS = [
    "Item",
    "Página",
    "Texto da Busca",
    "Arquivo",
    "Data",
    "URL",
    "Título",
    "Categoria",
    "Fabricante",
    "Modelo",
    "Preço",
    "Unidades à Venda",
    "Existe campo código SCH?",
    "Código SCH foi fornecido?",
    "Código de Homologação",
    "Código SCH é o do produto?",
    "O produto é homologado?",
    "O código EAN foi fornecido?",
    "Código EAN é o do produto?",
    "Código EAN-GTIN",
]


TO_DISCARD = {
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
}


SCRAPER = {
    "amazon": AmazonScraper,
    "ml": MercadoLivreScraper,
    "magalu": MagaluScraper,
    "americanas": AmericanasScraper,
    # "casasbahia": CasasBahiaScraper,
    "carrefour": CarrefourScraper,
}


def delete_files(df: pd.DataFrame, filter: pd.Series) -> None:
    for row in df[filter].itertuples():
        if (file := FOLDER / "screenshots" / f"{row.screenshot}").is_file():
            print(f"Deleting {file}")
            file.unlink()


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    for column in ["nome", "categoria", "url"]:
        delete_files(df, df[column].isna())
        df = df.dropna(subset=column).reset_index(drop=True)

    for row in df.itertuples():
        if not (FOLDER / "screenshots" / f"{row.screenshot}").is_file():
            print(f"Missing file, deleting row {row.screenshot}")
            df = df.drop(index=row.Index)

    categories = df["categoria"].str.split("|", expand=True)
    categories.columns = [f"categoria_{c}" for c in categories.columns]
    for cat in categories:
        categories[cat] = categories[cat].str.strip()
    df = pd.concat([df, categories], axis=1)
    for cat in categories.columns:
        condition = df[cat].notna()
        df.loc[condition, "subcategoria"] = df.loc[condition, cat]
    return df


def write_excel(df, output_file, sheet_name):
    df.rename(
        columns={
            "palavra_busca": "Texto da Busca",
            "página_de_busca": "Página",
            "index": "Item",
            "screenshot": "Arquivo",
            "url": "URL",
            "nome": "Título",
            "subcategoria": "Categoria",
            "marca": "Fabricante",
            "modelo": "Modelo",
            "preço": "Preço",
            "certificado": "Código de Homologação",
            "ean_gtin": "Código EAN-GTIN",
        },
        inplace=True,
    )

    df = df[COLUNAS]
    writer = pd.ExcelWriter(
        output_file,
        engine="xlsxwriter",
        engine_kwargs={"options": {"strings_to_urls": True}},
    )
    df.to_excel(writer, sheet_name=sheet_name, engine="xlsxwriter", index=False)
    worksheet = writer.sheets[sheet_name]
    # Make the columns wider for clarity.
    worksheet.autofit()
    worksheet.set_default_row(hide_unused_rows=True)
    # Freeze the first row
    worksheet.freeze_panes(1, 0)
    for i, link in enumerate(df["Arquivo"], start=2):
        pdf = PREFIX + link
        worksheet.write_url(f"D{i}", pdf, string=link)
    writer.close()


def process_amazon(output_file, category="Celulares e Smartphones"):
    df = pd.DataFrame(output_file.read_json().values(), dtype="string")
    df = preprocess(df)
    delete_files(df, df["subcategoria"] != category)
    df = df.loc[df["subcategoria"] == category]
    df["Data"] = pd.to_datetime(df["data"], format="mixed").dt.strftime("%d/%m/%Y")
    discard = df["certificado"].isna() & df["subcategoria"].isin(TO_DISCARD["amazon"])
    delete_files(df, discard)
    df = df.loc[~discard]
    df["Unidades à Venda"] = "Não Informado"
    columns = [
        "Existe campo código SCH?",
        "Código SCH foi fornecido?",
    ]
    for column in columns:
        df[column] = "Sim"
        df.loc[df["certificado"].isna(), column] = "Não"
    columns = [
        "O produto é homologado?",
        "Código SCH é o do produto?",
        "Código EAN é o do produto?",
    ]
    for column in columns:
        df[column] = ""

    column = "O código EAN foi fornecido?"
    df[column] = "Sim"
    df.loc[df["ean_gtin"].isna(), column] = "Não"
    write_excel(df, output_file.with_suffix(".xlsx"), "amazon-smartphone")


def process_ml(output_file, category="Celulares e Smartphones"):
    df = pd.DataFrame(output_file.read_json().values(), dtype="string")
    df = preprocess(df)
    df["subcategoria"] = df["categoria_1"]
    delete_files(df, df["subcategoria"] != category)
    df = df.loc[df["subcategoria"] == category]
    df["Data"] = pd.to_datetime(df["data"], format="mixed").dt.strftime("%d/%m/%Y")
    discard = df["certificado"].isna() & df["subcategoria"].isin(TO_DISCARD["ml"])
    delete_files(df, discard)
    df = df.loc[~discard]
    df["Unidades à Venda"] = df["estoque"]
    columns = [
        "Existe campo código SCH?",
        "Código SCH foi fornecido?",
    ]
    for column in columns:
        df[column] = "Sim"
        df.loc[df["certificado"].isna(), column] = "Não"
    columns = [
        "O produto é homologado?",
        "Código SCH é o do produto?",
        "Código EAN é o do produto?",
    ]
    for column in columns:
        df[column] = ""

    column = "O código EAN foi fornecido?"
    df[column] = "Sim"
    df.loc[df["ean_gtin"].isna(), column] = "Não"
    write_excel(df, output_file.with_suffix(".xlsx"), "ml-smartphone")


def process_magalu(output_file, category="Celulares e Smartphones"):
    df = pd.DataFrame(output_file.read_json().values(), dtype="string")
    df = preprocess(df)
    for cat in SUBCATEGORIES["magalu"]:
        df.loc[df["subcategoria"].str.lower().str.contains(cat), "subcategoria"] = (
            category
        )

    df = df.loc[df["subcategoria"] == category]
    df["Data"] = pd.to_datetime(df["data"], format="mixed").dt.strftime("%d/%m/%Y")
    discard = df["certificado"].isna() & df["subcategoria"].isin(TO_DISCARD["magalu"])
    delete_files(df, discard)
    df = df.loc[~discard]
    df["Unidades à Venda"] = "Não Informado"
    columns = [
        "Existe campo código SCH?",
        "Código SCH foi fornecido?",
    ]
    for column in columns:
        df[column] = "Sim"
        df.loc[df["certificado"].isna(), column] = "Não"
    columns = [
        "O produto é homologado?",
        "Código SCH é o do produto?",
        "Código EAN é o do produto?",
    ]
    for column in columns:
        df[column] = ""

    column = "O código EAN foi fornecido?"
    df[column] = "Sim"
    df.loc[df["ean_gtin"].isna(), column] = "Não"

    write_excel(df, output_file.with_suffix(".xlsx"), "magalu-smartphone")


def process_carrefour(output_file, category="Smartphones"):
    df = pd.DataFrame(output_file.read_json().values(), dtype="string")
    df.loc[df["nome"].str.lower().str.contains("smartphone"), "categoria"] = category
    df = preprocess(df)
    for cat in SUBCATEGORIES["carrefour"]:
        df.loc[df["subcategoria"].str.lower().str.contains(cat), "subcategoria"] = (
            category
        )
    df = df.loc[df["subcategoria"] == category]
    df["Data"] = pd.to_datetime(df["data"], format="mixed").dt.strftime("%d/%m/%Y")
    discard = df["certificado"].isna() & df["subcategoria"].isin(TO_DISCARD["amazon"])
    delete_files(df, discard)
    df = df.loc[~discard]
    df["Unidades à Venda"] = "Não Informado"
    columns = [
        "Existe campo código SCH?",
        "Código SCH foi fornecido?",
    ]
    for column in columns:
        df[column] = "Sim"
        df.loc[df["certificado"].isna(), column] = "Não"
    columns = [
        "O produto é homologado?",
        "Código SCH é o do produto?",
        "Código EAN é o do produto?",
    ]
    for column in columns:
        df[column] = ""

    column = "O código EAN foi fornecido?"
    df[column] = "Sim"
    df.loc[df["ean_gtin"].isna(), column] = "Não"

    write_excel(df, output_file.with_suffix(".xlsx"), "carrefour-smartphone")


def process_americanas(output_file, category="smartphone"):
    df = pd.DataFrame(output_file.read_json().values(), dtype="string")
    for row in df.itertuples():
        chrs = eval(row.características)
        df.loc[row.Index, "ean_gtin"] = chrs.get("Código de barras", "")
    df = preprocess(df)
    df["subcategoria"] = df["categoria_2"]
    for cat in SUBCATEGORIES["americanas"]:
        df.loc[df["subcategoria"].str.lower().str.contains(cat), "subcategoria"] = (
            category
        )

    df = df.loc[df["subcategoria"] == category]
    df["Data"] = pd.to_datetime(df["data"], format="mixed").dt.strftime("%d/%m/%Y")
    discard = df["certificado"].isna() & df["subcategoria"].isin(
        TO_DISCARD["americanas"]
    )
    delete_files(df, discard)
    df = df.loc[~discard]
    df["Unidades à Venda"] = "Não Informado"
    columns = [
        "Existe campo código SCH?",
        "Código SCH foi fornecido?",
    ]
    for column in columns:
        df[column] = "Sim"
        df.loc[df["certificado"].isna(), column] = "Não"
    columns = [
        "O produto é homologado?",
        "Código SCH é o do produto?",
        "Código EAN é o do produto?",
    ]
    for column in columns:
        df[column] = ""

    column = "O código EAN foi fornecido?"
    df[column] = "Sim"
    df.loc[df["ean_gtin"].isna(), column] = "Não"

    write_excel(df, output_file.with_suffix(".xlsx"), "americanas-smartphone")


def process_casasbahia(output_file, category="Celulares e Smartphones"):
    df = pd.DataFrame(output_file.read_json().values(), dtype="string")
    for col in COLUNAS[11:]:
        df[col] = ""
    df["Item"] = df.index.to_list()
    for col in ["Arquivo", "Fabricante", "Modelo"]:
        df[col] = ""
    df["Categoria"] = category
    # df["Data"] = pd.to_datetime(df["data"], format="mixed").dt.strftime("%d/%m/%Y")
    df["Data"] = TODAY
    df["preço"] = (
        df["preço"].str.replace("R$", "").str.replace(".", "").str.replace(",", ".")
    )
    df = df.sample(65)
    write_excel(df, output_file.with_suffix(".xlsx"), "casasbahia-smartphone")


def process_shopee(output_file, category="Celulares e Smartphones"):
    df = pd.DataFrame(output_file.read_json(), dtype="string")
    for col in COLUNAS[11:]:
        df[col] = ""
    df["Item"] = df.index.to_list()
    for col in ["Arquivo", "Fabricante", "Modelo", "Página"]:
        df[col] = ""
    df["Categoria"] = category
    df["Texto da Busca"] = "smartphone"
    # df["Data"] = pd.to_datetime(df["data"], format="mixed").dt.strftime("%d/%m/%Y")
    df["Data"] = TODAY
    df["preço"] = (
        df["preço"].str.replace("R$", "").str.replace(".", "").str.replace(",", ".")
    )
    df = df.sample(65)
    write_excel(df, output_file.with_suffix(".xlsx"), "casasbahia-smartphone")


def run_inspection(scraper, keyword, headless, screenshot, sample):
    site = SCRAPER[scraper](headless=headless)
    output_file = site.inspect_pages(keyword, screenshot, sample)
    # output_file = Path(FOLDER / scraper / f"{scraper}_{TODAY}_{keyword}.json")
    if scraper == "amazon":
        process_amazon(output_file)
    elif scraper == "ml":
        process_ml(output_file)
    elif scraper == "magalu":
        process_magalu(output_file)
    elif scraper == "carrefour":
        process_carrefour(output_file)
    elif scraper == "americanas":
        process_americanas(output_file)
    elif scraper == "casasbahia":
        process_casasbahia(output_file)
    elif scraper == "shopee":
        process_shopee(output_file)


if __name__ == "__main__":

    def main(
        scraper: str = None,
        keyword: str = KEYWORDS[0],
        search: bool = True,
        headless: bool = True,
        screenshot: bool = False,
        sample: int = 78,
    ):
        if not scraper:
            for scraper in SCRAPER:
                if search:
                    SCRAPER[scraper](headless=headless).search(keyword)
                else:
                    run_inspection(scraper, keyword, headless, screenshot, sample)
        else:
            if search:
                SCRAPER[scraper](headless=headless).search(keyword)
            else:
                run_inspection(scraper, keyword, headless, screenshot, sample)

    typer.run(main)
