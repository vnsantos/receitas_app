import streamlit as st
import sqlite3
import pandas as pd

# --- Configuração e Inicialização do Banco de Dados ---
def init_db():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    
    # Criação das tabelas base
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, unit TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sub_recipes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipe_ingredients (recipe_id INTEGER, product_id INTEGER, quantity REAL, unit TEXT, PRIMARY KEY (recipe_id, product_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipe_sub_recipes (recipe_id INTEGER, sub_recipe_id INTEGER, quantity REAL, PRIMARY KEY (recipe_id, sub_recipe_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sub_recipe_ingredients (sub_recipe_id INTEGER, product_id INTEGER, quantity REAL, unit TEXT, PRIMARY KEY (sub_recipe_id, product_id))''')

    # MIRAÇÕES: Garantir que colunas novas existam em bancos antigos
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
    except:
        return "0,00"

UNITS = ['kg', 'g', 'L', 'ml', 'un', 'pct', 'cx','cda']

# --- Interface Streamlit ---
st.set_page_config(page_title='Gestor de Receitas Profissional', layout='wide')
st.title('🍳 Gestão de Receitas e Custos')

tabs = st.tabs(['🔍 Visualizar Receitas', '📝 Montar Receita', '🍲 Gerenciar Sub-Receitas', '📦 Produtos'])

with tabs[3]:
    st.header('📦 Cadastro de Produtos')
    c_p1, c_p2 = st.columns([1, 2])
    with c_p1:
        with st.form('f_prod', clear_on_submit=True):
            n = st.text_input('Nome do Produto')
            col_q1, col_q2 = st.columns(2)
            dq = col_q1.number_input('Qtd Base', min_value=0.01, value=1.0, step=0.01, format="%.2f")
            u = col_q2.selectbox('Unidade', UNITS)
            if st.form_submit_button('Salvar'):
                if n:
                    run_query('INSERT INTO products (name, unit, default_quantity) VALUES (?, ?, ?)', (n, u, dq))
                    st.rerun()

    with c_p2:
        prods = get_all('products')
        if not prods.empty:
            st.write("Produtos Cadastrados:")
            for _, p_row in prods.iterrows():
                col_a, col_b = st.columns([3, 1])
                # Uso de .get() ou verificação para evitar KeyError
                p_qty = p_row['default_quantity'] if 'default_quantity' in p_row else 1.0
                p_unit = p_row['unit'] if 'unit' in p_row else 'un'
                txt = f"{p_row['name']} - {format_br(p_qty)} {p_unit}"
                col_a.write(txt)
                if col_b.button('Excluir', key=f"del_p_{p_row['id']}"):
                    run_query('DELETE FROM products WHERE id = ?', (int(p_row['id']),))
                    run_query('DELETE FROM recipe_ingredients WHERE product_id = ?', (int(p_row['id']),))
                    run_query('DELETE FROM sub_recipe_ingredients WHERE product_id = ?', (int(p_row['id']),))
                    st.rerun()

with tabs[2]:
    st.header('🍲 Gerenciar Sub-Receitas')
    with st.expander('Nova Sub-Receita'):
        nsr = st.text_input('Nome da Sub-Receita')
        if st.button('Criar Sub-Receita'):
            if nsr:
                run_query('INSERT INTO sub_recipes (name) VALUES (?)', (nsr,))
                st.rerun()

    srs = get_all('sub_recipes')
    if not srs.empty:
        col_sr_sel, col_sr_del = st.columns([3, 1])
        sel_sr = col_sr_sel.selectbox('Selecione Sub-Receita:', srs['id'], format_func=lambda x: srs[srs['id']==x]['name'].values[0])
        if col_sr_del.button('Excluir Sub-Receita Total'):
            run_query('DELETE FROM sub_recipes WHERE id = ?', (int(sel_sr),))
            st.rerun()

        col_sr1, col_sr2 = st.columns(2)
        with col_sr1:
            ps = get_all('products')
            if not ps.empty:
                p_sel_name = st.selectbox('Produto para Sub-Receita', ps['name'])
                c_q, c_u = st.columns(2)
                p_q = c_q.number_input('Qtd', min_value=0.0, step=0.01, format="%.2f", key='sr_pq')
                p_u_sel = c_u.selectbox('Unidade', UNITS, key='sr_pu')
                if st.button('Adicionar à Sub-Receita'):
                    pid = int(ps[ps['name']==p_sel_name]['id'].values[0])
                    run_query('INSERT OR REPLACE INTO sub_recipe_ingredients (sub_recipe_id, product_id, quantity, unit) VALUES (?, ?, ?, ?)', (int(sel_sr), pid, p_q, p_u_sel))
                    st.success('Item adicionado!')
        with col_sr2:
            conn = get_db_connection()
            items_sr = pd.read_sql_query('SELECT p.id as p_id, p.name as Item, sri.quantity as Qtd, sri.unit as Und FROM sub_recipe_ingredients sri JOIN products p ON sri.product_id = p.id WHERE sri.sub_recipe_id = ?', conn, params=(int(sel_sr),))
            conn.close()
            if not items_sr.empty:
                st.write('Itens atuais:')
                for _, item in items_sr.iterrows():
                    c_item, c_btn = st.columns([3, 1])
                    c_item.write(f"{item['Item']} - {format_br(item['Qtd'])} {item['Und']}")
                    if c_btn.button('Remover', key=f"rsr_{item['p_id']}"):
                        run_query('DELETE FROM sub_recipe_ingredients WHERE sub_recipe_id = ? AND product_id = ?', (int(sel_sr), int(item['p_id'])))
                        st.rerun()

with tabs[1]:
    st.header('📝 Montagem de Receita Final')
    with st.expander('Nova Receita Final'):
        nr = st.text_input('Nome da Receita Final')
        if st.button('Criar Receita'):
            if nr:
                run_query('INSERT INTO recipes (name) VALUES (?)', (nr,))
                st.rerun()

    recs = get_all('recipes')
    if not recs.empty:
        col_r_sel, col_r_del = st.columns([3, 1])
        rid = col_r_sel.selectbox('Selecione a receita:', recs['id'], format_func=lambda x: recs[recs['id']==x]['name'].values[0])
        if col_r_del.button('Excluir Receita Total'):
            run_query('DELETE FROM recipes WHERE id = ?', (int(rid),))
            st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            st.write('**Produtos Diretos**')
            ps = get_all('products')
            if not ps.empty:
                p_name_rec = st.selectbox('Produto', ps['name'], key='sel_p_rec')
                c_rq, c_ru = st.columns(2)
                pq = c_rq.number_input('Qtd', min_value=0.0, step=0.01, format="%.2f", key='rpq')
                ru = c_ru.selectbox('Unidade', UNITS, key='rpu')
                if st.button('Vincular Produto'):
                    pid_rec = int(ps[ps['name']==p_name_rec]['id'].values[0])
                    run_query('INSERT OR REPLACE INTO recipe_ingredients (recipe_id, product_id, quantity, unit) VALUES (?, ?, ?, ?)', (int(rid), pid_rec, pq, ru))
                    st.rerun()
        with c2:
            st.write('**Sub-Receitas**')
            srs_list = get_all('sub_recipes')
            if not srs_list.empty:
                sr_name_rec = st.selectbox('Sub-Receita', srs_list['name'])
                sq = st.number_input('Qtd de Porções', min_value=0.0, step=0.01, format="%.2f", key='rsq')
                if st.button('Vincular Sub-Receita'):
                    sid_rec = int(srs_list[srs_list['name']==sr_name_rec]['id'].values[0])
                    run_query('INSERT OR REPLACE INTO recipe_sub_recipes (recipe_id, sub_recipe_id, quantity) VALUES (?, ?, ?)', (int(rid), sid_rec, sq))
                    st.rerun()

with tabs[0]:
    st.header('🔍 Ficha Técnica Detalhada')
    recs_v = get_all('recipes')
    if not recs_v.empty:
        target = st.selectbox('Abrir Receita:', recs_v['id'], format_func=lambda x: recs_v[recs_v['id']==x]['name'].values[0])
        conn = get_db_connection()
        prods_final = pd.read_sql_query('SELECT p.name as Item, ri.quantity as Qtd, ri.unit as Unidade FROM recipe_ingredients ri JOIN products p ON ri.product_id = p.id WHERE ri.recipe_id = ?', conn, params=(int(target),))
        subs_final = pd.read_sql_query('SELECT sr.name as SubReceita, rsr.quantity as Qtd, sr.id as sr_id FROM recipe_sub_recipes rsr JOIN sub_recipes sr ON rsr.sub_recipe_id = sr.id WHERE rsr.recipe_id = ?', conn, params=(int(target),))
        conn.close()

        st.subheader('Itens Diretos')
        if not prods_final.empty:
            prods_final['Qtd'] = prods_final['Qtd'].apply(format_br)
            st.table(prods_final)
        else: st.info('Sem itens diretos.')

        st.subheader('Sub-Receitas Vinculadas')
        if not subs_final.empty:
            for _, row in subs_final.iterrows():
                with st.expander(f"{row['SubReceita']} (Qtd: {format_br(row['Qtd'])})"):
                    conn = get_db_connection()
                    items_in_sr = pd.read_sql_query('SELECT p.name as Componente, sri.quantity as Qtd, sri.unit as Und FROM sub_recipe_ingredients sri JOIN products p ON sri.product_id = p.id WHERE sri.sub_recipe_id = ?', conn, params=(int(row['sr_id']),))
                    conn.close()
                    if not items_in_sr.empty:
                        items_in_sr['Qtd'] = items_in_sr['Qtd'].apply(format_br)
                        st.table(items_in_sr)
                    else: st.write('Esta sub-receita não possui itens cadastrados.')
        else: st.info('Sem sub-receitas vinculadas.')
    else:
        st.warning('Cadastre uma receita primeiro.')
