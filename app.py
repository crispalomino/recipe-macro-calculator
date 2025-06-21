
import streamlit as st
import pandas as pd
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

# Load initial data
custom_ingredients = load_custom_ingredients()
saved_recipes = load_saved_recipes()

st.set_page_config(page_title="Recipe Macro Calculator", layout="wide")

st.title("🥗 Recipe Macro Calculator")

menu = st.sidebar.radio("Navigation", ["Add New Recipe", "Saved Recipes", "Add Custom Ingredient"])

# ─────────────────────────────
# Add New Recipe Page
# ─────────────────────────────
if menu == "Add New Recipe":
    st.header("Add New Recipe")

    title = st.text_input("Recipe Title")
    servings = st.number_input("Number of Servings", min_value=1, value=1, step=1)

    st.markdown("### Ingredients")
    ingredients = []
    for i in range(10):
        cols = st.columns([3, 2, 1, 1, 1, 1])
        name = cols[0].text_input("Ingredient", key=f"name_{i}")
        amt = cols[1].number_input("Amount", 0.0, 10000.0, step=1.0, key=f"amt_{i}")
        unit = cols[2].selectbox("Unit", ["g", "oz", "ml", "cup", "tbsp", "tsp", "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"], key=f"unit_{i}")
        p = cols[3].number_input("Protein (100g)", 0.0, 1000.0, step=0.1, key=f"p_{i}")
        c = cols[4].number_input("Carbs (100g)", 0.0, 1000.0, step=0.1, key=f"c_{i}")
        f = cols[5].number_input("Fat (100g)", 0.0, 1000.0, step=0.1, key=f"f_{i}")
        if name:
            if p == 0.0 and c == 0.0 and f == 0.0:
                usda_result = fetch_usda_nutrition(name)
                if usda_result and isinstance(usda_result, tuple):
                    p, c, f = usda_result
                    cols[3].write(f"USDA P: {p}")
                    cols[4].write(f"USDA C: {c}")
                    cols[5].write(f"USDA F: {f}")
            ingredients.append({"name": name, "amt": amt, "unit": unit, "p": p, "c": c, "f": f})

    instructions = st.text_area("Instructions (optional)")

    if st.button("Calculate Macros"):
        if ingredients:
            df, totals = calc_macros(ingredients, servings, custom_ingredients)
            st.subheader("Macros per Ingredient")
            st.dataframe(df)
            st.subheader("Total Macros")
            st.json(totals)
            if st.button("Export This Recipe"):
                pdf_bytes = export_recipe_pdf(title, df, totals, servings, instructions)
                st.download_button("📄 Download PDF", pdf_bytes, file_name=f"{title}.pdf")
            if st.button("Save Recipe"):
                save_recipe(title, servings, ingredients, instructions)
                st.success("Recipe saved.")
        else:
            st.error("Please add at least one ingredient.")

# ─────────────────────────────
# Saved Recipes Page
# ─────────────────────────────
elif menu == "Saved Recipes":
    st.header("Saved Recipes")
    saved = load_saved_recipes()
    if saved:
        recipe_names = sorted(saved.keys())
        selected = st.selectbox("Select a recipe", recipe_names)
        recipe = saved[selected]
        st.write(f"**Servings:** {recipe['servings']}")
        st.write(f"**Instructions:** {recipe['instructions']}")
        df, totals = calc_macros(recipe["ingredients"], recipe["servings"], custom_ingredients)
        st.dataframe(df)
        st.subheader("Total Macros")
        st.json(totals)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export as PDF"):
                pdf_bytes = export_recipe_pdf(selected, df, totals, recipe["servings"], recipe["instructions"])
                st.download_button("📄 Download PDF", pdf_bytes, file_name=f"{selected}.pdf")
        with col2:
            if st.button("Delete Recipe"):
                delete_recipe(selected)
                st.success("Recipe deleted.")
    else:
        st.info("No saved recipes found.")

# ─────────────────────────────
# Add Custom Ingredient Page
# ─────────────────────────────
elif menu == "Add Custom Ingredient":
    st.header("Add Custom Ingredient")
    name = st.text_input("Ingredient Name")
    unit = st.selectbox("Unit Type", ["g", "oz", "ml", "cup", "tbsp", "tsp", "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"])
    g_per_unit = st.number_input("Grams per Unit", 0.0, 1000.0, value=1.0)
    p = st.number_input("Protein (per 100g)", 0.0, 1000.0, step=0.1)
    c = st.number_input("Carbs (per 100g)", 0.0, 1000.0, step=0.1)
    f = st.number_input("Fat (per 100g)", 0.0, 1000.0, step=0.1)
    if st.button("Save Custom Ingredient"):
        save_custom_ingredient(name, unit, g_per_unit, p, c, f)
        st.success(f"{name} saved as custom ingredient.")
