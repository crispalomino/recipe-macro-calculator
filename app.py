import streamlit as st
import pandas as pd
from utils import (
    load_custom_ingredients, save_custom_ingredient,
    load_saved_recipes, save_recipe, delete_recipe,
    convert_unit_to_grams, fetch_usda_nutrition, calc_macros,
    export_recipe_pdf
)

st.set_page_config(page_title="Recipe Macro Calculator", layout="wide")
st.title("🥗 Recipe Macro Calculator")

# Load data
custom_ingredients = load_custom_ingredients()
saved_recipes = load_saved_recipes()
categories = sorted(set(r.get("category", "Uncategorized") for r in saved_recipes.values()))
selected_category = st.sidebar.selectbox("📁 Filter by Category", ["All"] + categories)
show_favorites = st.sidebar.checkbox("⭐ Show Favorites Only")
search_term = st.sidebar.text_input("🔍 Search by title or tag")

# Filter recipes
filtered = []
for k, v in saved_recipes.items():
    if selected_category != "All" and v.get("category", "Uncategorized") != selected_category:
        continue
    if show_favorites and not v.get("favorite"):
        continue
    if search_term.lower() not in k.lower() and not any(search_term.lower() in tag.lower() for tag in v.get("tags", [])):
        continue
    v["title"] = k
    filtered.append(v)

recipe_titles = [r["title"] for r in filtered]

selected = st.selectbox("📋 Select a Recipe", [""] + recipe_titles)

if selected:
    recipe = saved_recipes[selected]
    st.subheader(selected)
    st.write(f"**Servings**: {recipe['servings']}")
    st.write("**Instructions**:")
    st.markdown(recipe.get("instructions", "_No instructions provided._"))

    df, totals = calc_macros(recipe["ingredients"], recipe["servings"], custom_ingredients)
    st.dataframe(df)

    st.markdown("### Total Macros")
    st.json(totals)

    # Export PDF
    if st.button("📄 Export This Recipe"):
        pdf = export_recipe_pdf(selected, df, totals, recipe["servings"], recipe.get("instructions", ""))
        st.download_button("Download PDF", pdf, file_name=f"{selected}.pdf")

    # Delete recipe
    if st.button("🗑️ Delete This Recipe"):
        delete_recipe(selected)
        st.success("Recipe deleted. Please refresh.")

st.markdown("---")
st.header("➕ Add New Recipe")

with st.form("add_recipe"):
    title = st.text_input("Recipe Title")
    servings = st.number_input("Number of Servings", min_value=1, value=1)
    instructions = st.text_area("Instructions (optional)")
    num_ingredients = st.number_input("Number of Ingredients", min_value=1, max_value=20, value=3)
    ingredients = []

    for i in range(num_ingredients):
        cols = st.columns([3, 2, 1, 1, 1, 1])
        name = cols[0].text_input(f"Ingredient", key=f"n_{i}")
        amt = cols[1].number_input("Amount", min_value=0.0, max_value=10000.0, value=100.0, key=f"a_{i}")
        unit = cols[2].selectbox("Unit", ["g", "oz", "ml", "cup", "tbsp", "tsp", "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"], key=f"u_{i}")
        p = cols[3].number_input("Protein (100g)", 0.0, 1000.0, 0.0, key=f"p_{i}")
        c = cols[4].number_input("Carbs (100g)", 0.0, 1000.0, 0.0, key=f"c_{i}")
        f = cols[5].number_input("Fat (100g)", 0.0, 1000.0, 0.0, key=f"f_{i}")
        ingredients.append({"name": name, "amt": amt, "unit": unit, "p": p, "c": c, "f": f})

    submitted = st.form_submit_button("Save Recipe")
    if submitted:
        save_recipe(title, servings, ingredients, instructions)
        st.success(f"Recipe '{title}' saved!")

st.sidebar.markdown("---")
st.sidebar.header("🧪 Add Custom Ingredient")
with st.sidebar.form("add_custom"):
    name = st.text_input("Ingredient Name")
    unit = st.selectbox("Unit", ["g", "oz", "ml", "cup", "tbsp", "tsp", "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"])
    g_per_unit = st.number_input("Grams per Unit", min_value=0.0, value=1.0)
    p = st.number_input("Protein per 100g", min_value=0.0, value=0.0)
    c = st.number_input("Carbs per 100g", min_value=0.0, value=0.0)
    f = st.number_input("Fat per 100g", min_value=0.0, value=0.0)
    add_it = st.form_submit_button("Add Custom Ingredient")
    if add_it:
        save_custom_ingredient(name, unit, g_per_unit, p, c, f)
        st.success(f"Custom ingredient '{name}' added.")
