from typing import Tuple
import urllib.request
from urllib.parse import unquote
import os
from fastcore.xtras import Path
import pandas as pd
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), override=True)

FOLDER = Path(__file__).parent / "data"

FOLDER.mkdir(exist_ok=True, parents=True)

UPDATE_SCH = False

CERTIFICADO_COLUMNS = {
    "Data da Homologação": "Data_da_Homologação",
    "Número de Homologação": "Número_de_Homologação",
    "Nome do Solicitante": "Nome_do_Solicitante",
    "Data de Validade do Certificado": "Data_de_Validade_do_Certificado",
    "Situação do Certificado": "Situação_do_Certificado",
    "Nome do Fabricante": "Fabricante",
    "Modelo": "Modelo",
    "Nome Comercial": "Nome_Comercial",
    "Tipo do Produto": "Tipo_do_Produto",
}

CONFORMIDADE_COLUMNS = {
    "NumeroHomologacao": "Número_de_Homologação",
    "DataEmissaoHomologacao": "Data_de_Homologação",
    "Fabricante": "Fabricante",
    "Produto": "Tipo_do_Produto",
    "Modelo": "Modelo",
    "NomeComercial": "Nome_Comercial",
    "StatusRequerimento": "Situação_do_Certificado",
}

G5_COLUMNS = {
    "NumeroHomologacao": "Número_de_Homologação",
    "DataEmissaoHomologacao": "Data_de_Homologação",
    "TipodeProduto": "Tipo_do_Produto",
    "Modelo": "Modelo",
    "NomeComercial": "Nome_Comercial",
    "Fabricante": "Fabricante",
}

MARCA_ANATEL_COLUMNS = {
    "Tipo de Produto": "Tipo_do_Produto",
    "Modelo do produto": "Modelo",
    "Nome Comercial": "Nome_Comercial",
    "Empresa Requerente": "Nome_do_Solicitante",
    "Fabricante": "Fabricante",
    "Status da Homologação": "Situação_do_Certificado",
    "Data": "Data_de_Homologação",
}

MATCH_COLUMNS = {
    "Nome_Comercial": "Nome_SCH",
    "Fabricante_y": "Fabricante_SCH",
    "Modelo_y": "Modelo_SCH",
    "Nome_do_Solicitante": "Solicitante",
    "Fabricante_x": "Fabricante",
    "Modelo_x": "Modelo",
}


# XLSX = Path(os.environ.get("ONEDRIVEDEST"))


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
        dtype="string[pyarrow]",
        dtype_backend="pyarrow",
        sep=";",
        usecols=CERTIFICADO_COLUMNS.keys(),
    )
    certificados.rename(columns=CERTIFICADO_COLUMNS, inplace=True)

    if not conformidade_path.is_file():
        update_sch()
    conformidade = pd.read_csv(
        conformidade_path,
        dtype="string[pyarrow]",
        dtype_backend="pyarrow",
        sep=";",
        usecols=CONFORMIDADE_COLUMNS.keys(),
    )
    conformidade.rename(columns=CONFORMIDADE_COLUMNS, inplace=True)

    if not celulares_path.is_file():
        update_sch()
    celulares = pd.read_csv(
        celulares_path,
        dtype="string[pyarrow]",
        dtype_backend="pyarrow",
        sep=";",
        usecols=G5_COLUMNS.keys(),
    )
    celulares.rename(columns=G5_COLUMNS, inplace=True)

    celulares = celulares[
        ~celulares.Número_de_Homologação.isin(certificados.Número_de_Homologação)
    ]

    return pd.concat([certificados, conformidade, celulares], ignore_index=True)


def merge_to_sch(
    df: pd.DataFrame, update: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Merges the given DataFrame df with the SCH homologation database table.

    Matches df and SCH on 'Número_de_Homologação', handling mismatches and duplicates.

    Returns a tuple of:
    - positive: the merged homologations found in both df and SCH.
    - negative: the homologations in df not found in SCH.

    """
    df = df.rename(
        columns={
            "Certificado_de_Homologação": "Número_de_Homologação",
            "Marca": "Fabricante",
        },
    )

    sch_table = read_sch(update)
    df["Número_de_Homologação"] = df["Número_de_Homologação"].astype(
        "string", copy=False
    )

    df.loc[:, "Número_de_Homologação"] = df.Número_de_Homologação.str.replace(".0", "")
    df.loc[:, "Número_de_Homologação"] = df.Número_de_Homologação.str.extract(
        r"(\d{1,12})"
    )[0].values
    df.loc[:, "Número_de_Homologação"] = df.Número_de_Homologação.str.zfill(12)

    hm = pd.merge(
        df,
        sch_table,
        on="Número_de_Homologação",
        copy=False,
        how="left",
        indicator=True,
    ).astype("string")

    hm.drop_duplicates(inplace=True)

    negative = hm[hm._merge == "left_only"].copy()
    negative.drop(["_merge"], axis=1, inplace=True)
    negative = negative.rename(columns=MATCH_COLUMNS)
    negative_columns = [c for c in negative.columns if "_SCH" not in c]
    negative = negative.loc[:, negative_columns]
    positive = hm[hm._merge == "both"].copy()
    positive.drop(
        ["Data_da_Homologação", "Data_de_Homologação", "_merge"], axis=1, inplace=True
    )
    positive = positive.rename(columns=MATCH_COLUMNS)
    return positive, negative
