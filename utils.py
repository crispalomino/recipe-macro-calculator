import json
import os
import requests
import pandas as pd
from fpdf import FPDF
from io import BytesIO
import streamlit as st

# ────── File paths ──────
CUSTOM_FILE = "custom_ingredients.json"
SAVED_FILE = "saved_recipes.json"

# ────── Loaders & Savers ──────
def load_custom_ingredients():
    if os.path.exists(CUSTOM_FILE):
        with open(CUSTOM_FILE, "r") as f:
            return json.load(f)
    return {}

def save_custom_ingredient(name, unit, g_per_unit, p, c, f):
    data = load_custom_ingredients()
    data[name.lower()] = {
        "unit": unit,
        "g_per_unit": g_per_unit,
        "p": p,
        "c": c,
        "f": f
    }
    with open(CUSTOM_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_saved_recipes():
    if os.path.exists(SAVED_FILE):
        with open(SAVED_FILE, "r") as f:
            return json.load(f)
    return {}

def save_recipe(title, servings, ingredients, instructions=""):
    data = load_saved_recipes()
    data[title] = {
        "servings": servings,
        "ingredients": ingredients,
        "instructions": instructions
    }
    with open(SAVED_FILE, "w") as f:
        json.dump(data, f, indent=2)

def delete_recipe(title):
    data = load_saved_recipes()
    if title in data:
        del data[title]
        with open(SAVED_FILE, "w") as f:
            json.dump(data, f, indent=2)

# ────── Unit Conversion ──────
UNIT_CONVERSIONS = {
    "g": 1,
    "oz": 28.35,
    "ml": 1,
    "cup": 240,
    "tbsp": 15,
    "tsp": 5,
    "slice": 30,
    "piece": 50,
    "clove": 5,
    "leaf": 2,
    "pinch": 0.3,
    "sprig": 1,
    "bunch": 25
}

def convert_unit_to_grams(unit, amount, custom_data=None):
    if custom_data and unit == custom_data.get("unit"):
        return amount * custom_data.get("g_per_unit", 1)
    return amount * UNIT_CONVERSIONS.get(unit, 1)

# ────── USDA Lookup ──────
def fetch_usda_nutrition(query):
    try:
        api_key = st.secrets["api_key"]
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={query}&api_key={api_key}&pageSize=1"
        res = requests.get(url)
        st.write(f"Querying USDA for: {query}")  # Debug output

        if res.status_code == 429:
            st.warning("API limit exceeded — whoa, girl, please try again tomorrow.")
            return None

        data = res.json()
        if "foods" not in data or not data["foods"]:
            st.warning(f"No USDA match found for: {query}")
            return None

        food = data["foods"][0]
        p = next((x["value"] for x in food["foodNutrients"] if x["nutrientName"] == "Protein"), 0.0)
        c = next((x["value"] for x in food["foodNutrients"] if x["nutrientName"] == "Carbohydrate, by difference"), 0.0)
        f = next((x["value"] for x in food["foodNutrients"] if x["nutrientName"] == "Total lipid (fat)"), 0.0)
        return p, c, f
    except Exception as e:
        st.error(f"Error during USDA lookup: {e}")
        return None

# ────── Macro Calculation ──────
def calc_macros(ingredients, servings, custom_data):
    rows = []
    total = {"calories": 0, "protein": 0, "carbs": 0, "net_carbs": 0, "fat": 0, "fiber": 0}
    for ing in ingredients:
        name = ing["name"]
        amt = ing["amt"]
        unit = ing["unit"]
        p = ing["p"]
        c = ing["c"]
        f = ing["f"]
        grams = convert_unit_to_grams(unit, amt, custom_data.get(name.lower()))
        protein = p * grams / 100
        carbs = c * grams / 100
        fat = f * grams / 100
        cal = 4 * protein + 4 * carbs + 9 * fat
        rows.append({
            "Ingredient": name,
            "Amount": f"{amt} {unit}",
            "Grams": round(grams, 2),
            "Protein": round(protein, 2),
            "Carbs": round(carbs, 2),
            "Fat": round(fat, 2),
            "Calories": round(cal, 2)
        })
        total["calories"] += cal
        total["protein"] += protein
        total["carbs"] += carbs
        total["fat"] += fat
        total["net_carbs"] += carbs  # Adjust later if fiber added
    return pd.DataFrame(rows), {k: round(v, 2) for k, v in total.items()}

# ────── PDF Export ──────
def export_recipe_pdf(title, df, totals, servings, instructions):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, title, ln=1)

    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 10, f"Servings: {servings}\n\nInstructions:\n{instructions}\n")

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Ingredients", ln=1)

    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        line = f"{row['Ingredient']}: {row['Amount']} ({row['Grams']}g) | P: {row['Protein']}g, C: {row['Carbs']}g, F: {row['Fat']}g, Cal: {row['Calories']}"
        pdf.multi_cell(0, 8, line)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Total Macros", ln=1)
    pdf.set_font("Arial", "", 10)
    for k, v in totals.items():
        pdf.cell(0, 8, f"{k.capitalize()}: {v}", ln=1)

    output = BytesIO()
    pdf.output(output)
    return output.getvalue()
