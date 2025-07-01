from flask import Flask, render_template, request
import pandas as pd
import joblib

# Inicializa a aplicação Flask
app = Flask(__name__)

# Carrega o modelo e os dados UMA VEZ quando a aplicação inicia para ser rápido
print("Carregando modelo e dados para a aplicação web...")
model = joblib.load('modelo_olheiro.joblib')
df = pd.read_csv('dados_limpos.csv')
print("Aplicação pronta para receber buscas.")

# Define a rota para a página inicial
@app.route('/')
def home():
    # Apenas mostra a página 'index.html' com o formulário de busca
    return render_template('index.html')

# Define a rota que recebe os dados do formulário e mostra os resultados
@app.route('/buscar', methods=['POST'])
def buscar():
    # Pega os dados do formulário que o usuário preencheu
    orcamento = float(request.form['orcamento'])
    idade_max = int(request.form['idade_max'])
    potencial_min = int(request.form['potencial_min'])

    # Filtra os jogadores com base nas escolhas do usuário
    resultados = df[
        (df['value'] <= orcamento) &
        (df['age'] <= idade_max) &
        (df['potential'] >= potencial_min)
    ].copy()

    # Se encontrarmos resultados, calculamos o custo-benefício e ordenamos
    if not resultados.empty:
        resultados['custo_beneficio'] = resultados['potential'] / (resultados['value'] + 1)
        top_jogadores = resultados.sort_values(by='custo_beneficio', ascending=False).head(10)
    else:
        top_jogadores = pd.DataFrame() # Cria uma tabela vazia se não achar ninguém

    # Envia os resultados para a página 'resultados.html' para serem exibidos
    return render_template('resultados.html', jogadores=top_jogadores.to_dict('records'), orcamento=orcamento)

if __name__ == '__main__':
    app.run(debug=True)