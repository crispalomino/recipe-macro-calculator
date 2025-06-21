import streamlit as st
import pandas as pd
import json
from utils import (
    load_custom_ingredients,
    save_custom_ingredient,
    convert_unit_to_grams,
    calc_macros,
    export_recipe_pdf,
    fetch_usda_nutrition,
    load_saved_recipes,
    save_recipe,
    delete_recipe
)

st.set_page_config(page_title="Recipe Macro Calculator", layout="wide")
st.title("📘 Recipe Macro Calculator")

# ────── USDA Key Check ──────
api_ready = "usda" in st.secrets and "api_key" in st.secrets["usda"]

# ────── Data Load ──────
custom_ingredients = load_custom_ingredients()
saved_recipes = load_saved_recipes()

# ────── Add Custom Ingredient ──────
with st.sidebar.expander("➕ Add Custom Ingredient", expanded=False):
    with st.form("custom_ingredient_form"):
        name = st.text_input("Name")
        unit = st.selectbox("Unit", ["g", "oz", "ml", "cup", "tbsp", "tsp", "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"])
        g_unit = st.number_input("Grams per unit", 0.1, 9999.0, 100.0)
        p = st.number_input("Protein (per 100g)", 0.0)
        f = st.number_input("Fat (per 100g)", 0.0)
        c = st.number_input("Carbs (per 100g)", 0.0)
        if st.form_submit_button("Save"):
            save_custom_ingredient(name, unit, g_unit, p, c, f)
            st.success(f"{name} saved.")

# ────── Recipe Inputs ──────
st.header("🧾 Create or Edit Recipe")

title = st.text_input("Recipe Title")
servings = st.number_input("Number of servings", 1, 100, 1)
scale_col1, scale_col2, scale_col3 = st.columns(3)
if scale_col1.button("🔁 0.5x Servings"):
    servings *= 0.5
if scale_col2.button("🔁 2x Servings"):
    servings *= 2
if scale_col3.button("🔁 4x Servings"):
    servings *= 4

instructions = st.text_area("Recipe Instructions", height=150)
num_ingredients = st.number_input("Number of ingredients", 1, 20, 5)

ingredient_inputs = []
for i in range(int(num_ingredients)):
    cols = st.columns([3, 1.5, 1.5, 1.5, 1, 1])
    name = cols[0].text_input("Ingredient", key=f"name_{i}")
    amt = cols[1].number_input("Amount", 0.0, 9999.0, step=1.0, key=f"amt_{i}")
    unit = cols[2].selectbox("Unit", ["g", "oz", "ml", "cup", "tbsp", "tsp", "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"], key=f"unit_{i}")

    # Lookup
    p = c = f = 0.0
    if name.lower() in custom_ingredients:
        ing = custom_ingredients[name.lower()]
        p, c, f = ing["p"], ing["c"], ing["f"]
    elif api_ready and name:
        usda = fetch_usda_nutrition(name)
        if usda:
            p, c, f = usda

    p = cols[3].number_input("Protein (100g)", 0.0, 1000.0, p, key=f"p_{i}")
    c = cols[4].number_input("Carbs (100g)", 0.0, 1000.0, c, key=f"c_{i}")
    f = cols[5].number_input("Fat (100g)", 0.0, 1000.0, f, key=f"f_{i}")

    ingredient_inputs.append({
        "name": name,
        "amt": amt,
        "unit": unit,
        "p": p,
        "c": c,
        "f": f
    })

# ────── Calculate & Output ──────
if st.button("🔍 Calculate Macros"):
    df, totals = calc_macros(ingredient_inputs, servings, custom_ingredients)
    st.subheader("Per Ingredient")
    st.dataframe(df)
    st.subheader("Total Recipe Macros")
    st.write(totals)
    per_serv = {k: round(v / servings, 2) for k, v in totals.items()}
    st.subheader(f"Per Serving (Servings: {servings})")
    st.write(per_serv)

    pdf = export_recipe_pdf(title or "Recipe", df, totals, servings, instructions)
    st.download_button("📄 Export This Recipe", data=pdf, file_name=f"{title or 'recipe'}.pdf", mime="application/pdf")

# ────── Save Recipe ──────
if st.button("💾 Save Recipe"):
    save_recipe(title, servings, ingredient_inputs, instructions)
    st.success("Recipe saved!")

# ────── Load/Delete Saved ──────
st.header("📂 Saved Recipes")
if saved_recipes:
    name = st.selectbox("Select Recipe", list(saved_recipes.keys()))
    col1, col2 = st.columns(2)
    if col1.button("📥 Load"):
        loaded = saved_recipes[name]
        st.experimental_rerun()
    if col2.button("❌ Delete"):
        delete_recipe(name)
        st.warning(f"{name} deleted.")