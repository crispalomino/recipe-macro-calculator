import streamlit as st
from utils import (
    calculate_macros, save_recipe, load_recipes,
    delete_recipe, load_custom_ingredients,
    save_custom_ingredient, generate_nutrition_label
)

st.set_page_config(page_title="Recipe Macro Calculator", layout="wide")
st.title("📊 Recipe Macro Calculator")

# Debug visual
st.markdown("🟢 App loaded successfully.")

# Scaling buttons
scaling_factor = st.radio("Scale servings by:", [1, 0.5, 2, 4], horizontal=True)
servings = st.number_input("How many servings?", min_value=1, value=4)
scaled_servings = max(1, int(servings * scaling_factor))

# Load custom ingredients
custom_ingredients = load_custom_ingredients()

# Sidebar form for custom ingredients
st.sidebar.header("➕ Add Custom Ingredient")
with st.sidebar.form("custom_ingredient_form"):
    ci_name = st.text_input("Name")
    ci_cals = st.number_input("Calories (per 100g)", step=0.01)
    ci_protein = st.number_input("Protein (g)", step=0.01)
    ci_carbs = st.number_input("Carbs (g)", step=0.01)
    ci_fat = st.number_input("Fat (g)", step=0.01)
    ci_fiber = st.number_input("Fiber (g)", step=0.01)
    if st.form_submit_button("Add"):
        save_custom_ingredient({
            "name": ci_name,
            "calories": ci_cals,
            "protein": ci_protein,
            "carbs": ci_carbs,
            "fat": ci_fat,
            "fiber": ci_fiber
        })
        st.sidebar.success(f"{ci_name} added!")

# Recipe form
st.subheader("🍽️ Enter Recipe Details")
title = st.text_input("Recipe Title")
num_ingredients = st.number_input("How many ingredients?", 1, 50, 5)
ingredients = []

unit_options = ["g", "oz", "ml", "cup", "tbsp", "tsp", "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"]

for i in range(num_ingredients):
    cols = st.columns([3, 1, 1, 1])
    name = cols[0].text_input(f"Ingredient {i+1} Name")
    amount = cols[1].number_input(f"Amount", key=f"a{i}")
    unit = cols[2].selectbox("Unit", unit_options, key=f"u{i}")

    if name in [ci["name"] for ci in custom_ingredients]:
        ci = next(c for c in custom_ingredients if c["name"] == name)
        calories = ci["calories"]
        protein = ci["protein"]
        carbs = ci["carbs"]
        fat = ci["fat"]
        fiber = ci["fiber"]
    else:
        calories = cols[3].number_input("Calories / 100g", key=f"c{i}")
        protein = st.number_input("Protein (g)", key=f"p{i}")
        carbs = st.number_input("Carbs (g)", key=f"carb{i}")
        fat = st.number_input("Fat (g)", key=f"f{i}")
        fiber = st.number_input("Fiber (g)", key=f"fib{i}")

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

# Instructions
instructions = st.text_area("Recipe Instructions")

# Calculate macros
if st.button("📋 Calculate Macros"):
    total, breakdown = calculate_macros(ingredients)
    st.success(f"Total Macros for Full Recipe:")
    st.write(total)

    per_serving = {k: round(v / scaled_servings, 2) for k, v in total.items()}
    st.info(f"Per Serving (for {scaled_servings} servings):")
    st.write(per_serving)

    st.subheader("Per Ingredient Breakdown:")
    for item in breakdown:
        st.write(item)

    if st.button("💾 Save Recipe"):
        save_recipe({
            "title": title,
            "ingredients": ingredients,
            "macros": total,
            "instructions": instructions,
            "servings": scaled_servings
        })
        st.success("Recipe saved!")

    if st.button("📤 Export This Recipe"):
        generate_nutrition_label(title, total, breakdown, scaled_servings, instructions)
        with open("nutrition_label.pdf", "rb") as f:
            st.download_button("Download PDF", f, file_name=f"{title}.pdf")

# Load and manage saved recipes
st.subheader("📚 View Saved Recipes")
recipes = load_recipes()
for idx, r in enumerate(recipes):
    with st.expander(r["title"]):
        st.write(f"Servings: {r.get('servings', '?')}")
        st.write("Instructions:", r.get("instructions", ""))
        st.write("Macros:", r["macros"])
        if st.button("🗑 Delete", key=f"del{idx}"):
            delete_recipe(idx)
            st.experimental_rerun()
