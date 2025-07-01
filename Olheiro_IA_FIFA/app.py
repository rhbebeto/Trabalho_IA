from flask import Flask, render_template, request, session, redirect, url_for, abort, jsonify
import pandas as pd
import os
import numpy as np
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_super_dificil'

# --- FUNÇÕES HELPER ---
def converter_valor_para_numero(valor):
    if isinstance(valor, str):
        valor_limpo = valor.replace('€', '')
        if 'M' in valor_limpo: return float(valor_limpo.replace('M', '')) * 1000000
        elif 'K' in valor_limpo: return float(valor_limpo.replace('K', '')) * 1000
        return float(valor_limpo)
    return float(valor)

def extrair_stat_base(valor):
    if isinstance(valor, str):
        return valor.split('+')[0].split('-')[0]
    return valor

# --- CARREGAMENTO E PREPARAÇÃO INICIAL ---
print("Carregando e preparando dados...")
caminho_do_script = os.path.dirname(os.path.abspath(__file__))
caminho_dados_originais = os.path.join(caminho_do_script, 'FIFA25_official_data.csv')
df = pd.read_csv(caminho_dados_originais, low_memory=False)

print("Limpando e preparando os dados...")
df['value'] = df['value'].apply(converter_valor_para_numero)
df['wage'] = df['wage'].apply(converter_valor_para_numero)

colunas_para_converter = [
    'weak_foot', 'skill_moves', 'club_contract_valid_until', 'overall_rating', 'potential', 'player_id', 'finishing', 
    'heading_accuracy', 'volleys', 'dribbling', 'curve', 'fk_accuracy', 'ball_control', 'acceleration', 
    'sprint_speed', 'agility', 'balance', 'shot_power', 'jumping', 'stamina', 'strength', 'aggression', 
    'interceptions', 'positioning', 'vision', 'penalties', 'defensive_awareness', 'standing_tackle', 'sliding_tackle', 'club_rating'
]
for col in colunas_para_converter:
    if col in df.columns:
        df[col] = df[col].apply(extrair_stat_base)
        df[col] = pd.to_numeric(df[col], errors='coerce')

df['dob'] = pd.to_datetime(df['dob'], errors='coerce')
df['age'] = ((pd.to_datetime('today') - df['dob']).dt.days / 365.25).astype(int)
colunas_essenciais = ['name', 'age', 'overall_rating', 'potential', 'value', 'wage', 'positions', 'player_id']
df.dropna(subset=colunas_essenciais, inplace=True)
df['positions'] = df['positions'].astype(str)

# --- DEFINIÇÃO DAS LISTAS GLOBAIS (AGORA NO LUGAR CERTO) ---
POSICOES_UNICAS = sorted(list(set(','.join(df['positions'].dropna().unique()).split(','))))
PAISES_UNICOS = sorted(df['country_name'].dropna().unique())
LIGAS_UNICAS = sorted(df['club_league_name'].dropna().unique())
CLUBES_UNICOS = sorted(df['club_name'].dropna().unique())
RIVALRIES = {
    'Real Madrid CF': ['FC Barcelona', 'Atlético de Madrid'], 'FC Barcelona': ['Real Madrid CF', 'RCD Espanyol'],
    'Atlético de Madrid': ['Real Madrid CF'], 'Manchester City': ['Manchester United', 'Liverpool'],
    'Manchester United': ['Manchester City', 'Liverpool', 'Leeds United'], 'Liverpool': ['Manchester United', 'Everton', 'Manchester City'],
    'Arsenal': ['Tottenham Hotspur', 'Chelsea'], 'Tottenham Hotspur': ['Arsenal', 'Chelsea'], 'Chelsea': ['Arsenal', 'Tottenham Hotspur'],
    'Inter': ['AC Milan', 'Juventus'], 'AC Milan': ['Inter'], 'Juventus': ['Inter', 'Torino'], 'AS Roma': ['Lazio'], 'Lazio': ['AS Roma'],
    'FC Bayern München': ['Borussia Dortmund'], 'Borussia Dortmund': ['FC Bayern München', 'FC Schalke 04'],
    'SL Benfica': ['FC Porto', 'Sporting CP'], 'FC Porto': ['SL Benfica', 'Sporting CP'], 'Sporting CP': ['SL Benfica', 'FC Porto'],
    'Boca Juniors': ['River Plate'], 'River Plate': ['Boca Juniors']
}
LEAGUE_FINANCIAL_POWER = {'Premier League': 10, 'LaLiga Santander': 9, 'Bundesliga': 8, 'Serie A TIM': 8, 'Ligue 1 Uber Eats': 7, 'Saudi Pro League': 9, 'MLS': 6}

print("Aplicação pronta.")

# --- ROTAS DA APLICAÇÃO ---
@app.route('/')
def home():
    session.pop('search_filters', None) 
    return render_template('index.html', posicoes=POSICOES_UNICAS, paises=PAISES_UNICOS, ligas=LIGAS_UNICAS)

@app.route('/buscar', methods=['POST', 'GET'])
def buscar():
    if request.method == 'POST':
        filters = request.form.to_dict()
        session['search_filters'] = filters
        return redirect(url_for('buscar'))
    filters = session.get('search_filters')
    if not filters:
        return redirect(url_for('home'))
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'overall_rating')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Coleta dos Filtros
    nome_jogador = filters.get('nome_jogador', '').strip()
    idade_min = int(filters.get('idade_min') or 0)
    idade_max = int(filters.get('idade_max') or 50)
    overall_min = int(filters.get('overall_min') or 0)
    overall_max = int(filters.get('overall_max') or 99)
    potential_min = int(filters.get('potential_min') or 0)
    potential_max = int(filters.get('potential_max') or 99)
    valor_min = float(filters.get('valor_min') or 0)
    valor_max = float(filters.get('valor_max') or 300000000)
    salario_max = float(filters.get('salario_max') or 1000000)
    pais = filters.get('pais', 'any')
    liga = filters.get('liga', 'any')
    posicao = filters.get('posicao', 'any')

    resultados = df.copy()
    if nome_jogador:
        resultados = resultados[resultados['name'].str.contains(nome_jogador, case=False, na=False)]
    
    resultados = resultados[
        (resultados['age'].between(idade_min, idade_max)) &
        (resultados['overall_rating'].between(overall_min, overall_max)) &
        (resultados['potential'].between(potential_min, potential_max)) &
        (resultados['value'].between(valor_min, valor_max)) &
        (resultados['wage'] <= salario_max)
    ]
    
    if pais != 'any': resultados = resultados[resultados['country_name'] == pais]
    if liga != 'any': resultados = resultados[resultados['club_league_name'] == liga]
    if posicao != 'any': resultados = resultados[resultados['positions'].str.contains(posicao)]

    if not resultados.empty:
        ascending = (sort_order == 'asc')
        if sort_by not in resultados.columns: sort_by = 'overall_rating'
        resultados = resultados.sort_values(by=sort_by, ascending=ascending)
        
        per_page = 20
        total_jogadores = len(resultados)
        total_pages = (total_jogadores + per_page - 1) // per_page
        start, end = (page - 1) * per_page, page * per_page
        jogadores_paginados = resultados.iloc[start:end]
    else:
        jogadores_paginados = pd.DataFrame(); total_pages = 0

    return render_template('resultados.html', jogadores=jogadores_paginados.to_dict('records'), page=page, total_pages=total_pages, sort_by=sort_by, sort_order=sort_order)

@app.route('/player/<int:player_id>')
def player_detail(player_id):
    player_series = df[df['player_id'] == player_id]
    if player_series.empty:
        abort(404)
    player_data = player_series.iloc[0].fillna(0)
    for col in colunas_para_converter:
        if col in player_data:
            player_data[col] = int(player_data[col])
    return render_template('player_detail.html', player=player_data.to_dict(), clubes=CLUBES_UNICOS)

# --- ROTA DE CÁLCULO DE REALISMO v2.1 (RECALIBRADA) ---
@app.route('/calculate_realism', methods=['POST'])
def calculate_realism():
    data = request.get_json()
    player_id = int(data['player_id'])
    target_club_name = data['target_club_name']

    player_data = df[df['player_id'] == player_id].iloc[0]
    target_club_series = df[df['club_name'] == target_club_name]
    
    if target_club_series.empty:
        return jsonify({'error': 'Clube não encontrado ou sem dados de rating.'}), 404

    target_club_data = target_club_series.iloc[0]

    # --- INÍCIO DO MOTOR DE REALISMO v2.1 ---
    
    # Fator 1: Prestígio (Fórmula SUAVIZADA)
    prestige_diff = player_data['overall_rating'] - target_club_data['club_rating']
    # AJUSTE: Divisor aumentado de 2.0 para 3.0 e expoente reduzido de 1.5 para 1.3
    penalty = (np.clip(prestige_diff, 0, 30) / 3.0) ** 1.3
    nota_prestigio = np.clip(10 - penalty, 0, 10)

    # Fator 2: Financeiro (Fórmula RECALIBRADA)
    player_value = player_data['value']
    league_name = target_club_data['club_league_name']
    financial_power = LEAGUE_FINANCIAL_POWER.get(league_name, 5)
    # AJUSTE: Constante de multiplicação diminuída de 5M para 3.5M para aumentar o impacto do valor
    nota_financeira = np.clip(10 - (player_value / (financial_power * 3500000)), 0, 10)
    
    # Fator 3: Potencial vs. Idade (Lógica mantida, pois está boa)
    potential_gap = player_data['potential'] - player_data['overall_rating']
    age_multiplier = max(0, (30 - player_data['age']) / 12) 
    nota_potencial = np.clip(potential_gap / 1.5, 0, 10) * age_multiplier

    # Fator 4: Rivalidade (Lógica mantida)
    fator_rivalidade = 1.0
    player_club = player_data['club_name']
    if player_club in RIVALRIES and target_club_name in RIVALRIES.get(player_club, []):
        fator_rivalidade = 0.1

    # Fator 5: Necessidade do Elenco (Penalidade REDUZIDA)
    fator_necessidade = 1.0
    player_position = player_data['positions'].split(',')[0]
    jogadores_do_clube_alvo_na_posicao = df[
        (df['club_name'] == target_club_name) & 
        (df['positions'].str.contains(player_position)) &
        (df['overall_rating'] >= player_data['overall_rating'])
    ]
    if not jogadores_do_clube_alvo_na_posicao.empty:
        fator_necessidade = 0.85 # AJUSTE: Penalidade agora é de 15% (antes era 30%)

    # --- CÁLCULO FINAL ---
    nota_base = (nota_prestigio * 0.6) + (nota_financeira * 0.3) + (nota_potencial * 0.1)
    nota_final = nota_base * fator_rivalidade * fator_necessidade
    
    return jsonify({
        'realism_score': round(nota_final, 1),
        'breakdown': {
            'Prestígio': round(nota_prestigio, 1),
            'Financeiro': round(nota_financeira, 1),
            'Potencial (x Idade)': round(nota_potencial, 1)
        },
        'comment': f"Penalidade por Rivalidade: -{int((1-fator_rivalidade)*100)}%, Penalidade por Necessidade: -{int((1-fator_necessidade)*100)}%"
    })

if __name__ == '__main__':
    app.run(debug=True)