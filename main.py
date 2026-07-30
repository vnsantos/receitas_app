import streamlit as st
import sqlite3
import pandas as pd

# --- Configuração e Inicialização do Banco de Dados ---
def init_db():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    # Tabelas base
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, unit TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sub_recipes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, description TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, description TEXT)''')
    # Tabelas de vínculo (Ingredientes e Sub-receitas dentro de Receitas)
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipe_ingredients (recipe_id INTEGER, product_id INTEGER, quantity REAL NOT NULL, PRIMARY KEY (recipe_id, product_id), FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE, FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS recipe_sub_recipes (recipe_id INTEGER, sub_recipe_id INTEGER, quantity REAL NOT NULL, PRIMARY KEY (recipe_id, sub_recipe_id), FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE, FOREIGN KEY (sub_recipe_id) REFERENCES sub_recipes(id) ON DELETE CASCADE)''')
    # Vínculo de produtos dentro de sub-receitas
    cursor.execute('''CREATE TABLE IF NOT EXISTS sub_recipe_ingredients (sub_recipe_id INTEGER, product_id INTEGER, quantity REAL NOT NULL, PRIMARY KEY (sub_recipe_id, product_id), FOREIGN KEY (sub_recipe_id) REFERENCES sub_recipes(id) ON DELETE CASCADE, FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE)''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('recipes.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Funções Auxiliares ---
def get_all(table):
    conn = get_db_connection()
    df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
    conn.close()
    return df

def run_query(query, params=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return True, 'Operação realizada com sucesso!'
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- Interface Streamlit ---
st.set_page_config(page_title='Gestor de Receitas Profissional', layout='wide')
st.title('🍳 Gestão de Receitas, Sub-Receitas e Itens')

tabs = st.tabs(['🔍 Visualizar Receitas', '📝 Montar Receita', '🍲 Criar Sub-Receita', '📦 Cadastro de Produtos'])

# 1. VISUALIZAR RECEITAS
with tabs[0]:
    st.header('Consulta de Fichas Técnicas')
    recipes_list = get_all('recipes')
    if not recipes_list.empty:
        target_id = st.selectbox('Escolha uma receita para abrir:', recipes_list['id'], format_func=lambda x: recipes_list[recipes_list['id']==x]['name'].values[0])
        
        conn = get_db_connection()
        # Busca produtos vinculados
        df_p = pd.read_sql_query('SELECT p.name as Produto, ri.quantity as Qtd, p.unit as Unidade FROM recipe_ingredients ri JOIN products p ON ri.product_id = p.id WHERE ri.recipe_id = ?', conn, params=(target_id,))
        # Busca sub-receitas vinculadas
        df_sr = pd.read_sql_query('SELECT sr.name as SubReceita, rsr.quantity as Qtd FROM recipe_sub_recipes rsr JOIN sub_recipes sr ON rsr.sub_recipe_id = sr.id WHERE rsr.recipe_id = ?', conn, params=(target_id,))
        conn.close()

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader('Produtos (Ingredientes)')
            if not df_p.empty: st.table(df_p)
            else: st.info('Sem produtos diretos nesta receita.')
        with col_b:
            st.subheader('Sub-Receitas (Bases)')
            if not df_sr.empty: st.table(df_sr)
            else: st.info('Sem sub-receitas nesta receita.')
    else:
        st.warning('Nenhuma receita cadastrada ainda.')

# 2. MONTAR RECEITA (Vincular itens)
with tabs[1]:
    st.header('Montagem de Receita Principal')
    with st.expander('➕ Criar Novo Nome de Receita'):
        new_r = st.text_input('Nome da Receita')
        if st.button('Cadastrar Nome'):
            run_query('INSERT INTO recipes (name) VALUES (?)', (new_r,))
            st.rerun()

    st.divider()
    recipes_df = get_all('recipes')
    if not recipes_df.empty:
        sel_id = st.selectbox('Selecione a receita que deseja editar:', recipes_df['id'], format_func=lambda x: recipes_df[recipes_df['id']==x]['name'].values[0])
        
        c1, c2 = st.columns(2)
        with c1:
            st.write('**Vincular Produto**')
            prods = get_all('products')
            p_name = st.selectbox('Escolha o Produto', prods['name'] if not prods.empty else ['Nenhum produto cadastrado'])
            p_qty = st.number_input('Quantidade', min_value=0.0, key='pq')
            if st.button('Vincular Produto'):
                pid = prods[prods['name']==p_name]['id'].values[0]
                run_query('INSERT OR REPLACE INTO recipe_ingredients (recipe_id, product_id, quantity) VALUES (?, ?, ?)', (sel_id, pid, p_qty))
                st.success('Produto vinculado!')
        
        with c2:
            st.write('**Vincular Sub-Receita**')
            subs = get_all('sub_recipes')
            sr_name = st.selectbox('Escolha a Sub-Receita', subs['name'] if not subs.empty else ['Nenhuma sub-receita cadastrada'])
            sr_qty = st.number_input('Quantidade', min_value=0.0, key='sq')
            if st.button('Vincular Sub-Receita'):
                sid = subs[subs['name']==sr_name]['id'].values[0]
                run_query('INSERT OR REPLACE INTO recipe_sub_recipes (recipe_id, sub_recipe_id, quantity) VALUES (?, ?, ?)', (sel_id, sid, sr_qty))
                st.success('Sub-receita vinculada!')

# 3. CRIAR SUB-RECEITA
with tabs[2]:
    st.header('Cadastro de Sub-Receitas (Bases)')
    sr_name_new = st.text_input('Nome da Sub-Receita (ex: Caldo de Galinha, Massa Base)')
    if st.button('Salvar Sub-Receita'):
        run_query('INSERT INTO sub_recipes (name) VALUES (?)', (sr_name_new,))
        st.success('Sub-receita criada!')
    st.dataframe(get_all('sub_recipes'), use_container_width=True)

# 4. PRODUTOS
with tabs[3]:
    st.header('Cadastro de Produtos (Matéria Prima)')
    with st.form('prod_form'):
        name = st.text_input('Nome do Item')
        unit = st.text_input('Unidade (kg, g, un, ml)')
        if st.form_submit_button('Salvar Produto'):
            run_query('INSERT INTO products (name, unit) VALUES (?, ?)', (name, unit))
            st.rerun()
    st.dataframe(get_all('products'), use_container_width=True)
