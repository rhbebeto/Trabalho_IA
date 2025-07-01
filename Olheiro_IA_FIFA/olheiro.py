import pandas as pd
import os
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

# --- CONFIGURAÇÕES E VARIÁVEIS (AJUSTADAS PARA O FIFA 25) ---
NOME_ARQUIVO_CSV = 'FIFA25_official_data.csv'

# **LISTA DE FEATURES SIMPLIFICADA E MAIS ROBUSTA**
COLUNAS_FEATURES = ['overall_rating', 'potential', 'age'] 

COLUNA_ALVO = 'value'
COLUNAS_DISPLAY = ['name', 'age', 'club_name', 'overall_rating', 'potential', 'value']

def converter_valor_para_numero(valor):
    if isinstance(valor, str):
        valor = valor.replace('€', '')
        if 'M' in valor:
            return float(valor.replace('M', '')) * 1000000
        if 'K' in valor:
            return float(valor.replace('K', '')) * 1000
    return float(valor)

print("--- Olheiro de IA para o Modo Carreira FIFA ---")

# --- PARTE 1: Carregar e Preparar os Dados ---
caminho_do_script = os.path.dirname(os.path.abspath(__file__))
caminho_completo_do_arquivo = os.path.join(caminho_do_script, NOME_ARQUIVO_CSV)

print(f"\nCarregando a base de dados de '{NOME_ARQUIVO_CSV}'...")
try:
    df = pd.read_csv(caminho_completo_do_arquivo, low_memory=False)
except FileNotFoundError:
    print(f"ERRO: O arquivo '{NOME_ARQUIVO_CSV}' não foi encontrado.")
    exit()

df['dob'] = pd.to_datetime(df['dob'], errors='coerce')
df['age'] = ((datetime.now() - df['dob']).dt.days / 365.25).astype(int)
df = df.copy()
df[COLUNA_ALVO] = df[COLUNA_ALVO].apply(converter_valor_para_numero)
print("Dados carregados e idade dos jogadores calculada!")

# --- PARTE 2: Treinar o Modelo ---
print("\nTreinando o modelo de IA para entender o mercado...")
df_clean = df.dropna(subset=COLUNAS_FEATURES + [COLUNA_ALVO])

# Checagem final para garantir que não está vazio
if df_clean.empty:
    print("\nERRO CRÍTICO: Após a limpeza, o conjunto de dados ficou vazio.")
    print("Verifique se as colunas selecionadas em 'COLUNAS_FEATURES' existem e possuem dados.")
    exit()

X = df_clean[COLUNAS_FEATURES]
y = df_clean[COLUNA_ALVO]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)
score = model.score(X_test, y_test)
print(f"Modelo treinado! Precisão da avaliação de mercado: {score:.2f}")

# --- PARTE 3: Caçar as Jovens Promessas ---
print("\nBuscando as melhores 'joias' escondidas no mercado...")
promessas = df_clean[(df_clean['age'] <= 21) & (df_clean['potential'] >= 85)].copy()
promessas['custo_beneficio'] = promessas['potential'] / (promessas[COLUNA_ALVO] + 1)
top_10_promessas = promessas.sort_values(by='custo_beneficio', ascending=False).head(10)

print("\n--- TOP 10 JOVENS PROMESSAS (CUSTO-BENEFÍCIO) ---")
pd.options.display.float_format = '€{:,.0f}'.format
print(top_10_promessas[COLUNAS_DISPLAY])