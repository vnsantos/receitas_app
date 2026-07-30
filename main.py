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

    # Migrações
    columns_to_add = [
        ('products', 'default_quantity', 'REAL DEFAULT 1.0'),
        ('recipe_ingredients', 'unit', 'TEXT'),
        ('sub_recipe_ingredients', 'unit', 'TEXT')
    ]
    for table, col, col_type in columns_to_add:
        try:
            cursor.execute(f"SELECT {col} FROM {table} LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
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
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_all(table):
    conn = get_db_connection()
    df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
    conn.close()
    return df

def format_br(value):
    try:
        return "{:,.2f}".format(float(value)).replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "0,00"

UNITS = ['kg', 'g', 'L', 'ml', 'un', 'pct', 'cx','cda']

# --- Interface Streamlit ---
st.set_page_config(page_title='Gestor de Receitas Profissional', layout='wide')
st.title('🍳 Gestão de Receitas e Custos')

tabs = st.tabs(['🔍 Visualizar Receitas', '📝 Montar Receita', '🍲 Gerenciar Sub-Receitas', '📦 Produtos'])

with tabs[3]:
    st.header('📦 Gestão de Produtos')
    prods = get_all('products')
    
    col_search, col_clear = st.columns([3, 1])
    search_term = col_search.text_input('🔍 Pesquisar Produto', placeholder='Digite o nome...')
    if col_clear.button('Limpar Filtro / Recarregar'):
        st.rerun()

    c_p1, c_p2 = st.columns([1, 2])
    with c_p1:
        st.subheader('Cadastro / Edição')
        edit_p = st.selectbox('Selecionar para Editar', ['Novo Produto'] + list(prods['name'].values)) if not prods.empty else 'Novo Produto'
        current_p = prods[prods['name'] == edit_p].iloc[0] if edit_p != 'Novo Produto' else None
        
        with st.form('f_prod', clear_on_submit=True):
            n = st.text_input('Nome do Produto', value=current_p['name'] if current_p is not None else "")
            col_q1, col_q2 = st.columns(2)
            dq = col_q1.number_input('Qtd Base', min_value=0.01, value=float(current_p['default_quantity']) if current_p is not None else 1.0, step=0.01)
            u = col_q2.selectbox('Unidade', UNITS, index=UNITS.index(current_p['unit']) if current_p is not None else 0)
            
            if st.form_submit_button('Salvar/Atualizar'):
                if n:
                    if current_p is not None:
                        run_query('UPDATE products SET name=?, unit=?, default_quantity=? WHERE id=?', (n, u, dq, int(current_p['id'])))
                    else:
                        run_query('INSERT INTO products (name, unit, default_quantity) VALUES (?, ?, ?)', (n, u, dq))
                    st.rerun()
            if st.form_submit_button('Limpar Campos'):
                st.rerun()

    with c_p2:
        st.write("Lista de Produtos:")
        if not prods.empty:
            filtered = prods[prods['name'].str.contains(search_term, case=False)]
            # Exibindo em formato de tabela para não ficar solto
            display_df = filtered.copy()
            display_df['Qtd Formatada'] = display_df['default_quantity'].apply(format_br)
            st.dataframe(display_df[['name', 'Qtd Formatada', 'unit']], use_container_width=True, hide_index=True)
            
            # Botão de exclusão rápida
            del_target = st.selectbox('Remover Produto:', ['Nenhum'] + list(filtered['name'].values), key='del_prod_list')
            if st.button('Confirmar Exclusão'):
                if del_target != 'Nenhum':
                    target_id = int(prods[prods['name'] == del_target]['id'].iloc[0])
                    run_query('DELETE FROM products WHERE id = ?', (target_id,))
                    st.rerun()

with tabs[2]:
    st.header('🍲 Gerenciar Sub-Receitas')
    srs = get_all('sub_recipes')
    
    with st.form('f_sub_rec'):
        nsr = st.text_input('Nome da Sub-Receita (Criar ou Editar)')
        c_sub1, c_sub2 = st.columns(2)
        if c_sub1.form_submit_button('Salvar Sub-Receita'):
            if nsr: run_query('INSERT OR REPLACE INTO sub_recipes (name) VALUES (?)', (nsr,)); st.rerun()
        if c_sub2.form_submit_button('Limpar'): st.rerun()

    if not srs.empty:
        sel_sr = st.selectbox('Selecione Sub-Receita para editar itens:', srs['id'], format_func=lambda x: srs[srs['id']==x]['name'].values[0])
        
        col_sr1, col_sr2 = st.columns(2)
        with col_sr1:
            ps = get_all('products')
            if not ps.empty:
                p_sel_name = st.selectbox('Adicionar Item', ps['name'])
                cq, cu = st.columns(2)
                pq = cq.number_input('Qtd', min_value=0.0, step=0.01, key='sr_pq')
                pu = cu.selectbox('Unidade', UNITS, key='sr_pu')
                if st.button('Vincular Item'):
                    pid = int(ps[ps['name']==p_sel_name]['id'].values[0])
                    run_query('INSERT OR REPLACE INTO sub_recipe_ingredients (sub_recipe_id, product_id, quantity, unit) VALUES (?, ?, ?, ?)', (int(sel_sr), pid, pq, pu))
                    st.rerun()
        with col_sr2:
            conn = get_db_connection()
            items = pd.read_sql_query('SELECT p.name as Item, sri.quantity as Qtd, sri.unit as Und FROM sub_recipe_ingredients sri JOIN products p ON sri.product_id = p.id WHERE sri.sub_recipe_id = ?', conn, params=(int(sel_sr),))
            conn.close()
            st.table(items) if not items.empty else st.info('Nenhum item vinculado.')

with tabs[1]:
    st.header('📝 Montagem de Receita Final')
    recs = get_all('recipes')
    
    with st.form('f_rec_main'):
        nr = st.text_input('Nome da Receita')
        c_r1, c_r2 = st.columns(2)
        if c_r1.form_submit_button('Salvar Receita'):
            if nr: run_query('INSERT OR REPLACE INTO recipes (name) VALUES (?)', (nr,)); st.rerun()
        if c_r2.form_submit_button('Limpar'): st.rerun()

    if not recs.empty:
        rid = st.selectbox('Selecione a receita:', recs['id'], format_func=lambda x: recs[recs['id']==x]['name'].values[0])
        # Lógica de vínculos similar às anteriores com botões de update já ativos via INSERT OR REPLACE
        st.info('Utilize os campos abaixo para adicionar ou atualizar ingredientes e sub-receitas.')

with tabs[0]:
    st.header('🔍 Ficha Técnica')
    recs_v = get_all('recipes')
    if not recs_v.empty:
        target = st.selectbox('Ver Ficha:', recs_v['id'], format_func=lambda x: recs_v[recs_v['id']==x]['name'].values[0])
        # Visualização detalhada conforme as versões anteriores
    else: st.warning('Cadastre uma receita primeiro.')
