# Recipe Macro Calculator

A web app built with Streamlit to calculate nutrition macros from custom or USDA ingredients. You can:

- Enter recipe ingredients
- Use USDA lookup or custom entries
- View totals and export as PDF

## Setup

1. Install requirements: `pip install -r requirements.txt`
2. Create `.streamlit/secrets.toml` with:
```toml
USDA_API_KEY = "your_api_key_here"
```
3. Run with: `streamlit run app.py`