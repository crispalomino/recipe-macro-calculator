import streamlit as st
import json
import os
from utils import (
    get_macro_totals,
    generate_pdf_from_dataframe,
    load_saved_recipes,
    save_recipe,
    delete_recipe,
    duplicate_recipe,
    load_custom_ingredients,
    add_custom_ingredient,
    convert_to_grams,
)

# Load saved recipes and custom ingredients
recipes = load_saved_recipes()
custom_ingredients = load_custom_ingredients()

st.title("🥗 Recipe Macro Calculator")

# Sidebar section for custom ingredient
with st.sidebar.expander("➕ Add Custom Ingredient"):
    with st.form("add_custom_ingredient"):
        name = st.text_input("Ingredient Name")
        unit = st.selectbox("Unit", ["g", "oz", "ml", "cup", "tbsp", "tsp", "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"])
        grams_per_unit = st.number_input("Grams per unit", min_value=0.0, step=0.1)
        calories = st.number_input("Calories per 100g", min_value=0.0)
        protein = st.number_input("Protein per 100g", min_value=0.0)
        carbs = st.number_input("Carbs per 100g", min_value=0.0)
        fat = st.number_input("Fat per 100g", min_value=0.0)
        submitted = st.form_submit_button("Add Ingredient")
        if submitted and name:
            add_custom_ingredient(name, unit, grams_per_unit, calories, protein, carbs, fat)
            st.success(f"{name} added!")

# Example form (simplified)
st.header("Add New Recipe")
with st.form("new_recipe"):
    title = st.text_input("Recipe Title")
    ingredients = st.text_area("List ingredients and quantities (e.g. 100g chicken, 2 tbsp olive oil)")
    submitted = st.form_submit_button("Calculate Macros")
    if submitted:
        # Dummy parser - real one would handle quantities, units, lookups, and conversions
        st.write("Macros would be shown here.")

# Load and display existing recipes
if recipes:
    st.header("📁 Saved Recipes")
    for recipe in recipes:
        st.subheader(recipe["title"])
        st.write(recipe)
