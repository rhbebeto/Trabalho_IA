import pandas as pd
import os # <-- Importamos a biblioteca 'os'

# --- Encontra o caminho absoluto para a pasta do script ---
# Isso garante que o Python sempre saiba onde o script está.
caminho_do_script = os.path.dirname(os.path.abspath(__file__))

# --- Define o nome do arquivo e cria o caminho completo para ele ---
NOME_ARQUIVO = 'FIFA25_official_data.csv'
caminho_completo_do_arquivo = os.path.join(caminho_do_script, NOME_ARQUIVO)


try:
    # Agora usamos o caminho completo para carregar o arquivo
    df = pd.read_csv(caminho_completo_do_arquivo, low_memory=False)
    print("Arquivo carregado com sucesso!")

    print("\nAs 5 primeiras linhas do dataset:")
    print(df.head())
    
    print("\nTODOS OS NOMES DAS COLUNAS DISPONÍVEIS:")
    print(df.columns.tolist())

except FileNotFoundError:
    print(f"ERRO: O arquivo '{NOME_ARQUIVO}' não foi encontrado no caminho '{caminho_completo_do_arquivo}'.")
    print("Verifique se o nome do arquivo está correto e na mesma pasta que o script.")