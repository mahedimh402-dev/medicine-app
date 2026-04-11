from flask import Flask, render_template, request, jsonify
import csv
import re
from itertools import combinations

app = Flask(__name__)

# -----------------------------
# CLEAN FUNCTION
# -----------------------------
def clean(text):
    return re.sub(r"\s+", " ", text.lower().strip())

# -----------------------------
# LOAD BRAND → GENERIC
# -----------------------------
mapping = {}

with open("Bangladesh Drug Brands & Interactions - Bangladesh Drug Brands & Interactions.csv", newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        generic = clean(row["Generic Name"])
        brands = row["Popular Brand Names (Major Manufacturers)"].split(",")

        for brand in brands:
            mapping[clean(brand)] = generic

medicine_list = list(mapping.keys())

# -----------------------------
# LOAD INTERACTIONS
# -----------------------------
pair_interactions = {}

with open("Drug_Interaction_Results_Bangladesh.csv", newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        combo = clean(row["Combination (Generic A + Generic B)"])
        result = row["Result"]

        parts = combo.split("+")

        if len(parts) >= 2:
            for g1, g2 in combinations(parts, 2):
                pair_interactions[(clean(g1), clean(g2))] = result
                pair_interactions[(clean(g2), clean(g1))] = result

# -----------------------------
# CHECK FUNCTION
# -----------------------------
def check_interaction(med1, med2):
    g1 = mapping.get(clean(med1))
    g2 = mapping.get(clean(med2))

    if not g1 or not g2:
        return "❌ Medicine not found in database"

    if (g1, g2) in pair_interactions:
        return f"⚠️ {pair_interactions[(g1, g2)]}"

    return "✅ No interaction found"

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/check", methods=["POST"])
def check():
    data = request.get_json()
    med1 = data.get("med1")
    med2 = data.get("med2")

    result = check_interaction(med1, med2)
    return jsonify({"result": result})

@app.route("/suggest")
def suggest():
    query = request.args.get("q", "").lower()
    suggestions = [m for m in medicine_list if query in m]
    return jsonify(suggestions[:5])

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run()
