import streamlit as st
import sqlite3
import pandas as pd

# --- Configuração e Inicialização do Banco de Dados ---
def init_db():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, unit TEXT NOT NULL, default_quantity REAL DEFAULT 1.0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sub_recipes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipe_ingredients (recipe_id INTEGER, product_id INTEGER, quantity REAL, unit TEXT, PRIMARY KEY (recipe_id, product_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipe_sub_recipes (recipe_id INTEGER, sub_recipe_id INTEGER, quantity REAL, PRIMARY KEY (recipe_id, sub_recipe_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sub_recipe_ingredients (sub_recipe_id INTEGER, product_id INTEGER, quantity REAL, unit TEXT, PRIMARY KEY (sub_recipe_id, product_id))''')
    
    # Migrações rápidas
    for table, col, col_type in [('products', 'default_quantity', 'REAL DEFAULT 1.0'), ('recipe_ingredients', 'unit', 'TEXT'), ('sub_recipe_ingredients', 'unit', 'TEXT')]:
        try: cursor.execute(f'SELECT {col} FROM {table} LIMIT 1')
        except sqlite3.OperationalError: cursor.execute(f'ALTER TABLE {table} ADD COLUMN {col} {col_type}')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('recipes.db')
    conn.row_factory = sqlite3.Row
    return conn

def run_query(query, params=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        st.error(f'Erro: {e}')
        return False
    finally: conn.close()

def get_all(table):
    conn = get_db_connection()
    df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
    conn.close()
    return df

def format_br(value):
    try: return "{:,.2f}".format(float(value)).replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "0,00"

UNITS = ['kg', 'g', 'L', 'ml', 'un', 'pct', 'cx','cda']

st.set_page_config(page_title='Gestor de Receitas', layout='wide')
st.title('🍳 Gestão de Receitas e Custos')

tabs = st.tabs(['🔍 Ficha Técnica', '📝 Montar Receita', '🍲 Sub-Receitas', '📦 Produtos'])

# --- ABA PRODUTOS ---
with tabs[3]:
    st.header('📦 Produtos')
    prods = get_all('products')
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader('Cadastrar/Editar')
        mode = st.radio('Ação', ['Novo', 'Editar'], horizontal=True)
        current_p = None
        if mode == 'Editar' and not prods.empty:
            target_name = st.selectbox('Selecionar Produto', prods['name'])
            current_p = prods[prods['name'] == target_name].iloc[0]
        
        with st.form('f_prod'):
            name = st.text_input('Nome', value=current_p['name'] if current_p is not None else "")
            q = st.number_input('Qtd Base', value=float(current_p['default_quantity']) if current_p is not None else 1.0)
            u = st.selectbox('Unidade', UNITS, index=UNITS.index(current_p['unit']) if current_p is not None else 0)
            if st.form_submit_button('Salvar'):
                if mode == 'Novo': run_query('INSERT INTO products (name, unit, default_quantity) VALUES (?,?,?)', (name, u, q))
                else: run_query('UPDATE products SET name=?, unit=?, default_quantity=? WHERE id=?', (name, u, q, int(current_p['id'])))
                st.rerun()

# --- ABA SUB-RECEITAS ---
with tabs[2]:
    st.header('🍲 Sub-Receitas')
    srs = get_all('sub_recipes')
    c_s1, c_s2 = st.columns([1, 2])
    with c_s1:
        st.subheader('Nova Sub-Receita')
        with st.form('new_sr'):
            ns = st.text_input('Nome')
            if st.form_submit_button('Criar'):
                run_query('INSERT INTO sub_recipes (name) VALUES (?)', (ns,))
                st.rerun()
    if not srs.empty:
        sel_sr = st.selectbox('Selecionar Sub-Receita para editar itens:', srs['id'], format_func=lambda x: srs[srs['id']==x]['name'].values[0])
        p_list = get_all('products')
        with st.form('add_item_sr'):
            p_sel = st.selectbox('Ingrediente', p_list['name'])
            sq = st.number_input('Qtd', min_value=0.0)
            su = st.selectbox('Unidade', UNITS)
            if st.form_submit_button('Vincular'):
                pid = int(p_list[p_list['name']==p_sel]['id'].values[0])
                run_query('INSERT OR REPLACE INTO sub_recipe_ingredients (sub_recipe_id, product_id, quantity, unit) VALUES (?,?,?,?)', (int(sel_sr), pid, sq, su))
                st.rerun()

# --- ABA MONTAR RECEITA ---
with tabs[1]:
    st.header('📝 Montagem de Receita Final')
    recs = get_all('recipes')
    c_r1, c_r2 = st.columns([1, 2])
    with c_r1:
        st.subheader('Nova Receita')
        with st.form('new_rec'):
            nr = st.text_input('Nome da Receita')
            if st.form_submit_button('Criar'):
                run_query('INSERT INTO recipes (name) VALUES (?)', (nr,))
                st.rerun()
    if not recs.empty:
        rid = st.selectbox('Selecione para configurar itens:', recs['id'], format_func=lambda x: recs[recs['id']==x]['name'].values[0])
        col_a, col_b = st.columns(2)
        with col_a:
            st.write('Add Ingrediente')
            pl = get_all('products')
            with st.form('ri'):
                p_ri = st.selectbox('Produto', pl['name'])
                q_ri = st.number_input('Qtd', key='qri')
                u_ri = st.selectbox('Unidade', UNITS, key='uri')
                if st.form_submit_button('Vincular Ingrediente'):
                    pid = int(pl[pl['name']==p_ri]['id'].values[0])
                    run_query('INSERT OR REPLACE INTO recipe_ingredients (recipe_id, product_id, quantity, unit) VALUES (?,?,?,?)', (int(rid), pid, q_ri, u_ri))
                    st.rerun()
        with col_b:
            st.write('Add Sub-Receita')
            sl = get_all('sub_recipes')
            with st.form('rsr'):
                s_sel = st.selectbox('Sub-Receita', sl['name'])
                sq_rsr = st.number_input('Qtd Porções')
                if st.form_submit_button('Vincular Sub-Receita'):
                    sid = int(sl[sl['name']==s_sel]['id'].values[0])
                    run_query('INSERT OR REPLACE INTO recipe_sub_recipes (recipe_id, sub_recipe_id, quantity) VALUES (?,?,?)', (int(rid), sid, sq_rsr))
                    st.rerun()

# --- ABA VISUALIZAR ---
with tabs[0]:
    st.header('🔍 Ficha Técnica')
    rv = get_all('recipes')
    if not rv.empty:
        tid = st.selectbox('Ver Ficha:', rv['id'], format_func=lambda x: rv[rv['id']==x]['name'].values[0])
        conn = get_db_connection()
        ing = pd.read_sql_query('SELECT p.name as Item, ri.quantity as Qtd, ri.unit as Und FROM recipe_ingredients ri JOIN products p ON ri.product_id = p.id WHERE ri.recipe_id = ?', conn, params=(int(tid),))
        sub = pd.read_sql_query('SELECT sr.name as Sub, rsr.quantity as Qtd, sr.id FROM recipe_sub_recipes rsr JOIN sub_recipes sr ON rsr.sub_recipe_id = sr.id WHERE rsr.recipe_id = ?', conn, params=(int(tid),))
        conn.close()
        st.subheader('Ingredientes Diretos')
        st.table(ing) if not ing.empty else st.info('Sem ingredientes.')
        st.subheader('Sub-Receitas')
        for _, r in sub.iterrows():
            with st.expander(f"{r['Sub']} ({r['Qtd']} un)"):
                conn = get_db_connection()
                details = pd.read_sql_query('SELECT p.name as Item, sri.quantity as Qtd, sri.unit as Und FROM sub_recipe_ingredients sri JOIN products p ON sri.product_id = p.id WHERE sri.sub_recipe_id = ?', conn, params=(int(r['id']),))
                conn.close()
                st.table(details)
    else: st.warning('Nenhuma receita cadastrada.')
