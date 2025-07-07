import pandas as pd

def consolidar_posicao(df_oper, df_prov, df_conv):
    log = []
    oper = df_oper.copy()

    # Normalizar tipos conhecidos
    tipos_entrada = ["Compra", "Bonificação", "Conversão (E)"]
    tipos_saida = ["Venda", "Conversão (S)"]

    ativos = oper["Ativo"].unique()
    resultados = []

    for ativo in ativos:
        df_ativo = oper[oper["Ativo"] == ativo]

        # Filtrar entradas e saídas
        entradas = df_ativo[df_ativo["Tipo"].isin(tipos_entrada)]
        saidas = df_ativo[df_ativo["Tipo"].isin(tipos_saida)]

        qtde_entrada = entradas["Quantidade"].sum()
        qtde_saida = saidas["Quantidade"].sum()
        quantidade_final = qtde_entrada - qtde_saida

        # Total investido = soma dos custos das entradas (com taxas)
        custo_total_entrada = entradas["Custo/Despesa Total"].sum()
        preco_medio_compra = (
            custo_total_entrada / qtde_entrada if qtde_entrada > 0 else 0
        )

        # Total vendido = valor obtido nas saídas
        valor_total_saida = (saidas["Valor Unitário"] * saidas["Quantidade"]).sum()
        preco_medio_venda = (
            valor_total_saida / qtde_saida if qtde_saida > 0 else None
        )

        total_investido = preco_medio_compra * quantidade_final
        lucro_preju = valor_total_saida - (qtde_saida * preco_medio_compra)

        if quantidade_final < 0:
            log.append(f"❗ Ativo {ativo} com quantidade final negativa: {quantidade_final}. Verifique conversões ou dados incoerentes.")

        resultados.append({
            "Ativo": ativo,
            "Quantidade Final": round(quantidade_final, 6),
            "Preço Médio de Compra": round(preco_medio_compra, 6),
            "Preço Médio de Venda": round(preco_medio_venda, 6) if preco_medio_venda else None,
            "Total Investido": round(total_investido, 2),
            "Total Vendido": round(valor_total_saida, 2),
            "Lucro/Prejuízo": round(lucro_preju, 2)
        })

    df_resultado = pd.DataFrame(resultados)
    return df_resultado, log
