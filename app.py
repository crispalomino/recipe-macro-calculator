import streamlit as st
import json
import os
from utils import (
    get_macro_totals,
    generate_pdf,
    generate_label_pdf,
    load_saved_recipes,
    save_recipe,
    delete_recipe,
    duplicate_recipe,
    export_recipes_json,
    import_recipes_json,
    search_usda,
)
from datetime import datetime

st.set_page_config(page_title="Recipe Macro Calculator", layout="wide")
st.title("🥗 Recipe Macro Calculator")

# Load saved recipes
saved_recipes = load_saved_recipes()
custom_ingredients_path = "custom_ingredients.json"

if not os.path.exists(custom_ingredients_path):
    with open(custom_ingredients_path, "w") as f:
        json.dump({}, f)

with open(custom_ingredients_path, "r") as f:
    custom_ingredients = json.load(f)

# Sidebar: Add custom ingredient
st.sidebar.header("➕ Add Custom Ingredient")
with st.sidebar.form("custom_ingredient_form"):
    new_ingredient = st.text_input("Ingredient name")
    protein = st.number_input("Protein (100g)", 0.0, 1000.0, 0.0)
    carbs = st.number_input("Carbs (100g)", 0.0, 1000.0, 0.0)
    fat = st.number_input("Fat (100g)", 0.0, 1000.0, 0.0)
    submitted = st.form_submit_button("Add Ingredient")
    if submitted and new_ingredient:
        custom_ingredients[new_ingredient.lower()] = {"protein": protein, "carbs": carbs, "fat": fat}
        with open(custom_ingredients_path, "w") as f:
            json.dump(custom_ingredients, f)
        st.sidebar.success(f"{new_ingredient} added.")

# Recipe editor
st.header("Add New Recipe")
recipe_title = st.text_input("Recipe Title")
ingredients = []
cols = st.columns([3, 1, 1, 1, 1, 1])
cols[0].markdown("**Ingredient**")
cols[1].markdown("**Amount**")
cols[2].markdown("**Unit**")
cols[3].markdown("**Protein (100g)**")
cols[4].markdown("**Carbs (100g)**")
cols[5].markdown("**Fat (100g)**")

units = ["g", "oz", "ml", "tbsp", "tsp", "cup", "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"]
for i in range(10):
    cols = st.columns([3, 1, 1, 1, 1, 1])
    name = cols[0].text_input("Ingredient", key=f"name_{i}")
    amt = cols[1].number_input("Amount", 0.0, 10000.0, 0.0, key=f"amt_{i}")
    unit = cols[2].selectbox("Unit", units, key=f"unit_{i}")
    p = float(cols[3].number_input("Protein (100g)", 0.0, 1000.0, 0.0, key=f"p_{i}"))
    c = float(cols[4].number_input("Carbs (100g)", 0.0, 1000.0, 0.0, key=f"c_{i}"))
    f = float(cols[5].number_input("Fat (100g)", 0.0, 1000.0, 0.0, key=f"f_{i}"))

    if name:
        ingredients.append({
            "name": name,
            "amount": amt,
            "unit": unit,
            "protein_per_100g": p,
            "carbs_per_100g": c,
            "fat_per_100g": f
        })

instructions = st.text_area("Instructions (optional)")

scaling_col = st.columns(3)
if scaling_col[0].button("🔁 Scale 0.5x"):
    for ing in ingredients:
        ing["amount"] *= 0.5
if scaling_col[1].button("🔁 Scale 2x"):
    for ing in ingredients:
        ing["amount"] *= 2
if scaling_col[2].button("🔁 Scale 4x"):
    for ing in ingredients:
        ing["amount"] *= 4

num_servings = st.number_input("Number of Servings", 1, 100, 1)
calculate = st.button("Calculate Macros")

if calculate and ingredients:
    totals = get_macro_totals(ingredients)
    per_serving = {k: round(v / num_servings, 2) for k, v in totals.items()}
    st.subheader("Total Macros")
    st.write(totals)
    st.subheader(f"Per Serving (÷ {num_servings})")
    st.write(per_serving)

    if recipe_title:
        save_recipe({
            "title": recipe_title,
            "ingredients": ingredients,
            "instructions": instructions,
            "servings": num_servings,
            "macros": per_serving
        })
        st.success("Recipe saved.")

# --- Saved Recipes ---
st.header("📒 Saved Recipes")
filter_col = st.columns([2, 2, 4])
show_favs = filter_col[1].checkbox("⭐ Show Favorites Only")
search_term = filter_col[2].text_input("🔍 Search by title or tag")

filtered = []
for r in saved_recipes:
    match_title = search_term.lower() in r["title"].lower()
    match_tag = any(search_term.lower() in tag.lower() for tag in r.get("tags", []))
    if (not search_term or match_title or match_tag) and (not show_favs or r.get("favorite")):
        filtered.append(r)

for i, r in enumerate(filtered):
    with st.expander(r["title"]):
        st.write(f"**Servings:** {r.get('servings', 1)}")
        st.write("**Macros per Serving:**")
        st.write(r["macros"])
        st.write("**Instructions:**")
        st.write(r.get("instructions", ""))
        col1, col2, col3, col4, col5 = st.columns(5)
        if col1.button("🗑 Delete", key=f"del_{i}"):
            delete_recipe(r["title"])
            st.experimental_rerun()
        if col2.button("📄 Duplicate", key=f"dup_{i}"):
            duplicate_recipe(r["title"])
            st.experimental_rerun()
        if col3.button("⬇ Export This Recipe", key=f"pdf_{i}"):
            pdf = generate_label_pdf(r["title"], r["macros"])
            st.download_button("📥 Download PDF", data=pdf, file_name=f"{r['title']}.pdf", mime="application/pdf")
        if col4.button("⭐ Toggle Favorite", key=f"fav_{i}"):
            r["favorite"] = not r.get("favorite", False)
            save_recipe(r, overwrite=True)
            st.experimental_rerun()

# --- Import/Export ---
st.sidebar.header("📤 Import/Export Recipes")
if st.sidebar.button("Export All"):
    export_data = export_recipes_json()
    st.sidebar.download_button("Download All Recipes", data=export_data, file_name="recipes.json", mime="application/json")

import_file = st.sidebar.file_uploader("Import Recipes", type="json")
if import_file:
    import_recipes_json(import_file)
    st.sidebar.success("Recipes imported.")
    st.experimental_rerun()

# --- USDA Ingredient Lookup ---
st.sidebar.header("🔍 USDA Ingredient Lookup")
usda_query = st.sidebar.text_input("Search USDA database")
if usda_query:
    results = search_usda(usda_query)
    if results:
        for name, macros in results:
            st.sidebar.write(f"**{name}**")
            st.sidebar.write(macros)
    else:
        st.sidebar.warning("No results found.")
