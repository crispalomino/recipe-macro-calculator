import streamlit as st
import pandas as pd
import os
from io import BytesIO
from utils import (
    load_custom_ingredients,
    save_custom_ingredient,
    load_saved_recipes,
    save_recipe,
    delete_recipe,
    convert_unit_to_grams,
    fetch_usda_nutrition,
    calc_macros,
    export_recipe_pdf
)

# App title
st.set_page_config(page_title="Recipe Macro Calculator", layout="wide")
st.title("🥗 Recipe Macro Calculator")

# Load data
custom_ingredients = load_custom_ingredients()
saved_recipes = load_saved_recipes()

# Sidebar: Add Custom Ingredient
with st.sidebar:
    st.header("🧂 Add Custom Ingredient")
    with st.form("custom_form"):
        name = st.text_input("Ingredient name")
        unit = st.selectbox("Unit", ["g", "oz", "ml", "cup", "tbsp", "tsp", "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"])
        g_per_unit = st.number_input("Grams per unit", 0.0, 1000.0)
        p = st.number_input("Protein (100g)", 0.0, 100.0)
        c = st.number_input("Carbs (100g)", 0.0, 100.0)
        f = st.number_input("Fat (100g)", 0.0, 100.0)
        submitted = st.form_submit_button("Save Ingredient")
        if submitted and name:
            save_custom_ingredient(name, unit, g_per_unit, p, c, f)
            st.success(f"{name} saved. Please reload the app.")

# Tabs
tab1, tab2, tab3 = st.tabs(["➕ Add New Recipe", "📂 View/Edit Recipes", "📥 Import USDA"])

# Tab 1: Add New Recipe
with tab1:
    st.subheader("Add New Recipe")
    title = st.text_input("Recipe Title", key="new_title")
    servings = st.number_input("Number of Servings", 1, 100, 1)
    instructions = st.text_area("Instructions (optional)", height=100)
    ingredients = []

    for i in range(5):  # Allow 5 ingredient slots
        cols = st.columns([2, 1, 1, 1, 1, 1])
        name = cols[0].text_input("Ingredient", key=f"ing_{i}")
        amt = cols[1].number_input("Amount", 0.0, 10000.0, key=f"amt_{i}")
        unit = cols[2].selectbox("Unit", ["g", "oz", "ml", "cup", "tbsp", "tsp", "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"], key=f"unit_{i}")
        p = cols[3].number_input("Protein (100g)", 0.0, 100.0, key=f"p_{i}")
        c = cols[4].number_input("Carbs (100g)", 0.0, 100.0, key=f"c_{i}")
        f = cols[5].number_input("Fat (100g)", 0.0, 100.0, key=f"f_{i}")
        if name:
            ingredients.append({"name": name, "amt": amt, "unit": unit, "p": p, "c": c, "f": f})

    if st.button("Calculate Macros"):
        if not ingredients:
            st.warning("Please enter at least one ingredient.")
        else:
            df, totals = calc_macros(ingredients, servings, custom_ingredients)
            st.dataframe(df)
            st.subheader("Total Macros")
            st.json(totals)

            if st.button("💾 Save Recipe"):
                save_recipe(title, servings, ingredients, instructions)
                st.success("Recipe saved!")

            if st.button("📄 Export This Recipe"):
                pdf_bytes = export_recipe_pdf(title, df, totals, servings, instructions)
                st.download_button("Download PDF", data=pdf_bytes, file_name=f"{title}.pdf")

# Tab 2: View/Edit Recipes
with tab2:
    st.subheader("Saved Recipes")
    if saved_recipes:
        selected = st.selectbox("Select a recipe", list(saved_recipes.keys()))
        rec = saved_recipes[selected]
        st.write(f"**Servings:** {rec['servings']}")
        st.write(f"**Instructions:** {rec['instructions']}")
        st.json(rec["ingredients"])
        if st.button("🗑️ Delete Recipe"):
            delete_recipe(selected)
            st.experimental_rerun()
    else:
        st.info("No recipes saved yet.")

# Tab 3: USDA API
with tab3:
    st.subheader("USDA Lookup")
    query = st.text_input("Search USDA for an ingredient")
    if st.button("Search") and query:
        result = fetch_usda_nutrition(query)
        if isinstance(result, tuple):
            st.success(f"Protein: {result[0]}, Carbs: {result[1]}, Fat: {result[2]}")
        elif result:
            st.error(result)
        else:
            st.warning("No result found.")
