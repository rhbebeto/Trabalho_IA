import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
import joblib
import os # <-- ADICIONADO

# --- As mesmas configurações e funções que já tínhamos ---
NOME_ARQUIVO_CSV = 'FIFA25_official_data.csv'
COLUNAS_FEATURES = ['overall_rating', 'potential', 'age'] 
COLUNA_ALVO = 'value'

def converter_valor_para_numero(valor):
    if isinstance(valor, str):
        valor = valor.replace('€', '')
        if 'M' in valor: return float(valor.replace('M', '')) * 1000000
        if 'K' in valor: return float(valor.replace('K', '')) * 1000
    return float(valor)

# --- LÓGICA DE TREINO ---
print("Iniciando o processo de treino...")

# 1. Carregar e preparar os dados
caminho_do_script = os.path.dirname(os.path.abspath(__file__)) # <-- ADICIONADO
caminho_completo_do_arquivo = os.path.join(caminho_do_script, NOME_ARQUIVO_CSV) # <-- ADICIONADO

df = pd.read_csv(caminho_completo_do_arquivo, low_memory=False) # <-- CÓDIGO CORRIGIDO
df['dob'] = pd.to_datetime(df['dob'], errors='coerce')
df['age'] = ((datetime.now() - df['dob']).dt.days / 365.25).astype(int)
df = df.copy()
df[COLUNA_ALVO] = df[COLUNA_ALVO].apply(converter_valor_para_numero)
print("Dados carregados e preparados.")

# 2. Limpar os dados para o treino
df_clean = df.dropna(subset=COLUNAS_FEATURES + [COLUNA_ALVO])
X = df_clean[COLUNAS_FEATURES]
y = df_clean[COLUNA_ALVO]

# 3. Treinar o modelo
model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
model.fit(X, y)
print("Modelo treinado com sucesso.")

# 4. Salvar o modelo e os dados limpos
joblib.dump(model, 'modelo_olheiro.joblib')
df_clean.to_csv('dados_limpos.csv', index=False)
print("Modelo e dados limpos foram salvos!")
print("Pode agora rodar a aplicação Flask ('app.py').")