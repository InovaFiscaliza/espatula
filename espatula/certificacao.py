import os
import urllib.request
from typing import Tuple
from urllib.parse import unquote

import pandas as pd
from dotenv import find_dotenv, load_dotenv
from fastcore.xtras import Path

from espatula.constantes import FOLDER

load_dotenv(find_dotenv(), override=True)

CERTIFICADO_COLUMNS = {
    "Data da Homologação": "Data_da_Homologação",
    "Número de Homologação": "certificado",
    "Nome do Solicitante": "Nome_do_Solicitante",
    "Data de Validade do Certificado": "Data_de_Validade_do_Certificado",
    "Situação do Certificado": "Situação_do_Certificado",
    "Nome do Fabricante": "fabricante",
    "Modelo": "Modelo",
    "Nome Comercial": "Nome_Comercial",
    "Tipo do Produto": "Tipo_do_Produto",
}

CONFORMIDADE_COLUMNS = {
    "NumeroHomologacao": "certificado",
    "DataEmissaoHomologacao": "Data_de_Homologação",
    "Fabricante": "fabricante",
    "Produto": "Tipo_do_Produto",
    "Modelo": "Modelo",
    "NomeComercial": "Nome_Comercial",
    "StatusRequerimento": "Situação_do_Certificado",
}

G5_COLUMNS = {
    "NumeroHomologacao": "certificado",
    "DataEmissaoHomologacao": "Data_de_Homologação",
    "TipodeProduto": "Tipo_do_Produto",
    "Modelo": "Modelo",
    "NomeComercial": "Nome_Comercial",
    "Fabricante": "fabricante",
}

MARCA_ANATEL_COLUMNS = {
    "Tipo de Produto": "Tipo_do_Produto",
    "Modelo do produto": "Modelo",
    "Nome Comercial": "Nome_Comercial",
    "Empresa Requerente": "Nome_do_Solicitante",
    "Fabricante": "fabricante",
    "Status da Homologação": "Situação_do_Certificado",
    "Data": "Data_de_Homologação",
}

MATCH_COLUMNS = {
    "Nome_Comercial": "nome_sch",
    "fabricante_x": "fabricante",
    "fabricante_y": "fabricante_sch",
    "Modelo_x": "modelo",
    "Modelo_y": "modelo_SCH",
}


def update_sch():
    for source in [
        os.environ["CERTIFICADOS"],
        os.environ["CONFORMIDADE"],
        os.environ["G5"],
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
    conformidade_path = (
        FOLDER / "Produtos_Homologados_por_Declaração_de_Conformidade.zip"
    )
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

    if not conformidade_path.is_file():
        update_sch()
    conformidade = pd.read_csv(
        conformidade_path,
        dtype="string",
        sep=";",
        usecols=CONFORMIDADE_COLUMNS.keys(),
    )
    conformidade.rename(columns=CONFORMIDADE_COLUMNS, inplace=True)

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

    return pd.concat([certificados, conformidade, celulares], ignore_index=True)


def merge_to_sch(
    df: pd.DataFrame, update: bool = False
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

    hm.drop_duplicates(inplace=True)
    hm = hm.rename(columns=MATCH_COLUMNS)
    columns = df.columns.tolist() + list(MATCH_COLUMNS.values())
    return hm.loc[:, columns]
