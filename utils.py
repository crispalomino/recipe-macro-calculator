import json
import os
from fpdf import FPDF
import pandas as pd
import requests

USDA_API_KEY = os.environ.get("USDA_API_KEY", "")

UNIT_CONVERSIONS = {
    "g": 1,
    "kg": 1000,
    "oz": 28.35,
    "lb": 453.6,
    "ml": 1,
    "tbsp": 15,
    "tsp": 5,
    "cup": 240,
    "slice": 25,
    "piece": 50,
    "clove": 5,
    "leaf": 1,
    "pinch": 0.36,
    "sprig": 0.5,
    "bunch": 100,
}

def convert_to_grams(amount, unit, ingredient=None, custom_ingredients=None):
    if custom_ingredients and ingredient in custom_ingredients:
        return amount * custom_ingredients[ingredient].get("density", 100)
    return amount * UNIT_CONVERSIONS.get(unit, 1)

def parse_ingredient_line(line):
    import re
    match = re.match(r"(\d+(\.\d+)?)\s*(\w+)\s*(.*)", line.strip())
    if not match:
        return 0, "g", ""
    amount = float(match.group(1))
    unit = match.group(3).lower()
    name = match.group(4).strip().lower()
    return amount, unit, name

def load_custom_ingredients():
    if os.path.exists("custom_ingredients.json"):
        with open("custom_ingredients.json", "r") as f:
            return json.load(f)
    return {}

def save_custom_ingredient(name, protein, carbs, fat, density):
    ingredients = load_custom_ingredients()
    ingredients[name.lower()] = {
        "protein": protein,
        "carbs": carbs,
        "fat": fat,
        "density": density,
    }
    with open("custom_ingredients.json", "w") as f:
        json.dump(ingredients, f, indent=2)

def fetch_usda_nutrition(query):
    if not USDA_API_KEY:
        return None
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {"api_key": USDA_API_KEY, "query": query, "pageSize": 1}
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()
        item = data["foods"][0]
        macros = {f["nutrientName"]: f["value"] for f in item["foodNutrients"]}
        return {
            "protein": macros.get("Protein", 0),
            "carbs": macros.get("Carbohydrate, by difference", 0),
            "fat": macros.get("Total lipid (fat)", 0),
        }
    except:
        return None

def get_macro_totals(ingredients):
    df = pd.DataFrame(ingredients)
    totals = df[["protein", "carbs", "fat"]].sum().to_frame().T
    totals["ingredient"] = "Total"
    return pd.concat([df, totals], ignore_index=True)

def generate_pdf_from_dataframe(df, title="Recipe"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=title, ln=1, align="C")
    for i, row in df.iterrows():
        line = f"{row.get('ingredient', '')}: {row.get('amount', '')} | {round(row.get('protein', 0), 1)}g P | {round(row.get('carbs', 0), 1)}g C | {round(row.get('fat', 0), 1)}g F"
        pdf.cell(200, 10, txt=line, ln=1)
    return pdf.output(dest="S").encode("latin-1")