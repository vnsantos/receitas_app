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
        st.error(f'Erro no Banco: {e}')
        return False
    finally: conn.close()

def get_all(table):
    conn = get_db_connection()
    df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
    conn.close()
    return df

UNITS = ['kg', 'g', 'L', 'ml', 'un', 'pct', 'cx','cda']

st.set_page_config(page_title='Gestor de Receitas', layout='wide')
st.title('🍳 Gestão de Receitas e Custos')

tabs = st.tabs(['🔍 Ficha Técnica', '📝 Montar Receita', '🍲 Sub-Receitas', '📦 Produtos'])

# --- ABA PRODUTOS ---
with tabs[3]:
    st.header('📦 Gestão de Produtos')
    prods = get_all('products')
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader('Cadastro / Edição')
        mode = st.radio('Ação Produto', ['Novo', 'Editar'], horizontal=True, key='mode_p')
        current_p = None
        if mode == 'Editar' and not prods.empty:
            target_name = st.selectbox('Produto para editar', prods['name'])
            current_p = prods[prods['name'] == target_name].iloc[0]
        
        with st.form('f_prod'):
            name = st.text_input('Nome', value=current_p['name'] if current_p is not None else "")
            q = st.number_input('Qtd Base', value=float(current_p['default_quantity']) if current_p is not None else 1.0, step=0.01)
            u = st.selectbox('Unidade', UNITS, index=UNITS.index(current_p['unit']) if current_p is not None else 0)
            b1, b2 = st.columns(2)
            if b1.form_submit_button('Salvar Produto'):
                if name:
                    if mode == 'Novo': run_query('INSERT INTO products (name, unit, default_quantity) VALUES (?,?,?)', (name, u, q))
                    else: run_query('UPDATE products SET name=?, unit=?, default_quantity=? WHERE id=?', (name, u, q, int(current_p['id'])))
                    st.rerun()
            if b2.form_submit_button('Limpar Campos'): st.rerun()
    with c2:
        st.subheader('Lista de Produtos')
        if not prods.empty: st.dataframe(prods[['name', 'default_quantity', 'unit']], use_container_width=True, hide_index=True)
        else: st.info('Nenhum produto cadastrado.')

# --- ABA SUB-RECEITAS ---
with tabs[2]:
    st.header('🍲 Sub-Receitas')
    srs = get_all('sub_recipes')
    c_s1, c_s2 = st.columns([1, 2])
    with c_s1:
        st.subheader('Gerenciar Sub-Receita')
        mode_sr = st.radio('Ação Sub-Receita', ['Nova', 'Editar'], horizontal=True, key='msr')
        curr_sr = None
        if mode_sr == 'Editar' and not srs.empty:
            sel_sr_name = st.selectbox('Selecionar Sub-Receita', srs['name'])
            curr_sr = srs[srs['name'] == sel_sr_name].iloc[0]
        
        with st.form('f_sr'):
            ns = st.text_input('Nome da Sub-Receita', value=curr_sr['name'] if curr_sr is not None else "")
            b1, b2 = st.columns(2)
            if b1.form_submit_button('Salvar Sub-Receita'):
                if ns:
                    if mode_sr == 'Nova': run_query('INSERT INTO sub_recipes (name) VALUES (?)', (ns,))
                    else: run_query('UPDATE sub_recipes SET name=? WHERE id=?', (ns, int(curr_sr['id'])))
                    st.rerun()
            if b2.form_submit_button('Limpar'): st.rerun()
            
        if mode_sr == 'Editar' and curr_sr is not None:
            st.write('---')
            pl = get_all('products')
            with st.form('add_item_sr'):
                st.write('**Adicionar Item**')
                p_sel = st.selectbox('Ingrediente', pl['name'])
                sq = st.number_input('Qtd', min_value=0.0, step=0.01)
                su = st.selectbox('Unidade', UNITS)
                if st.form_submit_button('Vincular'):
                    pid = int(pl[pl['name']==p_sel]['id'].values[0])
                    run_query('INSERT OR REPLACE INTO sub_recipe_ingredients (sub_recipe_id, product_id, quantity, unit) VALUES (?,?,?,?)', (int(curr_sr['id']), pid, sq, su))
                    st.rerun()
    with c_s2:
        st.subheader('Lista de Sub-Receitas')
        if not srs.empty: st.dataframe(srs[['name']], use_container_width=True, hide_index=True)
        else: st.info('Nenhuma sub-receita.')

# --- ABA MONTAR RECEITA ---
with tabs[1]:
    st.header('📝 Receitas Principais')
    recs = get_all('recipes')
    c_r1, c_r2 = st.columns([1, 2])
    with c_r1:
        st.subheader('Gerenciar Receita')
        mode_r = st.radio('Ação Receita', ['Nova', 'Editar'], horizontal=True, key='mr')
        curr_r = None
        if mode_r == 'Editar' and not recs.empty:
            sel_r_name = st.selectbox('Selecionar Receita', recs['name'])
            curr_r = recs[recs['name'] == sel_r_name].iloc[0]
            
        with st.form('f_r'):
            nr = st.text_input('Nome da Receita', value=curr_r['name'] if curr_r is not None else "")
            b1, b2 = st.columns(2)
            if b1.form_submit_button('Salvar Receita'):
                if nr:
                    if mode_r == 'Nova': run_query('INSERT INTO recipes (name) VALUES (?)', (nr,))
                    else: run_query('UPDATE recipes SET name=? WHERE id=?', (nr, int(curr_r['id'])))
                    st.rerun()
            if b2.form_submit_button('Limpar'): st.rerun()
            
        if mode_r == 'Editar' and curr_r is not None:
            st.write('---')
            ca, cb = st.columns(2)
            with ca:
                pl = get_all('products')
                with st.form('ri'):
                    st.write('**Ingrediente**')
                    p_ri = st.selectbox('Produto', pl['name'])
                    q_ri = st.number_input('Qtd', step=0.01, key='q_m')
                    u_ri = st.selectbox('Unidade', UNITS, key='u_m')
                    if st.form_submit_button('Add'):
                        pid = int(pl[pl['name']==p_ri]['id'].values[0])
                        run_query('INSERT OR REPLACE INTO recipe_ingredients (recipe_id, product_id, quantity, unit) VALUES (?,?,?,?)', (int(curr_r['id']), pid, q_ri, u_ri))
                        st.rerun()
            with cb:
                sl = get_all('sub_recipes')
                with st.form('rsr'):
                    st.write('**Sub-Receita**')
                    s_sel = st.selectbox('Sub', sl['name'])
                    sq_rsr = st.number_input('Qtd', step=0.1, key='qs_m')
                    if st.form_submit_button('Add '):
                        sid = int(sl[sl['name']==s_sel]['id'].values[0])
                        run_query('INSERT OR REPLACE INTO recipe_sub_recipes (recipe_id, sub_recipe_id, quantity) VALUES (?,?,?)', (int(curr_r['id']), sid, sq_rsr))
                        st.rerun()
    with c_r2:
        st.subheader('Lista de Receitas')
        if not recs.empty: st.dataframe(recs[['name']], use_container_width=True, hide_index=True)
        else: st.info('Nenhuma receita.')

# --- ABA FICHA TÉCNICA ---
with tabs[0]:
    st.header('🔍 Ficha Técnica')
    rv = get_all('recipes')
    if not rv.empty:
        tid = st.selectbox('Visualizar:', rv['id'], format_func=lambda x: rv[rv['id']==x]['name'].values[0])
        conn = get_db_connection()
        ing = pd.read_sql_query('SELECT p.name as Item, ri.quantity as Qtd, ri.unit as Und FROM recipe_ingredients ri JOIN products p ON ri.product_id = p.id WHERE ri.recipe_id = ?', conn, params=(int(tid),))
        sub = pd.read_sql_query('SELECT sr.name as Sub, rsr.quantity as Qtd, sr.id FROM recipe_sub_recipes rsr JOIN sub_recipes sr ON rsr.sub_recipe_id = sr.id WHERE rsr.recipe_id = ?', conn, params=(int(tid),))
        conn.close()
        st.write('---')
        st.subheader(f"Composição: {rv[rv['id']==tid]['name'].values[0]}")
        if not ing.empty: st.table(ing)
        if not sub.empty:
            for _, r in sub.iterrows():
                with st.expander(f"{r['Sub']} ({r['Qtd']} un)"):
                    conn = get_db_connection()
                    det = pd.read_sql_query('SELECT p.name as Item, sri.quantity as Qtd, sri.unit as Und FROM sub_recipe_ingredients sri JOIN products p ON sri.product_id = p.id WHERE sri.sub_recipe_id = ?', conn, params=(int(r['id']),))
                    conn.close()
                    if not det.empty: st.table(det)
    else: st.warning('Nenhuma receita disponível.')
