import pandas as pd

def carregar_dados(caminho_arquivo):
    log = []
    xls = pd.ExcelFile(caminho_arquivo)
    abas_esperadas = ["Operações", "Proventos", "Conversoes_Mapeadas"]
    abas_existentes = xls.sheet_names

    for aba in abas_esperadas:
        if aba not in abas_existentes:
            raise ValueError(f"Aba obrigatória ausente: {aba}")

    df_oper = xls.parse("Operações")
    df_oper = df_oper.rename(columns={
        "ORDEM": "Tipo",
        "BROKER": "Corretora",
        "NEGOCIAÇÃO": "Data",
        "QUANTIDADE": "Quantidade",
        "PREÇO": "Valor Unitário",
        "TOTAL": "Custo/Despesa Total"
    })

    # Normalização de campos
    df_oper["Custo/Despesa Total"] = (
        df_oper["Custo/Despesa Total"]
        .astype(str)
        .str.replace(r"[^\d,.-]", "", regex=True)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    df_oper["Quantidade"] = pd.to_numeric(df_oper["Quantidade"], errors="coerce")
    df_oper["Valor Unitário"] = pd.to_numeric(df_oper["Valor Unitário"], errors="coerce")
    df_oper["Moeda"] = "BRL"

    campos_obrigatorios = ["Data", "Ativo", "Tipo", "Quantidade", "Valor Unitário", "Corretora", "Moeda", "Custo/Despesa Total"]
    for campo in campos_obrigatorios:
        if df_oper[campo].isnull().any():
            log.append(f"❗ Campo obrigatório ausente na aba Operações: {campo}")

    df_prov = xls.parse("Proventos")
    df_prov = df_prov.rename(columns={
        "Pagamento": "Data Pagamento",
        "Valor": "Valor por Cota"
    })
    df_prov["Moeda"] = "BRL"

    df_conv = xls.parse("Conversoes_Mapeadas")
    df_conv = df_conv.rename(columns={
        "Quantidade_De": "Qtde_De",
        "Quantidade_Para": "Qtde_Para",
        "Data_Conversao": "Data",
        "Preco_Medio": "Preco_Medio_Origem",
        "Valor_Retornado": "Retorno_Valor"
    })

    return df_oper, df_prov, df_conv, log
