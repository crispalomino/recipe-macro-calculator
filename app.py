import streamlit as st
import json
import os
from utils import (
    load_custom_ingredients,
    save_custom_ingredient,
    convert_to_grams,
    calculate_macros,
    generate_pdf,
    search_usda_food,
    extract_macros_from_usda
)

st.set_page_config(page_title="Recipe Macro Calculator", layout="wide")

st.title("🥣 Recipe Macro Calculator")

usda_api_key = st.secrets["usda"]["api_key"]

custom_ingredients = load_custom_ingredients()
unit_options = ["g", "oz", "ml", "cup", "tbsp", "tsp", "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"]

st.sidebar.header("➕ Add Custom Ingredient")
with st.sidebar.form("custom_form"):
    name = st.text_input("Name")
    calories = st.number_input("Calories (per 100g)", value=0.0)
    protein = st.number_input("Protein (g)", value=0.0)
    carbs = st.number_input("Carbs (g)", value=0.0)
    fat = st.number_input("Fat (g)", value=0.0)
    fiber = st.number_input("Fiber (g)", value=0.0)
    if st.form_submit_button("Save Custom Ingredient"):
        save_custom_ingredient(name, calories, protein, carbs, fat, fiber)
        st.success(f"'{name}' saved!")

recipe_title = st.text_input("Recipe Title")
num_ingredients = st.number_input("Number of Ingredients", min_value=1, max_value=50, value=5)

ingredients = []
for i in range(num_ingredients):
    cols = st.columns([3, 1, 1, 1])
    name = cols[0].text_input(f"Ingredient {i+1} Name")
    amount = cols[1].number_input("Amount", key=f"a{i}")
    unit = cols[2].selectbox("Unit", unit_options, key=f"u{i}")

    calories = protein = carbs = fat = fiber = 0.0

    if name in [ci["name"] for ci in custom_ingredients]:
        ci = next(c for c in custom_ingredients if c["name"] == name)
        calories = ci["calories"]
        protein = ci["protein"]
        carbs = ci["carbs"]
        fat = ci["fat"]
        fiber = ci["fiber"]
    elif name:
        usda_results = search_usda_food(name, usda_api_key)
        if usda_results:
            usda_macros = extract_macros_from_usda(usda_results[0])
            calories = usda_macros["calories"]
            protein = usda_macros["protein"]
            carbs = usda_macros["carbs"]
            fat = usda_macros["fat"]
            fiber = usda_macros["fiber"]
            st.info(f"Auto-filled from USDA: {usda_results[0].get('description', '')}")
        else:
            st.warning(f"No USDA match found for '{name}'.")

    calories = st.number_input("Calories / 100g", value=calories, key=f"c{i}")
    protein = st.number_input("Protein (g)", value=protein, key=f"p{i}")
    carbs = st.number_input("Carbs (g)", value=carbs, key=f"carb{i}")
    fat = st.number_input("Fat (g)", value=fat, key=f"f{i}")
    fiber = st.number_input("Fiber (g)", value=fiber, key=f"fib{i}")

    ingredients.append({
        "name": name,
        "amount": amount,
        "unit": unit,
        "calories": calories,
        "protein": protein,
        "carbs": carbs,
        "fat": fat,
        "fiber": fiber
    })

servings = st.number_input("Number of Servings", min_value=1, value=1)
scale_buttons = st.columns(3)
if scale_buttons[0].button("0.5x"):
    servings = int(servings * 0.5)
if scale_buttons[1].button("2x"):
    servings *= 2
if scale_buttons[2].button("4x"):
    servings *= 4

if st.button("Calculate Macros"):
    results = calculate_macros(ingredients, servings)
    st.subheader("📊 Full Recipe Macros")
    st.write(results["total"])
    st.subheader("🍽 Per Serving Macros")
    st.write(results["per_serving"])
    if st.button("Export This Recipe"):
        generate_pdf(recipe_title, ingredients, results)
        st.success("PDF exported!")
