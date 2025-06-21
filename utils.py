import json
import os

def get_macro_totals(ingredients):
    # Placeholder - real logic would sum based on macros
    return {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}

def generate_pdf_from_dataframe(df, title="Macros"):
    # Placeholder - PDF logic here
    pass

def load_saved_recipes():
    if os.path.exists("saved_recipes.json"):
        with open("saved_recipes.json", "r") as f:
            return json.load(f)
    return []

def save_recipe(recipe):
    recipes = load_saved_recipes()
    recipes.append(recipe)
    with open("saved_recipes.json", "w") as f:
        json.dump(recipes, f, indent=2)

def delete_recipe(index):
    recipes = load_saved_recipes()
    if 0 <= index < len(recipes):
        recipes.pop(index)
        with open("saved_recipes.json", "w") as f:
            json.dump(recipes, f, indent=2)

def duplicate_recipe(index):
    recipes = load_saved_recipes()
    if 0 <= index < len(recipes):
        copy = recipes[index].copy()
        copy["title"] += " (Copy)"
        recipes.append(copy)
        with open("saved_recipes.json", "w") as f:
            json.dump(recipes, f, indent=2)

def load_custom_ingredients():
    if os.path.exists("custom_ingredients.json"):
        with open("custom_ingredients.json", "r") as f:
            return json.load(f)
    return []

def add_custom_ingredient(name, unit, grams_per_unit, calories, protein, carbs, fat):
    ingredients = load_custom_ingredients()
    ingredients.append({
        "name": name,
        "unit": unit,
        "grams_per_unit": grams_per_unit,
        "calories": calories,
        "protein": protein,
        "carbs": carbs,
        "fat": fat
    })
    with open("custom_ingredients.json", "w") as f:
        json.dump(ingredients, f, indent=2)

def convert_to_grams(amount, unit, name, custom_ingredients):
    for ing in custom_ingredients:
        if ing["name"].lower() == name.lower() and ing["unit"] == unit:
            return amount * ing["grams_per_unit"]
    return amount  # fallback
