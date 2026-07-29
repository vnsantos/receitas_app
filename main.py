import streamlit as st
import sqlite3

# --- Database Initialization ---
def init_db():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            unit TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sub_recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            recipe_id INTEGER,
            product_id INTEGER,
            quantity REAL NOT NULL,
            PRIMARY KEY (recipe_id, product_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sub_recipe_ingredients (
            sub_recipe_id INTEGER,
            product_id INTEGER,
            quantity REAL NOT NULL,
            PRIMARY KEY (sub_recipe_id, product_id),
            FOREIGN KEY (sub_recipe_id) REFERENCES sub_recipes(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipe_sub_recipes (
            recipe_id INTEGER,
            sub_recipe_id INTEGER,
            quantity REAL NOT NULL,
            PRIMARY KEY (recipe_id, sub_recipe_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
            FOREIGN KEY (sub_recipe_id) REFERENCES sub_recipes(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

# Initialize the database when the app starts (or if it doesn't exist)
init_db()

# --- Database Connection Utility ---
def get_db_connection():
    conn = sqlite3.connect('recipes.db')
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

# --- Product Management Functions ---
def add_product(name, unit):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (name, unit) VALUES (?, ?)", (name, unit))
        conn.commit()
        return True, "Product added successfully!"
    except sqlite3.IntegrityError:
        return False, f"Product '{name}' already exists."
    except Exception as e:
        return False, f"Error adding product: {e}"
    finally:
        conn.close()

def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return products

def get_product_by_id(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

def update_product(product_id, name, unit):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE products SET name = ?, unit = ? WHERE id = ?", (name, unit, product_id))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Product updated successfully!"
        else:
            return False, "Product not found."
    except sqlite3.IntegrityError:
        return False, f"Product '{name}' already exists with a different ID."
    except Exception as e:
        return False, f"Error updating product: {e}"
    finally:
        conn.close()

def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Product deleted successfully!"
        else:
            return False, "Product not found."
    except Exception as e:
        return False, f"Error deleting product: {e}"
    finally:
        conn.close()

# --- Sub-Recipe Management Functions ---
def add_sub_recipe(name, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO sub_recipes (name, description) VALUES (?, ?)", (name, description))
        conn.commit()
        return True, "Sub-Recipe added successfully!"
    except sqlite3.IntegrityError:
        return False, f"Sub-Recipe '{name}' already exists."
    except Exception as e:
        return False, f"Error adding sub-recipe: {e}"
    finally:
        conn.close()

def get_sub_recipes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sub_recipes")
    sub_recipes = cursor.fetchall()
    conn.close()
    return sub_recipes

def get_sub_recipe_by_id(sub_recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sub_recipes WHERE id = ?", (sub_recipe_id,))
    sub_recipe = cursor.fetchone()
    conn.close()
    return sub_recipe

def update_sub_recipe(sub_recipe_id, name, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE sub_recipes SET name = ?, description = ? WHERE id = ?", (name, description, sub_recipe_id))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Sub-Recipe updated successfully!"
        else:
            return False, "Sub-Recipe not found."
    except sqlite3.IntegrityError:
        return False, f"Sub-Recipe '{name}' already exists with a different ID."
    except Exception as e:
        return False, f"Error updating sub-recipe: {e}"
    finally:
        conn.close()

def delete_sub_recipe(sub_recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sub_recipes WHERE id = ?", (sub_recipe_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Sub-Recipe deleted successfully!"
        else:
            return False, "Sub-Recipe not found."
    except Exception as e:
        return False, f"Error deleting sub-recipe: {e}"
    finally:
        conn.close()

# --- Sub-Recipe Ingredient Management Functions ---
def add_sub_recipe_product_ingredient(sub_recipe_id, product_id, quantity):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO sub_recipe_ingredients (sub_recipe_id, product_id, quantity) VALUES (?, ?, ?)", (sub_recipe_id, product_id, quantity))
        conn.commit()
        return True, "Product ingredient added to sub-recipe!"
    except sqlite3.IntegrityError:
        return False, "This product is already an ingredient in this sub-recipe. Use update to change quantity."
    except Exception as e:
        return False, f"Error adding product ingredient: {e}"
    finally:
        conn.close()

def get_sub_recipe_product_ingredients(sub_recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT sri.product_id, p.name as product_name, p.unit, sri.quantity FROM sub_recipe_ingredients sri JOIN products p ON sri.product_id = p.id WHERE sri.sub_recipe_id = ?""", (sub_recipe_id,))
    ingredients = cursor.fetchall()
    conn.close()
    return ingredients

def update_sub_recipe_product_ingredient(sub_recipe_id, product_id, new_quantity):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE sub_recipe_ingredients SET quantity = ? WHERE sub_recipe_id = ? AND product_id = ?", (new_quantity, sub_recipe_id, product_id))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Product ingredient quantity updated!"
        else:
            return False, "Product ingredient not found in sub-recipe."
    except Exception as e:
        return False, f"Error updating product ingredient: {e}"
    finally:
        conn.close()

def delete_sub_recipe_product_ingredient(sub_recipe_id, product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sub_recipe_ingredients WHERE sub_recipe_id = ? AND product_id = ?", (sub_recipe_id, product_id))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Product ingredient removed from sub-recipe!"
        else:
            return False, "Product ingredient not found in sub-recipe."
    except Exception as e:
        return False, f"Error deleting product ingredient: {e}"
    finally:
        conn.close()

# --- Main Recipe Management Functions ---
def add_recipe(name, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO recipes (name, description) VALUES (?, ?)", (name, description))
        conn.commit()
        return True, "Recipe added successfully!"
    except sqlite3.IntegrityError:
        return False, f"Recipe '{name}' already exists."
    except Exception as e:
        return False, f"Error adding recipe: {e}"
    finally:
        conn.close()

def get_recipes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes")
    recipes = cursor.fetchall()
    conn.close()
    return recipes

def get_recipe_by_id(recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    recipe = cursor.fetchone()
    conn.close()
    return recipe

def update_recipe(recipe_id, name, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE recipes SET name = ?, description = ? WHERE id = ?", (name, description, recipe_id))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Recipe updated successfully!"
        else:
            return False, "Recipe not found."
    except sqlite3.IntegrityError:
        return False, f"Recipe '{name}' already exists with a different ID."
    except Exception as e:
        return False, f"Error updating recipe: {e}"
    finally:
        conn.close()

def delete_recipe(recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Recipe deleted successfully!"
        else:
            return False, "Recipe not found."
    except Exception as e:
        return False, f"Error deleting recipe: {e}"
    finally:
        conn.close()

# --- Recipe Product Ingredient Management Functions ---
def add_recipe_product_ingredient(recipe_id, product_id, quantity):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO recipe_ingredients (recipe_id, product_id, quantity) VALUES (?, ?, ?)", (recipe_id, product_id, quantity))
        conn.commit()
        return True, "Product ingredient added to recipe!"
    except sqlite3.IntegrityError:
        return False, "This product is already an ingredient in this recipe. Use update to change quantity."
    except Exception as e:
        return False, f"Error adding product ingredient: {e}"
    finally:
        conn.close()

def get_recipe_product_ingredients(recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT ri.product_id, p.name as product_name, p.unit, ri.quantity FROM recipe_ingredients ri JOIN products p ON ri.product_id = p.id WHERE ri.recipe_id = ?""", (recipe_id,))
    ingredients = cursor.fetchall()
    conn.close()
    return ingredients

def update_recipe_product_ingredient(recipe_id, product_id, new_quantity):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE recipe_ingredients SET quantity = ? WHERE recipe_id = ? AND product_id = ?", (new_quantity, recipe_id, product_id))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Product ingredient quantity updated!"
        else:
            return False, "Product ingredient not found in recipe."
    except Exception as e:
        return False, f"Error updating product ingredient: {e}"
    finally:
        conn.close()

def delete_recipe_product_ingredient(recipe_id, product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ? AND product_id = ?", (recipe_id, product_id))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Product ingredient removed from recipe!"
        else:
            return False, "Product ingredient not found in recipe."
    except Exception as e:
        return False, f"Error deleting product ingredient: {e}"
    finally:
        conn.close()

# --- Recipe Sub-Recipe Management Functions ---
def add_recipe_sub_recipe(recipe_id, sub_recipe_id, quantity):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO recipe_sub_recipes (recipe_id, sub_recipe_id, quantity) VALUES (?, ?, ?)", (recipe_id, sub_recipe_id, quantity))
        conn.commit()
        return True, "Sub-Recipe added to recipe!"
    except sqlite3.IntegrityError:
        return False, "This sub-recipe is already part of this main recipe. Use update to change quantity."
    except Exception as e:
        return False, f"Error adding sub-recipe to recipe: {e}"
    finally:
        conn.close()

def get_recipe_sub_recipes(recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT rsr.sub_recipe_id, sr.name as sub_recipe_name, rsr.quantity FROM recipe_sub_recipes rsr JOIN sub_recipes sr ON rsr.sub_recipe_id = sr.id WHERE rsr.recipe_id = ?""", (recipe_id,))
    sub_recipes = cursor.fetchall()
    conn.close()
    return sub_recipes

def update_recipe_sub_recipe(recipe_id, sub_recipe_id, new_quantity):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE recipe_sub_recipes SET quantity = ? WHERE recipe_id = ? AND sub_recipe_id = ?", (new_quantity, recipe_id, sub_recipe_id))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Sub-Recipe quantity in recipe updated!"
        else:
            return False, "Sub-Recipe not found in recipe."
    except Exception as e:
        return False, f"Error updating sub-recipe in recipe: {e}"
    finally:
        conn.close()

def delete_recipe_sub_recipe(recipe_id, sub_recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM recipe_sub_recipes WHERE recipe_id = ? AND sub_recipe_id = ?", (recipe_id, sub_recipe_id))
        conn.commit()
        if cursor.rowcount > 0:
            return True, "Sub-Recipe removed from recipe!"
        else:
            return False, "Sub-Recipe not found in recipe."
    except Exception as e:
        return False, f"Error deleting sub-recipe from recipe: {e}"
    finally:
        conn.close()


# --- Streamlit App Layout ---
st.set_page_config(page_title="Recipe Management App", layout="wide")
st.title("🍳 Recipe and Inventory Management")

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["Products", "Sub-Recipes", "Recipes"])

with tab1:
    st.header("📦 Product Management")
    # Form to add new products
    with st.form("add_product_form", clear_on_submit=True):
        st.subheader("Add New Product")
        product_name = st.text_input("Product Name")
        product_unit = st.text_input("Unit (e.g., kg, g, unidade)")
        submitted = st.form_submit_button("Add Product")
        if submitted:
            if product_name and product_unit:
                success, message = add_product(product_name, product_unit)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.warning("Please fill in all fields.")

    st.subheader("Existing Products")
    products = get_products()
    if products:
        st.dataframe(products)

        st.markdown("--- ")
        st.subheader("Update Product")
        # Use a unique key for selectbox to avoid Streamlit rerun issues
        product_to_update_id = st.selectbox("Select Product to Update", [p['id'] for p in products], format_func=lambda x: get_product_by_id(x)['name'], key='update_product_select')
        if product_to_update_id:
            selected_product = get_product_by_id(product_to_update_id)
            with st.form("update_product_form", clear_on_submit=False):
                updated_name = st.text_input("New Product Name", value=selected_product['name'])
                updated_unit = st.text_input("New Unit", value=selected_product['unit'])
                update_submitted = st.form_submit_button("Update Product")
                if update_submitted:
                    if updated_name and updated_unit:
                        success, message = update_product(product_to_update_id, updated_name, updated_unit)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    else:
                        st.warning("Please fill in all fields for update.")

        st.markdown("--- ")
        st.subheader("Delete Product")
        product_to_delete_id = st.selectbox("Select Product to Delete", [p['id'] for p in products], format_func=lambda x: get_product_by_id(x)['name'], key='delete_product_select')
        if product_to_delete_id:
            if st.button("Delete Selected Product"):
                success, message = delete_product(product_to_delete_id)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    else:
        st.info("No products added yet.")

with tab2:
    st.header("🍲 Sub-Recipe Management")

    # Add Sub-Recipe Form
    with st.form("add_sub_recipe_form", clear_on_submit=True):
        st.subheader("Add New Sub-Recipe")
        sub_recipe_name = st.text_input("Sub-Recipe Name")
        sub_recipe_description = st.text_area("Description (Optional)")
        submitted = st.form_submit_button("Add Sub-Recipe")
        if submitted:
            if sub_recipe_name:
                success, message = add_sub_recipe(sub_recipe_name, sub_recipe_description)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.warning("Sub-Recipe Name cannot be empty.")

    st.subheader("Existing Sub-Recipes")
    sub_recipes = get_sub_recipes()
    if sub_recipes:
        st.dataframe(sub_recipes)

        st.markdown("--- ")
        st.subheader("Manage Sub-Recipe Ingredients and Details")
        selected_sub_recipe_id = st.selectbox("Select Sub-Recipe to Manage", [sr['id'] for sr in sub_recipes], format_func=lambda x: get_sub_recipe_by_id(x)['name'], key='manage_sub_recipe_select')

        if selected_sub_recipe_id:
            selected_sub_recipe = get_sub_recipe_by_id(selected_sub_recipe_id)
            st.markdown(f"### Managing: {selected_sub_recipe['name']}")

            # Update Sub-Recipe Form
            with st.form("update_sub_recipe_form", clear_on_submit=False):
                st.write("Update Sub-Recipe Details")
                updated_sr_name = st.text_input("New Sub-Recipe Name", value=selected_sub_recipe['name'], key=f'update_sr_name_{selected_sub_recipe_id}')
                updated_sr_description = st.text_area("New Description", value=selected_sub_recipe['description'] if selected_sub_recipe['description'] else "", key=f'update_sr_desc_{selected_sub_recipe_id}')
                update_submitted = st.form_submit_button("Update Sub-Recipe")
                if update_submitted:
                    if updated_sr_name:
                        success, message = update_sub_recipe(selected_sub_recipe_id, updated_sr_name, updated_sr_description)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    else:
                        st.warning("Sub-Recipe Name cannot be empty.")

            st.markdown("--- ")
            st.write("#### Add Product Ingredient to Sub-Recipe")
            available_products = get_products()
            if available_products:
                with st.form(f"add_sr_ingredient_form_{selected_sub_recipe_id}", clear_on_submit=True):
                    product_options = {p['name']: p['id'] for p in available_products}
                    selected_product_name = st.selectbox("Select Product", list(product_options.keys()), key=f'add_sr_product_select_{selected_sub_recipe_id}')
                    ingredient_quantity = st.number_input("Quantity", min_value=0.01, value=1.0, step=0.1, key=f'add_sr_quantity_{selected_sub_recipe_id}')
                    add_ingredient_submitted = st.form_submit_button("Add Ingredient")
                    if add_ingredient_submitted:
                        product_id = product_options[selected_product_name]
                        success, message = add_sub_recipe_product_ingredient(selected_sub_recipe_id, product_id, ingredient_quantity)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            else:
                st.info("No products available to add as ingredients. Please add products in the 'Products' tab first.")

            st.markdown("--- ")
            st.write("#### Current Product Ingredients")
            current_ingredients = get_sub_recipe_product_ingredients(selected_sub_recipe_id)
            if current_ingredients:
                st.dataframe(current_ingredients)

                # Delete Ingredient Form
                st.write("Remove Product Ingredient")
                ingredient_options = {f"{ing['product_name']} ({ing['quantity']} {ing['unit']})": ing['product_id'] for ing in current_ingredients}
                product_to_remove_option = st.selectbox("Select Ingredient to Remove", list(ingredient_options.keys()), format_func=lambda x: x.split(' (')[0], key=f'remove_sr_ingredient_select_{selected_sub_recipe_id}')
                if product_to_remove_option:
                    if st.button("Remove Ingredient", key=f'remove_sr_ingredient_button_{selected_sub_recipe_id}'):
                        selected_product_id = ingredient_options[product_to_remove_option]
                        success, message = delete_sub_recipe_product_ingredient(selected_sub_recipe_id, selected_product_id)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            else:
                st.info("No product ingredients added to this sub-recipe yet.")

            st.markdown("--- ")
            st.subheader("Delete Sub-Recipe")
            if st.button("Delete Selected Sub-Recipe", key=f'delete_sr_button_{selected_sub_recipe_id}'):
                success, message = delete_sub_recipe(selected_sub_recipe_id)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    else:
        st.info("No sub-recipes added yet.")


with tab3:
    st.header("📝 Recipe Management")

    # Add Recipe Form
    with st.form("add_recipe_form", clear_on_submit=True):
        st.subheader("Add New Recipe")
        recipe_name = st.text_input("Recipe Name")
        recipe_description = st.text_area("Description (Optional)")
        submitted = st.form_submit_button("Add Recipe")
        if submitted:
            if recipe_name:
                success, message = add_recipe(recipe_name, recipe_description)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.warning("Recipe Name cannot be empty.")

    st.subheader("Existing Recipes")
    recipes = get_recipes()
    if recipes:
        st.dataframe(recipes)

        st.markdown("--- ")
        st.subheader("Manage Recipe Ingredients, Sub-Recipes, and Details")
        selected_recipe_id = st.selectbox("Select Recipe to Manage", [r['id'] for r in recipes], format_func=lambda x: get_recipe_by_id(x)['name'], key='manage_recipe_select')

        if selected_recipe_id:
            selected_recipe = get_recipe_by_id(selected_recipe_id)
            st.markdown(f"### Managing: {selected_recipe['name']}")

            # Update Recipe Form
            with st.form("update_recipe_form", clear_on_submit=False):
                st.write("Update Recipe Details")
                updated_r_name = st.text_input("New Recipe Name", value=selected_recipe['name'], key=f'update_r_name_{selected_recipe_id}')
                updated_r_description = st.text_area("New Description", value=selected_recipe['description'] if selected_recipe['description'] else "", key=f'update_r_desc_{selected_recipe_id}')
                update_submitted = st.form_submit_button("Update Recipe")
                if update_submitted:
                    if updated_r_name:
                        success, message = update_recipe(selected_recipe_id, updated_r_name, updated_r_description)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    else:
                        st.warning("Recipe Name cannot be empty.")

            st.markdown("--- ")
            st.write("#### Add Product Ingredient to Recipe")
            available_products = get_products()
            if available_products:
                with st.form(f"add_r_ingredient_form_{selected_recipe_id}", clear_on_submit=True):
                    product_options = {p['name']: p['id'] for p in available_products}
                    selected_product_name = st.selectbox("Select Product", list(product_options.keys()), key=f'add_r_product_select_{selected_recipe_id}')
                    ingredient_quantity = st.number_input("Quantity", min_value=0.01, value=1.0, step=0.1, key=f'add_r_quantity_{selected_recipe_id}')
                    add_ingredient_submitted = st.form_submit_button("Add Product Ingredient")
                    if add_ingredient_submitted:
                        product_id = product_options[selected_product_name]
                        success, message = add_recipe_product_ingredient(selected_recipe_id, product_id, ingredient_quantity)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            else:
                st.info("No products available to add as ingredients. Please add products in the 'Products' tab first.")

            st.markdown("--- ")
            st.write("#### Current Product Ingredients")
            current_product_ingredients = get_recipe_product_ingredients(selected_recipe_id)
            if current_product_ingredients:
                st.dataframe(current_product_ingredients)

                # Delete Product Ingredient Form
                st.write("Remove Product Ingredient")
                product_ing_options = {f"{ing['product_name']} ({ing['quantity']} {ing['unit']})": ing['product_id'] for ing in current_product_ingredients}
                product_to_remove_option = st.selectbox("Select Product Ingredient to Remove", list(product_ing_options.keys()), format_func=lambda x: x.split(' (')[0], key=f'remove_r_product_ingredient_select_{selected_recipe_id}')
                if product_to_remove_option:
                    if st.button("Remove Product Ingredient", key=f'remove_r_product_ingredient_button_{selected_recipe_id}'):
                        selected_product_id = product_ing_options[product_to_remove_option]
                        success, message = delete_recipe_product_ingredient(selected_recipe_id, selected_product_id)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            else:
                st.info("No product ingredients added to this recipe yet.")

            st.markdown("--- ")
            st.write("#### Add Sub-Recipe to Recipe")
            available_sub_recipes = get_sub_recipes()
            if available_sub_recipes:
                with st.form(f"add_r_sub_recipe_form_{selected_recipe_id}", clear_on_submit=True):
                    sub_recipe_options = {sr['name']: sr['id'] for sr in available_sub_recipes}
                    selected_sub_recipe_name = st.selectbox("Select Sub-Recipe", list(sub_recipe_options.keys()), key=f'add_r_sub_recipe_select_{selected_recipe_id}')
                    sub_recipe_quantity = st.number_input("Quantity (e.g., how many units of this sub-recipe are needed)", min_value=0.01, value=1.0, step=0.1, key=f'add_r_sub_recipe_quantity_{selected_recipe_id}')
                    add_sub_recipe_submitted = st.form_submit_button("Add Sub-Recipe")
                    if add_sub_recipe_submitted:
                        sub_recipe_id = sub_recipe_options[selected_sub_recipe_name]
                        success, message = add_recipe_sub_recipe(selected_recipe_id, sub_recipe_id, sub_recipe_quantity)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            else:
                st.info("No sub-recipes available to add. Please create sub-recipes in the 'Sub-Recipes' tab first.")

            st.markdown("--- ")
            st.write("#### Current Sub-Recipes in Recipe")
            current_recipe_sub_recipes = get_recipe_sub_recipes(selected_recipe_id)
            if current_recipe_sub_recipes:
                st.dataframe(current_recipe_sub_recipes)

                # Delete Sub-Recipe from Recipe Form
                st.write("Remove Sub-Recipe from Recipe")
                sub_recipe_in_recipe_options = {f"{rsr['sub_recipe_name']} ({rsr['quantity']} units)": rsr['sub_recipe_id'] for rsr in current_recipe_sub_recipes}
                sub_recipe_to_remove_option = st.selectbox("Select Sub-Recipe to Remove", list(sub_recipe_in_recipe_options.keys()), format_func=lambda x: x.split(' (')[0], key=f'remove_r_sub_recipe_select_{selected_recipe_id}')
                if sub_recipe_to_remove_option:
                    if st.button("Remove Sub-Recipe", key=f'remove_r_sub_recipe_button_{selected_recipe_id}'):
                        selected_sub_recipe_id_to_remove = sub_recipe_in_recipe_options[sub_recipe_to_remove_option]
                        success, message = delete_recipe_sub_recipe(selected_recipe_id, selected_sub_recipe_id_to_remove)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            else:
                st.info("No sub-recipes added to this recipe yet.")

            st.markdown("--- ")
            st.subheader("Delete Recipe")
            if st.button("Delete Selected Recipe", key=f'delete_r_button_{selected_recipe_id}'):
                success, message = delete_recipe(selected_recipe_id)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    else:
        st.info("No recipes added yet.")
