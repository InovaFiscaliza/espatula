import sys
from fastcore.xtras import Path

import typer
import pandas as pd


sys.path.append(str(Path(__file__).parent.parent))
from amazon import AmazonScraper
from mercado_livre import MercadoLivreScraper
from magalu import MagaluScraper
from americanas import AmericanasScraper

# from casas_bahia import CasasBahiaScraper
from carrefour import CarrefourScraper
from base import KEYWORDS, FOLDER

PREFIX = "https://anatel365.sharepoint.com/sites/Desenvolvimentodeappfiscalizaoe-commerce/Documentos%20Compartilhados/General/Resultados/screenshots/"


COLUNAS = [
    "Item",
    "Texto da Busca",
    "Arquivo da Página",
    "Data da Coleta",
    "Endereço eletrônico (URL)",
    "Descrição do produto no anúncio",
    "Tipo do Produto",
    "Fabricante",
    "Modelo do Produto",
    "Valor do Produto (R$)",
    "Número de Unidades à Venda",
    "Existe o campo código de homologação no anúncio? (Sim ou Não)",
    "O código de homologação foi fornecido? (Sim ou Não)",
    "O produto é homologado? (Sim, Não e N.A.)",
    "Validação do código de homologação - O código de homologação fornecido é o do produto anunciado? (Sim, Não, N.A.)",
    "O código EAN foi fornecido? (Sim ou Não) - Apenas para Smartphones.",
    "O código EAN fornecido corresponde ao produto? (Sim ou Não) -  Apenas para Smartphones.",
    "Observação 1 - Qual Código de Homologação fornecido no anúncio?",
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
}

SUBCATEGORIES = {
    "amazon": ["Celulares e Smartphones"],
    "ml": ["Celulares e Smartphones"],
}


SCRAPER = {
    "amazon": {"scraper": AmazonScraper, "processor": None},
    "mercado_livre": MercadoLivreScraper,
    "magalu": MagaluScraper,
    "americanas": AmericanasScraper,
    # "casas_bahia": CasasBahiaScraper,
    "carrefour": CarrefourScraper,
}


def split_categories(df):
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
    for i, link in enumerate(df["Arquivo da Página"], start=2):
        pdf = PREFIX + link
        worksheet.write_url(f"C{i}", pdf, string=link)
    writer.close()


def process_amazon(output_file, category="Celulares e Smartphones"):
    df = pd.DataFrame(output_file.read_json().values(), dtype="string")
    df = split_categories(df)
    df = df.loc[df["subcategoria"] == category]
    df["Item"] = df.index.to_list()
    df["Data da Coleta"] = pd.to_datetime(df["data"], format="mixed").dt.strftime(
        "%d/%m/%Y"
    )
    discard = df["certificado"].isna() & df["subcategoria"].isin(TO_DISCARD["amazon"])
    df = df.loc[~discard]
    df["Número de Unidades à Venda"] = "Não Informado"
    columns = [
        "Existe o campo código de homologação no anúncio? (Sim ou Não)",
        "O código de homologação foi fornecido? (Sim ou Não)",
    ]
    for column in columns:
        df[column] = "Sim"
        df.loc[df["certificado"].isna(), column] = "Não"
    columns = [
        "O produto é homologado? (Sim, Não e N.A.)",
        "Validação do código de homologação - O código de homologação fornecido é o do produto anunciado? (Sim, Não, N.A.)",
        "O código EAN fornecido corresponde ao produto? (Sim ou Não) -  Apenas para Smartphones.",
    ]
    for column in columns:
        df[column] = ""

    column = "O código EAN foi fornecido? (Sim ou Não) - Apenas para Smartphones."
    df[column] = "Sim"
    df.loc[df["ean_gtin"].isna(), column] = "Não"
    df.rename(
        columns={
            "palavra_busca": "Texto da Busca",
            "screenshot": "Arquivo da Página",
            "url": "Endereço eletrônico (URL)",
            "nome": "Descrição do produto no anúncio",
            "subcategoria": "Tipo do Produto",
            "marca": "Fabricante",
            "modelo": "Modelo do Produto",
            "preço": "Valor do Produto (R$)",
            "certificado": "Observação 1 - Qual Código de Homologação fornecido no anúncio?",
        },
        inplace=True,
    )

    df = df[COLUNAS]
    write_excel(df, output_file.with_suffix(".xlsx"), "amazon-smartphone")


def process_ml(output_file, category="Celulares e Smartphones"):
    df = pd.DataFrame(output_file.read_json().values(), dtype="string")
    df = split_categories(df)
    df["subcategoria"] = df["categoria_1"]
    df = df.loc[df["subcategoria"] == category]
    df["Item"] = df.index.to_list()
    df["Data da Coleta"] = pd.to_datetime(df["data"], format="mixed").dt.strftime(
        "%d/%m/%Y"
    )
    discard = df["certificado"].isna() & df["subcategoria"].isin(TO_DISCARD["ml"])
    df = df.loc[~discard]
    df["Número de Unidades à Venda"] = df["estoque"]
    columns = [
        "Existe o campo código de homologação no anúncio? (Sim ou Não)",
        "O código de homologação foi fornecido? (Sim ou Não)",
    ]
    for column in columns:
        df[column] = "Sim"
        df.loc[df["certificado"].isna(), column] = "Não"
    columns = [
        "O produto é homologado? (Sim, Não e N.A.)",
        "Validação do código de homologação - O código de homologação fornecido é o do produto anunciado? (Sim, Não, N.A.)",
        "O código EAN fornecido corresponde ao produto? (Sim ou Não) -  Apenas para Smartphones.",
    ]
    for column in columns:
        df[column] = ""

    column = "O código EAN foi fornecido? (Sim ou Não) - Apenas para Smartphones."
    df[column] = "Sim"
    df.loc[df["ean_gtin"].isna(), column] = "Não"
    df.rename(
        columns={
            "palavra_busca": "Texto da Busca",
            "screenshot": "Arquivo da Página",
            "url": "Endereço eletrônico (URL)",
            "nome": "Descrição do produto no anúncio",
            "subcategoria": "Tipo do Produto",
            "marca": "Fabricante",
            "modelo": "Modelo do Produto",
            "preço": "Valor do Produto (R$)",
            "certificado": "Observação 1 - Qual Código de Homologação fornecido no anúncio?",
        },
        inplace=True,
    )

    df = df[COLUNAS]
    write_excel(df, output_file.with_suffix(".xlsx"), "ml-smartphone")


def run_inspection(scraper, keyword, headless, screenshot, sample):
    site = SCRAPER[scraper](headless=headless)
    output_file = site.inspect_pages(keyword, screenshot, sample)
    if scraper == "amazon":
        process_amazon(output_file)


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
