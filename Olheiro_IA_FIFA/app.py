from flask import Flask, render_template, request, session, redirect, url_for, abort
import pandas as pd
import os

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

# --- CARREGAMENTO E PREPARAÇÃO ---
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
    'interceptions', 'positioning', 'vision', 'penalties', 'defensive_awareness', 'standing_tackle', 'sliding_tackle'
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

POSICOES_UNICAS = sorted(list(set(','.join(df['positions'].dropna().unique()).split(','))))
PAISES_UNICOS = sorted(df['country_name'].dropna().unique())
LIGAS_UNICAS = sorted(df['club_league_name'].dropna().unique())
print("Aplicação pronta.")


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


# --- SUBSTITUA A SUA FUNÇÃO 'player_detail' POR ESTA ---
@app.route('/player/<int:player_id>')
def player_detail(player_id):
    print("\n--- INICIANDO DIAGNÓSTICO DA PÁGINA DE DETALHES ---")
    print(f"Buscando jogador com ID: {player_id}")

    # 1. Achar o jogador no DataFrame original
    player_series = df[df['player_id'] == player_id]
    if player_series.empty:
        print("ERRO DE DIAGNÓSTICO: Jogador não encontrado no DataFrame. Abortando.")
        abort(404)
    
    player_data = player_series.iloc[0]
    print("\n--- PASSO 1: DADOS BRUTOS DO JOGADOR (DA LINHA DO DF) ---")
    # Vamos inspecionar algumas colunas de stats e seus tipos
    stats_para_checar = ['finishing', 'dribbling', 'strength', 'overall_rating']
    for stat in stats_para_checar:
        if stat in player_data:
            print(f"Coluna '{stat}': Valor = '{player_data[stat]}', Tipo = {type(player_data[stat])}")
        else:
            print(f"Coluna '{stat}' não encontrada.")

    # 2. Tentar preencher valores nulos
    try:
        player_data_filled = player_data.fillna(0)
        print("\n--- PASSO 2: DADOS APÓS APLICAR .fillna(0) ---")
        print(player_data_filled[stats_para_checar])
    except Exception as e:
        print(f"!!! ERRO no PASSO 2 (.fillna): {e} !!!")
        # Se falhar aqui, não podemos continuar
        return "Erro durante o passo de fillna. Verifique o terminal."

    # 3. Tentar converter para dicionário e enviar
    try:
        player_dict = player_data_filled.to_dict()
        print("\n--- PASSO 3: DADOS FINAIS (DICIONÁRIO ENVIADO PARA O HTML) ---")
        print("Valores para as stats que estamos checando:")
        for stat in stats_para_checar:
            print(f"'{stat}': {player_dict.get(stat)}")

        print("\n--- FIM DO DIAGNÓSTICO. Tentando renderizar o template... ---")
        return render_template('player_detail.html', player=player_dict)

    except Exception as e:
        print(f"!!! ERRO no PASSO 3 (.to_dict ou render_template): {e} !!!")
        return "Erro final antes de renderizar. Verifique o terminal."

if __name__ == '__main__':
    app.run(debug=True)