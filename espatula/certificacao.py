import os
import urllib.request
from typing import Tuple
from urllib.parse import unquote

import pandas as pd
from fastcore.xtras import Path

FOLDER = Path(os.environ.get("FOLDER", f"{Path(__file__)}/data"))


CERTIFICADOS = "https://www.anatel.gov.br/dadosabertos/paineis_de_dados/certificacao_de_produtos/produtos_certificados.zip"
CONFORMIDADE = "https://www.anatel.gov.br/dadosabertos/paineis_de_dados/certificacao_de_produtos/Produtos_Homologados_por_Declara%C3%A7%C3%A3o_de_Conformidade.zip"
G5 = "https://www.anatel.gov.br/dadosabertos/paineis_de_dados/certificacao_de_produtos/celulares_5g_homologados.zip"


CERTIFICADO_COLUMNS = {
    "Data da Homologação": "Data_de_Homologação",
    "Número de Homologação": "certificado",
    "Nome do Solicitante": "Nome_do_Solicitante",
    "Data de Validade do Certificado": "Data_de_Validade_do_Certificado",
    "Situação do Certificado": "Situação_do_Certificado",
    "Nome do Fabricante": "fabricante_sch",
    "Modelo": "modelo_sch",
    "Nome Comercial": "nome_sch",
    "Tipo do Produto": "tipo_sch",
}

# CONFORMIDADE_COLUMNS = {
#     "NumeroHomologacao": "certificado",
#     "DataEmissaoHomologacao": "Data_de_Homologação",
#     "Fabricante": "fabricante",
#     "Produto": "tipo_sch",
#     "Modelo": "modelo",
#     "NomeComercial": "nome",
#     "StatusRequerimento": "Situação_do_Certificado",
# }

G5_COLUMNS = {
    "NumeroHomologacao": "certificado",
    "DataEmissaoHomologacao": "Data_de_Homologação",
    "TipodeProduto": "tipo_sch",
    "Modelo": "modelo_sch",
    "NomeComercial": "nome_sch",
    "Fabricante": "fabricante_sch",
}

# MARCA_ANATEL_COLUMNS = {
#     "Tipo de Produto": "tipo_sch",
#     "Modelo do produto": "modelo",
#     "Nome Comercial": "nome",
#     "Empresa Requerente": "Nome_do_Solicitante",
#     "Fabricante": "fabricante",
#     "Status da Homologação": "Situação_do_Certificado",
#     "Data": "Data_de_Homologação",
# }

# MATCH_COLUMNS = {
#     "nome_x": "nome",
#     "nome_y": "nome_sch",
#     "fabricante_x": "fabricante",
#     "fabricante_y": "fabricante_sch",
#     "modelo_x": "modelo",
#     "modelo_y": "modelo_sch",
# }

COLS_SCH = ["nome_sch", "fabricante_sch", "modelo_sch", "tipo_sch"]


def update_sch():
    for source in [
        CERTIFICADOS,
        # CONFORMIDADE,
        G5,
    ]:
        urllib.request.urlretrieve(
            source, Path(f"{FOLDER}/{unquote(source.split('/')[-1])}")
        )


def read_sch(update: bool = False) -> pd.DataFrame:
    """Reads SCH homologation data from cached files, updates if requested,
    concatenates and returns as DataFrame.

    Parameters:
        update (bool): Whether to re-download latest files before reading.

    Returns:
        pd.DataFrame: DataFrame containing concatenated homologation data.
    """
    if update:
        update_sch()

    certificados_path = FOLDER / "produtos_certificados.zip"
    # conformidade_path = (
    #     FOLDER / "Produtos_Homologados_por_Declaração_de_Conformidade.zip"
    # )
    celulares_path = FOLDER / "celulares_5g_homologados.zip"

    if not certificados_path.is_file():
        update_sch()
    certificados = pd.read_csv(
        certificados_path,
        dtype="string",
        sep=";",
        usecols=CERTIFICADO_COLUMNS.keys(),
    )
    certificados.rename(columns=CERTIFICADO_COLUMNS, inplace=True)

    # if not conformidade_path.is_file():
    #     update_sch()
    # conformidade = pd.read_csv(
    #     conformidade_path,
    #     dtype="string",
    #     sep=";",
    #     usecols=CONFORMIDADE_COLUMNS.keys(),
    # )
    # conformidade.rename(columns=CONFORMIDADE_COLUMNS, inplace=True)

    if not celulares_path.is_file():
        update_sch()
    celulares = pd.read_csv(
        celulares_path,
        dtype="string",
        sep=";",
        usecols=G5_COLUMNS.keys(),
    )
    celulares.rename(columns=G5_COLUMNS, inplace=True)

    celulares = celulares[~celulares.certificado.isin(certificados.certificado)]

    df = pd.concat([certificados, celulares], ignore_index=True)

    cols = ["certificado"] + COLS_SCH

    return df.loc[:, cols]


def merge_to_sch(
    df: pd.DataFrame, update: bool = False, tipo_sch: str = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Merges the given DataFrame df with the SCH homologation database table.

    Matches df and SCH on 'certificado', handling mismatches and duplicates.

    Returns a tuple of:
    - positive: the merged homologations found in both df and SCH.
    - negative: the homologations in df not found in SCH.

    """
    df = df.rename(
        columns={
            "marca": "fabricante",
        },
    )

    sch_table = read_sch(update)
    df["certificado"] = df["certificado"].astype("string", copy=False)

    df.loc[:, "certificado"] = df.certificado.str.replace(".0", "")
    df.loc[:, "certificado"] = df.certificado.str.extract(r"(\d{1,12})")[0].values
    df.loc[:, "certificado"] = df.certificado.str.zfill(12)

    hm = pd.merge(
        df,
        sch_table,
        on="certificado",
        copy=False,
        how="left",
        indicator=True,
    ).astype("string")

    if tipo_sch is not None:
        hm = hm.loc[hm.tipo_sch == tipo_sch].drop_duplicates().reset_index(drop=True)
    return hm.drop("_merge", axis=1)
