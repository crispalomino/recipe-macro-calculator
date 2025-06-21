import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def convert_units_to_grams(amount, unit, custom_conversion=None):
    conversions = {
        "g": 1,
        "oz": 28.35,
        "ml": 1,
        "cup": 240,
        "tbsp": 15,
        "tsp": 5,
        "slice": 30,
        "piece": 50,
        "clove": 5,
        "leaf": 0.5,
        "pinch": 0.3,
        "sprig": 2,
        "bunch": 100,
    }
    if custom_conversion is not None:
        return amount * custom_conversion
    return amount * conversions.get(unit, 1)

def calculate_macros(ingredients):
    total = {"calories": 0, "protein": 0, "carbs": 0, "net_carbs": 0, "fat": 0, "fiber": 0}
    detailed = []
    for item in ingredients:
        grams = convert_units_to_grams(item["amount"], item["unit"], item.get("custom_conversion"))
        multiplier = grams / 100
        macros = {
            "ingredient": item["name"],
            "calories": round(item["calories"] * multiplier, 2),
            "protein": round(item["protein"] * multiplier, 2),
            "carbs": round(item["carbs"] * multiplier, 2),
            "net_carbs": round((item["carbs"] - item["fiber"]) * multiplier, 2),
            "fat": round(item["fat"] * multiplier, 2),
            "fiber": round(item["fiber"] * multiplier, 2),
        }
        for key in total:
            total[key] += macros[key]
        detailed.append(macros)
    total = {k: round(v, 2) for k, v in total.items()}
    return total, detailed

def save_recipe(data, filename="saved_recipes.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []
    existing.append(data)
    with open(filename, "w") as f:
        json.dump(existing, f, indent=4)

def load_recipes(filename="saved_recipes.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def delete_recipe(index, filename="saved_recipes.json"):
    recipes = load_recipes(filename)
    if 0 <= index < len(recipes):
        recipes.pop(index)
        with open(filename, "w") as f:
            json.dump(recipes, f, indent=4)

def load_custom_ingredients(filename="custom_ingredients.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_custom_ingredient(data, filename="custom_ingredients.json"):
    ingredients = load_custom_ingredients(filename)
    ingredients.append(data)
    with open(filename, "w") as f:
        json.dump(ingredients, f, indent=4)

def generate_nutrition_label(recipe_title, macros, detailed, servings, instructions, filename="nutrition_label.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"Nutrition Label: {recipe_title}")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Servings: {servings}")
    c.drawString(50, height - 100, "Per Serving Macros:")
    y = height - 120
    for key, value in macros.items():
        if key != "ingredient":
            c.drawString(60, y, f"{key.capitalize()}: {round(value/servings, 2)}")
            y -= 15

    y -= 10
    c.drawString(50, y, "Ingredients Breakdown:")
    y -= 20
    for item in detailed:
        c.drawString(60, y, f"{item['ingredient']}: {item['calories']} cal, {item['protein']}g P, {item['carbs']}g C, {item['fat']}g F, {item['fiber']}g Fiber")
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    if instructions:
        y -= 20
        c.drawString(50, y, "Instructions:")
        y -= 15
        for line in instructions.split("\\n"):
            c.drawString(60, y, line.strip())
            y -= 15
            if y < 50:
                c.showPage()
                y = height - 50

    c.save()
