import streamlit as st
import json
import os
from utils import (
    get_macro_totals,
    generate_pdf_from_dataframe,
    convert_to_grams,
    load_custom_ingredients,
    save_custom_ingredient,
    parse_ingredient_line,
    USDA_API_KEY,
    fetch_usda_nutrition,
)

# Load or create custom ingredients
custom_ingredients = load_custom_ingredients()

st.set_page_config(page_title="Recipe Macro Calculator", layout="centered")
st.title("🥗 Recipe Macro Calculator")

# Sidebar - Add Custom Ingredient
st.sidebar.header("➕ Add Custom Ingredient")
with st.sidebar.form("custom_ingredient_form"):
    name = st.text_input("Ingredient name")
    protein = st.number_input("Protein (g per 100g)", min_value=0.0)
    carbs = st.number_input("Carbs (g per 100g)", min_value=0.0)
    fat = st.number_input("Fat (g per 100g)", min_value=0.0)
    density = st.number_input("Custom weight per unit (grams)", min_value=0.0, value=100.0)
    submitted = st.form_submit_button("Add Ingredient")
    if submitted and name:
        save_custom_ingredient(name, protein, carbs, fat, density)
        st.sidebar.success(f"Saved custom ingredient: {name}")

# Main Area
st.header("Add New Recipe")

title = st.text_input("Recipe Title", "")
raw_ingredients = st.text_area("List ingredients and quantities (e.g. 100g chicken, 2 tbsp olive oil)")

if st.button("Calculate Macros"):
    lines = raw_ingredients.split("\n")
    ingredient_data = []
    for line in lines:
        amount, unit, name = parse_ingredient_line(line)
        if not name:
            continue
        if name in custom_ingredients:
            macros_per_100g = custom_ingredients[name]
            grams = amount if unit == "g" else convert_to_grams(amount, unit, name, custom_ingredients)
            protein = grams * macros_per_100g["protein"] / 100
            carbs = grams * macros_per_100g["carbs"] / 100
            fat = grams * macros_per_100g["fat"] / 100
        else:
            macros_per_100g = fetch_usda_nutrition(name)
            if macros_per_100g is None:
                st.warning(f"Could not find nutrition for: {name}")
                continue
            grams = convert_to_grams(amount, unit, name)
            protein = grams * macros_per_100g["protein"] / 100
            carbs = grams * macros_per_100g["carbs"] / 100
            fat = grams * macros_per_100g["fat"] / 100

        ingredient_data.append({
            "ingredient": name,
            "amount": f"{amount} {unit}",
            "grams": grams,
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
        })

    if ingredient_data:
        df = get_macro_totals(ingredient_data)
        st.dataframe(df)
        pdf = generate_pdf_from_dataframe(df, title=title)
        st.download_button("📄 Export This Recipe", data=pdf, file_name=f"{title}.pdf", mime="application/pdf")