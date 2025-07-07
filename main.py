from leitor_planilha import carregar_dados
from consolidar_posicao import consolidar_posicao
from exportador import exportar_planilha
import datetime
import os

CAMINHO_ARQUIVO = os.path.join("data", "OV10_base_2025.xlsx")

def main():
    print("🔄 Iniciando leitura da planilha...")
    df_operacoes, df_proventos, df_conversoes, log_leitura = carregar_dados(CAMINHO_ARQUIVO)

    print("📊 Consolidando posição patrimonial...")
    df_posicao, log_consolidacao = consolidar_posicao(df_operacoes, df_proventos, df_conversoes)

    print("💾 Exportando arquivo final...")
    data_hoje = datetime.datetime.now().strftime("%Y%m%d")
    caminho_saida = os.path.join("data", f"OV10_output_{data_hoje}.xlsx")
    exportar_planilha(df_posicao, log_leitura + log_consolidacao, caminho_saida)

    print(f"✅ Processo concluído com sucesso! Arquivo gerado: {caminho_saida}")

if __name__ == "__main__":
    main()
