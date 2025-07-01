import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

# --- CONFIGURAÇÕES ---
NOME_ARQUIVO_CSV = 'FIFA25_official_data.csv'
COLUNAS_FEATURES = ['overall_rating', 'potential', 'age'] 
COLUNA_ALVO = 'value'

def converter_valor_para_numero(valor):
    if isinstance(valor, str):
        valor = valor.replace('€', '')
        if 'M' in valor: return float(valor.replace('M', '')) * 1000000
        if 'K' in valor: return float(valor.replace('K', '')) * 1000
    return float(valor)

print("Iniciando o processo de treino...")

# --- PARTE 1: Carregar e Preparar os Dados ---
caminho_do_script = os.path.dirname(os.path.abspath(__file__))
caminho_completo_do_arquivo = os.path.join(caminho_do_script, NOME_ARQUIVO_CSV)

df = pd.read_csv(caminho_completo_do_arquivo, low_memory=False)

# --- NOVO: Bloco de Conversão de Tipos de Dados ---
# Lista de colunas que devem ser numéricas para nossos filtros
colunas_numericas = [
    'weak_foot', 'skill_moves', 'club_contract_valid_until', 
    'acceleration', 'sprint_speed', 'finishing', 
    'defensive_awareness', 'standing_tackle'
]
# Convertemos cada coluna para número. `errors='coerce'` transforma o que não for número em NaN (vazio).
for col in colunas_numericas:
    df[col] = pd.to_numeric(df[col], errors='coerce')
print("Tipos de dados das colunas de filtro corrigidos.")
# --- FIM DO NOVO BLOCO ---

df['dob'] = pd.to_datetime(df['dob'], errors='coerce')
df['age'] = ((datetime.now() - df['dob']).dt.days / 365.25).astype(int)
df = df.copy()
df[COLUNA_ALVO] = df[COLUNA_ALVO].apply(converter_valor_para_numero)
print("Dados carregados e preparados.")

# Limpar os dados para o treino
df_clean = df.dropna(subset=COLUNAS_FEATURES + [COLUNA_ALVO])
X = df_clean[COLUNAS_FEATURES]
y = df_clean[COLUNA_ALVO]

# Treinar o modelo
model = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
model.fit(X, y)
print("Modelo treinado com sucesso.")

# Salvar o modelo e os dados limpos
joblib.dump(model, 'modelo_olheiro.joblib')
df_clean.to_csv('dados_limpos.csv', index=False)
print("Modelo e dados limpos foram salvos!")
print("Pode agora rodar a aplicação Flask ('app.py').")