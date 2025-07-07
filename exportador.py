import pandas as pd

def exportar_planilha(df_posicao, log, caminho_saida):
    with pd.ExcelWriter(caminho_saida, engine="openpyxl") as writer:
        df_posicao.to_excel(writer, sheet_name="Posicao_Consolidada", index=False)
        df_log = pd.DataFrame(log, columns=["Log de Processamento"])
        df_log.to_excel(writer, sheet_name="Log_Processamento", index=False)
