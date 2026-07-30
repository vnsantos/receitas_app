import streamlit as st
import sqlite3
import pandas as pd

# --- Configuração e Inicialização do Banco de Dados ---
def init_db():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, unit TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sub_recipes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipe_ingredients (recipe_id INTEGER, product_id INTEGER, quantity REAL, PRIMARY KEY (recipe_id, product_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipe_sub_recipes (recipe_id INTEGER, sub_recipe_id INTEGER, quantity REAL, PRIMARY KEY (recipe_id, sub_recipe_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sub_recipe_ingredients (sub_recipe_id INTEGER, product_id INTEGER, quantity REAL, PRIMARY KEY (sub_recipe_id, product_id))''')
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
        return True, 'Sucesso!'
    except Exception as e: return False, str(e)
    finally: conn.close()

def get_all(table): 
    conn = get_db_connection()
    df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
    conn.close()
    return df

# --- Interface Streamlit ---
st.set_page_config(page_title='Gestor de Receitas', layout='wide')
st.title('🍳 Gestão de Receitas e Custos')

tabs = st.tabs(['🔍 Visualizar Receitas', '📝 Montar Receita', '🍲 Gerenciar Sub-Receitas', '📦 Produtos'])

with tabs[3]:
    st.header('📦 Cadastro de Produtos')
    with st.form('f_prod'):
        n = st.text_input('Nome')
        u = st.text_input('Unidade (kg, g, un)')
        if st.form_submit_button('Salvar'):
            run_query('INSERT INTO products (name, unit) VALUES (?, ?)', (n, u))
            st.rerun()
    st.dataframe(get_all('products'), use_container_width=True)

with tabs[2]:
    st.header('🍲 Gerenciar Sub-Receitas')
    with st.expander('Nova Sub-Receita'):
        nsr = st.text_input('Nome da Sub-Receita')
        if st.button('Criar Sub-Receita'):
            run_query('INSERT INTO sub_recipes (name) VALUES (?)', (nsr,))
            st.rerun()
    
    srs = get_all('sub_recipes')
    if not srs.empty:
        sel_sr = st.selectbox('Selecione Sub-Receita para editar itens:', srs['id'], format_func=lambda x: srs[srs['id']==x]['name'].values[0])
        col_sr1, col_sr2 = st.columns(2)
        with col_sr1:
            ps = get_all('products')
            p_sel = st.selectbox('Produto para Sub-Receita', ps['name'] if not ps.empty else [])
            p_q = st.number_input('Qtd Produto', min_value=0.0, key='sr_pq')
            if st.button('Adicionar à Sub-Receita'):
                pid = ps[ps['name']==p_sel]['id'].values[0]
                run_query('INSERT OR REPLACE INTO sub_recipe_ingredients VALUES (?, ?, ?)', (sel_sr, pid, p_q))
        with col_sr2:
            conn = get_db_connection()
            items_sr = pd.read_sql_query('SELECT p.name, sri.quantity FROM sub_recipe_ingredients sri JOIN products p ON sri.product_id = p.id WHERE sri.sub_recipe_id = ?', conn, params=(sel_sr,))
            conn.close()
            st.write('Itens atuais da Sub-Receita:')
            st.table(items_sr)

with tabs[1]:
    st.header('📝 Montagem de Receita Final')
    with st.expander('Nova Receita Final'):
        nr = st.text_input('Nome da Receita Final')
        if st.button('Criar Receita'):
            run_query('INSERT INTO recipes (name) VALUES (?)', (nr,))
            st.rerun()
    
    recs = get_all('recipes')
    if not recs.empty:
        rid = st.selectbox('Selecione a receita:', recs['id'], format_func=lambda x: recs[recs['id']==x]['name'].values[0])
        c1, c2 = st.columns(2)
        with c1:
            st.write('**Adicionar Produto Direto**')
            ps = get_all('products')
            p_name = st.selectbox('Produto', ps['name'] if not ps.empty else [])
            pq = st.number_input('Qtd', min_value=0.0, key='rpq')
            if st.button('Vincular Produto'):
                pid = ps[ps['name']==p_name]['id'].values[0]
                run_query('INSERT OR REPLACE INTO recipe_ingredients VALUES (?, ?, ?)', (rid, pid, pq))
        with c2:
            st.write('**Adicionar Sub-Receita**')
            srs_list = get_all('sub_recipes')
            sr_name = st.selectbox('Sub-Receita', srs_list['name'] if not srs_list.empty else [])
            sq = st.number_input('Qtd', min_value=0.0, key='rsq')
            if st.button('Vincular Sub-Receita'):
                sid = srs_list[srs_list['name']==sr_name]['id'].values[0]
                run_query('INSERT OR REPLACE INTO recipe_sub_recipes VALUES (?, ?, ?)', (rid, sid, sq))

with tabs[0]:
    st.header('🔍 Ficha Técnica Detalhada')
    recs_v = get_all('recipes')
    if not recs_v.empty:
        target = st.selectbox('Abrir Receita:', recs_v['id'], format_func=lambda x: recs_v[recs_v['id']==x]['name'].values[0])
        conn = get_db_connection()
        prods_final = pd.read_sql_query('SELECT p.name as Item, ri.quantity as Qtd, p.unit as Unidade FROM recipe_ingredients ri JOIN products p ON ri.product_id = p.id WHERE ri.recipe_id = ?', conn, params=(target,))
        subs_final = pd.read_sql_query('SELECT sr.name as SubReceita, rsr.quantity as Qtd FROM recipe_sub_recipes rsr JOIN sub_recipes sr ON rsr.sub_recipe_id = sr.id WHERE rsr.recipe_id = ?', conn, params=(target,))
        conn.close()
        
        st.subheader('Itens Diretos')
        st.table(prods_final) if not prods_final.empty else st.info('Sem itens diretos.')
        
        st.subheader('Sub-Receitas Vinculadas')
        if not subs_final.empty:
            for index, row in subs_final.iterrows():
                with st.expander(f"{row['SubReceita']} (Qtd: {row['Qtd']})"):
                    conn = get_db_connection()
                    # Busca ID da sub-receita pelo nome
                    sid = conn.execute('SELECT id FROM sub_recipes WHERE name = ?', (row['SubReceita'],)).fetchone()[0]
                    items_in_sr = pd.read_sql_query('SELECT p.name as Componente, sri.quantity as Qtd, p.unit FROM sub_recipe_ingredients sri JOIN products p ON sri.product_id = p.id WHERE sri.sub_recipe_id = ?', conn, params=(sid,))
                    conn.close()
                    st.table(items_in_sr) if not items_in_sr.empty else st.write('Esta sub-receita não possui itens cadastrados.')
        else: st.info('Sem sub-receitas vinculadas.')
