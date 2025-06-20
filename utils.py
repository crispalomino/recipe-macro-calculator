import requests
from fpdf import FPDF

API_KEY = "wp4IKeeh6SmUmDyPkFieEDVcKRPH7e8cbAglRick"
BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# Default gram equivalents (can be overridden by user)
UNIT_CONVERSIONS = {
    "g": 1,
    "oz": 28.35,
    "ml": 1,
    "cup": 240,
    "tbsp": 15,
    "tsp": 5,
    "slice": None,
    "piece": None,
    "clove": None,
    "leaf": None,
    "pinch": None,
    "sprig": None,
    "bunch": None
}

def convert_to_grams(weight, unit, override=None):
    if override and override > 0:
        return override * weight
    factor = UNIT_CONVERSIONS.get(unit.lower(), 1)
    return weight * factor if factor else 0

def get_macro_totals(ingredients, weights, units, overrides):
    total = {"Protein": 0, "Fat": 0, "Carbohydrate": 0, "Fiber": 0, "Net Carbs": 0, "Calories": 0}
    detail = []

    for name, wt, unit, override in zip(ingredients, weights, units, overrides):
        grams = convert_to_grams(wt, unit, override)
        macros = get_macros_for_ingredient(name, grams)
        for k in total:
            total[k] += macros[k]
        detail.append({
            "name": name,
            "input_weight": wt,
            "unit": unit,
            "grams": grams,
            "macros": macros
        })

    return total, detail

def get_macros_for_ingredient(ingredient_name, weight_g):
    params = {
        "api_key": API_KEY,
        "query": ingredient_name,
        "pageSize": 1,
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    try:
        nutrients = data["foods"][0]["foodNutrients"]
    except (KeyError, IndexError):
        return {k: 0 for k in ["Protein", "Fat", "Carbohydrate", "Fiber", "Net Carbs", "Calories"]}

    macro_map = {
        "Protein": 1003,
        "Fat": 1004,
        "Carbohydrate": 1005,
        "Fiber": 1079,
        "Calories": 1008,
    }

    result = {}
    for name, code in macro_map.items():
        value = next((n["value"] for n in nutrients if n["nutrientId"] == code), 0)
        result[name] = value * weight_g / 100

    result["Net Carbs"] = max(result["Carbohydrate"] - result["Fiber"], 0)
    return result

def generate_pdf(title, ingredients, total_macros, servings, filename="output.pdf", instructions=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(200, 10, txt=title, ln=True, align="C")

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, txt="Nutrition Facts (per serving)", ln=True)
    pdf.set_font("Helvetica", size=11)

    pdf.cell(200, 7, txt=f"Calories: {round(total_macros['Calories'] / servings, 1)} kcal", ln=True)
    pdf.cell(200, 7, txt=f"Protein: {round(total_macros['Protein'] / servings, 1)} g", ln=True)
    pdf.cell(200, 7, txt=f"Fat: {round(total_macros['Fat'] / servings, 1)} g", ln=True)
    pdf.cell(200, 7, txt=f"Carbs: {round(total_macros['Carbohydrate'] / servings, 1)} g", ln=True)
    pdf.cell(200, 7, txt=f"Fiber: {round(total_macros['Fiber'] / servings, 1)} g", ln=True)
    pdf.cell(200, 7, txt=f"Net Carbs: {round(total_macros['Net Carbs'] / servings, 1)} g", ln=True)

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(200, 10, txt="Ingredients", ln=True)
    pdf.set_font("Helvetica", size=10)

    for item in ingredients:
        label = f"{item['name']} ({item['input_weight']} {item['unit']} → {round(item['grams'], 1)}g)"
        pdf.multi_cell(0, 6, label, ln=True)

    if instructions:
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(200, 10, txt="Instructions", ln=True)
        pdf.set_font("Helvetica", size=10)
        for line in instructions.strip().split("\n"):
            pdf.multi_cell(0, 6, line)

    pdf.output(filename)

def generate_pdf_from_dataframe(df, title, filename="comparison.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(200, 10, txt=title, ln=True, align="C")

    pdf.set_font("Helvetica", "B", 9)
    col_width = 38
    row_height = 8

    pdf.set_fill_color(220, 220, 220)
    pdf.cell(col_width, row_height, "Title", border=1, fill=True)
    for col in df.columns:
        pdf.cell(col_width, row_height, col[:15], border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", size=9)
    for index, row in df.iterrows():
        pdf.cell(col_width, row_height, index[:15], border=1)
        for val in row:
            pdf.cell(col_width, row_height, str(round(val, 2)), border=1)
        pdf.ln()

    pdf.output(filename)