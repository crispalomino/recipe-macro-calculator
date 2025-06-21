import streamlit as st
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

st.set_page_config(page_title="Recipe Macro Calculator", layout="centered")

st.title("📊 Recipe Macro Calculator")

# Load data
custom_data = load_custom_ingredients()
saved = load_saved_recipes()
units = ["g", "oz", "ml", "cup", "tbsp", "tsp", "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"]

# Sidebar – Add custom ingredient
st.sidebar.header("➕ Add Custom Ingredient")
with st.sidebar.form("add_custom"):
    new_name = st.text_input("Name").strip()
    unit = st.selectbox("Unit", units, key="custom_unit")
    g_per_unit = st.number_input("Grams per unit", min_value=0.1)
    p = st.number_input("Protein per 100g", min_value=0.0)
    c = st.number_input("Carbs per 100g", min_value=0.0)
    f = st.number_input("Fat per 100g", min_value=0.0)
    submit_custom = st.form_submit_button("Add")
    if submit_custom and new_name:
        save_custom_ingredient(new_name, unit, g_per_unit, p, c, f)
        st.sidebar.success(f"Added: {new_name}")

# Recipe setup
title = st.text_input("📘 Recipe Title")
servings = st.number_input("🍽 Number of Servings", value=1, min_value=1)

num_ingredients = st.number_input("Number of Ingredients", value=5, min_value=1, step=1)

ingredients = []
st.subheader("🧾 Ingredients")

for i in range(int(num_ingredients)):
    cols = st.columns([3, 2, 2, 2, 2, 2])
    name = cols[0].text_input("Ingredient", key=f"name_{i}")
    amt = cols[1].number_input("Amt", key=f"amt_{i}", min_value=0.0)
    unit = cols[2].selectbox("Unit", units, key=f"unit_{i}")
    p = cols[3].number_input("P/100g", key=f"p_{i}", value=0.0)
    c = cols[4].number_input("C/100g", key=f"c_{i}", value=0.0)
    f = cols[5].number_input("F/100g", key=f"f_{i}", value=0.0)

    # Autofill if macros are blank
    if name and amt > 0 and unit:
        if (p == 0.0 or c == 0.0 or f == 0.0) and name.lower() not in custom_data:
            result = fetch_usda_nutrition(name)
            if isinstance(result, tuple):
                p, c, f = result
                st.session_state[f"p_{i}"] = p
                st.session_state[f"c_{i}"] = c
                st.session_state[f"f_{i}"] = f
                st.caption(f"📡 USDA fetched: P={p} C={c} F={f}")
            elif isinstance(result, str):
                st.warning(result)

    if name and amt:
        ingredients.append({
            "name": name,
            "amt": amt,
            "unit": unit,
            "p": p,
            "c": c,
            "f": f
        })

# Instructions
instructions = st.text_area("📋 Instructions (optional)")

# Calculate
if st.button("Calculate Macros") and ingredients:
    df, totals = calc_macros(ingredients, servings, custom_data)
    st.success("✅ Macro Breakdown:")
    st.dataframe(df)
    st.subheader("Total Macros (for full recipe):")
    st.write(totals)

    st.subheader("Per Serving:")
    if servings:
        per = {k: round(v / servings, 2) for k, v in totals.items()}
        st.write(per)

    st.download_button(
        label="📥 Export This Recipe",
        data=export_recipe_pdf(title, df, totals, servings, instructions),
        file_name=f"{title.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

# Save
if st.button("💾 Save This Recipe"):
    if title and ingredients:
        save_recipe(title, servings, ingredients, instructions)
        st.success("Recipe saved.")

# Sidebar – View recipes
st.sidebar.header("📂 Load or Manage Recipes")
selected = st.sidebar.selectbox("📑 View Saved Recipe", [""] + list(saved.keys()))
if selected:
    data = saved[selected]
    st.sidebar.write(f"🍽 Servings: {data['servings']}")
    st.sidebar.write(f"🧾 Ingredients: {len(data['ingredients'])}")
    if st.sidebar.button("❌ Delete"):
        delete_recipe(selected)
        st.sidebar.success("Deleted. Refresh to update.")
