import streamlit as st
from utils import get_macro_totals, generate_pdf, generate_pdf_from_dataframe
import tempfile
import json
import os
import pandas as pd

st.set_page_config(page_title="Recipe Macro Calculator", layout="centered")
st.title("🥗 Recipe Macro Calculator")

SAVED_RECIPES_FILE = "saved_recipes.json"
UNIT_OPTIONS = [
    "g", "oz", "ml", "cup", "tbsp", "tsp",
    "slice", "piece", "clove", "leaf", "pinch", "sprig", "bunch"
]

def load_recipes():
    if not os.path.exists(SAVED_RECIPES_FILE):
        return []
    with open(SAVED_RECIPES_FILE, "r") as f:
        return [json.loads(line) for line in f if line.strip()]

def save_all_recipes(recipes):
    with open(SAVED_RECIPES_FILE, "w") as f:
        for r in recipes:
            f.write(json.dumps(r) + "\n")

def save_recipe(recipe_data, overwrite=False):
    recipes = load_recipes()
    if overwrite:
        recipes = [r for r in recipes if r.get("title") != recipe_data["title"]]
    recipes.append(recipe_data)
    save_all_recipes(recipes)

def build_recipe_object(title, servings, tags, category, ingredients, favorite=False, instructions="", base_servings=None):
    return {
        "title": title.strip(),
        "servings": servings,
        "base_servings": base_servings if base_servings else servings,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "category": category.strip(),
        "favorite": favorite,
        "instructions": instructions.strip(),
        "ingredients": ingredients
    }

def auto_increment_title(base_title, existing_titles):
    count = 1
    while True:
        new_title = f"{base_title} ({count})"
        if new_title not in existing_titles:
            return new_title
        count += 1

recipes = load_recipes()

# ✅ FIXED: safely extract categories
categories = sorted(set(
    r.get("category", "Uncategorized") if isinstance(r, dict) else "Uncategorized"
    for r in recipes
))
categories = ["All"] + categories

selected_category = st.selectbox("📁 Filter by Category", categories)
show_favorites_only = st.checkbox("⭐ Show Favorites Only")

# ✅ FIXED: filter only valid dicts
filtered = [
    r for r in recipes if isinstance(r, dict)
    and (selected_category == "All" or r.get("category") == selected_category)
    and (not show_favorites_only or r.get("favorite", False))
]

search_query = st.text_input("🔍 Search by title or tag")
if search_query:
    filtered = [
        r for r in filtered
        if isinstance(r, dict) and (
            search_query.lower() in r.get("title", "").lower() or
            any(search_query.lower() in tag.lower() for tag in r.get("tags", []))
        )
    ]

# ✅ FIXED: avoid type error if recipe malformed
recipe_titles = [r["title"] for r in filtered if isinstance(r, dict) and "title" in r]
selected_title = st.selectbox("📂 Load a Recipe", [""] + recipe_titles)
loaded_recipe = next((r for r in recipes if isinstance(r, dict) and r.get("title") == selected_title), None)

default_title = loaded_recipe["title"] if loaded_recipe else "My Healthy Recipe"
default_servings = loaded_recipe["servings"] if loaded_recipe else 1
base_servings = loaded_recipe.get("base_servings", default_servings) if loaded_recipe else default_servings
default_ingredients = loaded_recipe.get("ingredients", []) if loaded_recipe else []
default_tags = ", ".join(loaded_recipe.get("tags", [])) if loaded_recipe else ""
default_category = loaded_recipe.get("category", "Uncategorized") if loaded_recipe else ""
default_fav = loaded_recipe.get("favorite", False) if loaded_recipe else False
default_instructions = loaded_recipe.get("instructions", "") if loaded_recipe else ""
initial_count = len(default_ingredients) if default_ingredients else 5

with st.form("recipe_form"):
    title = st.text_input("Recipe Title", default_title)
    servings = st.number_input("Servings", min_value=1, value=default_servings)
    category = st.text_input("Category", value=default_category)
    tags = st.text_input("Tags (comma-separated)", default_tags)
    favorite = st.checkbox("⭐ Mark as Favorite", value=default_fav)
    instructions = st.text_area("Instructions / Notes", value=default_instructions)

    st.markdown("### Ingredients")
    num_ingredients = st.number_input("How many ingredients?", min_value=1, max_value=25, value=initial_count)
    scaling_factor = servings / base_servings if base_servings else 1

    ingredients = []
    for i in range(int(num_ingredients)):
        st.markdown(f"#### Ingredient {i+1}")
        col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
        name = col1.text_input("Name", value=default_ingredients[i]["name"] if i < len(default_ingredients) else "", key=f"name_{i}")
        weight = col2.number_input("Amount", min_value=0.0,
                                   value=round(default_ingredients[i]["weight"], 2) * scaling_factor if i < len(default_ingredients) else 0.0, key=f"wt_{i}")
        unit = col3.selectbox("Unit", UNIT_OPTIONS,
                              index=UNIT_OPTIONS.index(default_ingredients[i]["unit"]) if i < len(default_ingredients) else 0, key=f"unit_{i}")
        override = col4.number_input("Override: 1 unit = ? g", min_value=0.0,
                                     value=default_ingredients[i].get("override", 0.0) if i < len(default_ingredients) else 0.0, key=f"override_{i}")

        if name:
            ingredients.append({
                "name": name,
                "weight": weight,
                "unit": unit,
                "override": override if override > 0 else None
            })

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    submitted = col1.form_submit_button("✅ Calculate")
    save = col2.form_submit_button("💾 Save")
    save_as = col3.form_submit_button("📝 Save As New")
    duplicate = col4.form_submit_button("📎 Duplicate")

if save or save_as:
    recipe_obj = build_recipe_object(
        title, servings, tags, category, ingredients, favorite, instructions, base_servings
    )
    save_recipe(recipe_obj, overwrite=not save_as)
    st.success("✅ Saved!" if not save_as else "✅ Saved as new!")
    st.experimental_rerun()

if duplicate and loaded_recipe:
    existing_titles = {r["title"] for r in recipes}
    new_title = auto_increment_title(loaded_recipe["title"], existing_titles)
    new_recipe = loaded_recipe.copy()
    new_recipe["title"] = new_title
    save_recipe(new_recipe)
    st.success(f"✅ Duplicated as: {new_title}")
    st.experimental_rerun()

if loaded_recipe and st.button("🗑 Delete This Recipe"):
    recipes = [r for r in recipes if r.get("title") != loaded_recipe["title"]]
    save_all_recipes(recipes)
    st.success(f"Deleted: {loaded_recipe['title']}")
    st.experimental_rerun()

if submitted:
    try:
        names = [i["name"] for i in ingredients]
        weights = [i["weight"] for i in ingredients]
        units = [i["unit"] for i in ingredients]
        overrides = [i.get("override") for i in ingredients]

        total_macros, detail = get_macro_totals(names, weights, units, overrides)

        st.markdown("## 🧾 Per Ingredient Macros")
        for item in detail:
            st.markdown(f"**{item['name']} ({item['input_weight']} {item['unit']} → {round(item['grams'], 1)}g):**")
            st.text(", ".join([
                f"{k}: {round(v, 2)}g" if k != "Calories" else f"{k}: {round(v, 2)} kcal"
                for k, v in item['macros'].items()
            ]))

        st.markdown("## 📊 Total Macros (Full Recipe)")
        for k, v in total_macros.items():
            st.write(f"{k}: {round(v, 2)} {'kcal' if k == 'Calories' else 'g'}")

        st.markdown(f"## 🍽 Per Serving (/{servings})")
        for k, v in total_macros.items():
            st.write(f"{k}: {round(v / servings, 2)} {'kcal' if k == 'Calories' else 'g'}")

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        generate_pdf(title, detail, total_macros, servings, filename=tmp.name, instructions=instructions)

        with open(tmp.name, "rb") as f:
            st.download_button("📄 Export This Recipe", f, file_name=f"{title}_nutrition.pdf")

    except Exception as e:
        st.error(f"Error during calculation: {str(e)}")
