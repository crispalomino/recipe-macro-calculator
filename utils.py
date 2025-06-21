import json, os, requests
import pandas as pd
from fpdf import FPDF
import streamlit as st

# ────────────────────────── CONFIG ──────────────────────────
def _read_json(path, blank):         # helper
    if os.path.exists(path):
        with open(path,"r") as f:
            try: return json.load(f)
            except: pass
    return blank

# ───────────────── CUSTOM INGREDIENTS ───────────────────────
CI_PATH = "custom_ingredients.json"

def load_custom_ingredients():
    return _read_json(CI_PATH, {})

def save_custom_ingredient(name, unit, g_unit, p,c,f):
    db = load_custom_ingredients()
    db[name.lower()] = {"u":unit,"g":g_unit,"p":p,"c":c,"f":f}
    with open(CI_PATH,"w") as f: json.dump(db,f,indent=2)

# ───────────────── USDA API ─────────────────────────────────
def fetch_usda_nutrition(query):
    try:
        api_key = st.secrets["usda"]["api_key"]
        res = requests.get(
            "https://api.nal.usda.gov/fdc/v1/foods/search",
            params={"api_key": api_key,"query": query,"pageSize": 1}
        )
        if res.status_code == 429:
            st.warning("⚠️ API limit exceeded — whoa, girl, please try again tomorrow.")
            return None
        item = res.json()["foods"][0]["foodNutrients"]
        grab = lambda n: next((x["value"] for x in item if n in x["nutrientName"]), 0)
        return grab("Protein"), grab("Carbohydrate"), grab("Total lipid")
    except Exception as e:
        st.error(f"Error fetching USDA data: {e}")
        return None

# ───────────────── UNITS ────────────────────────────────────
U2G = {
    "g": 1, "oz": 28.35, "ml": 1, "cup": 240, "tbsp": 15, "tsp": 5,
    "slice": 25, "piece": 50, "clove": 5, "leaf": 1, "pinch": 0.3,
    "sprig": 0.5, "bunch": 80
}

def convert_unit_to_grams(amount, unit, name="", ci=None):
    if ci and name.lower() in ci:
        return amount * ci[name.lower()]["g"]
    return amount * U2G.get(unit, 1)

# ───────────────── MACRO CALC ──────────────────────────────
def calc_macros(ing_rows, servings, ci):
    rows = []
    tot = {"Protein": 0, "Carbs": 0, "Fat": 0}
    for r in ing_rows:
        if not r["name"]: continue
        g = convert_unit_to_grams(r["amt"], r["unit"], r["name"], ci)
        p = g * r["p"] / 100
        c = g * r["c"] / 100
        f = g * r["f"] / 100
        rows.append(dict(
            Ingredient=r["name"],
            Amount=f'{r["amt"]} {r["unit"]}',
            Grams=g,
            Protein=round(p, 2),
            Carbs=round(c, 2),
            Fat=round(f, 2)
        ))
        tot["Protein"] += p
        tot["Carbs"] += c
        tot["Fat"] += f
    return pd.DataFrame(rows), {k: round(v, 2) for k, v in tot.items()}

# ───────────────── PDF ─────────────────────────────────────
def export_recipe_pdf(title, df, tot, serv):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(190, 9, txt=title, ln=1, align="C")
    pdf.ln(2)
    for _, r in df.iterrows():
        pdf.cell(190, 8, txt=(
            f'{r["Ingredient"]}: {r["Amount"]} '
            f'| P {r["Protein"]}g C {r["Carbs"]}g F {r["Fat"]}g'
        ), ln=1)
    pdf.ln(2)
    pdf.cell(190, 8, txt=f'Total: P {tot["Protein"]}g  C {tot["Carbs"]}g  F {tot["Fat"]}g', ln=1)
    pdf.cell(190, 8, txt=(
        f'Per serving ({serv}): '
        f'P {tot["Protein"] / serv:.1f}g  '
        f'C {tot["Carbs"] / serv:.1f}g  '
        f'F {tot["Fat"] / serv:.1f}g'
    ), ln=1)
    return pdf.output(dest="S").encode("latin-1")

# ───────────────── SAVED RECIPES ───────────────────────────
RCP_PATH = "saved_recipes.json"

def load_saved_recipes():
    return _read_json(RCP_PATH, {})

def save_recipe(title, servings, rows):
    db = load_saved_recipes()
    db[title] = {"serv": servings, "rows": rows}
    with open(RCP_PATH, "w") as f:
        json.dump(db, f, indent=2)

def delete_recipe(title):
    db = load_saved_recipes()
    if title in db:
        del db[title]
        with open(RCP_PATH, "w") as f:
            json.dump(db, f, indent=2)