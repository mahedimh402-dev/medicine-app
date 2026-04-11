from flask import Flask, render_template, request, jsonify
import csv
import re

app = Flask(__name__)

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
# LOAD INTERACTIONS (SIMPLE & STABLE)
# -----------------------------
pair_interactions = {}

with open("Drug_Interaction_Results_Bangladesh.csv", newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        combo = clean(row["Combination (Generic A + Generic B)"])
        result = row["Result"]

        parts = combo.split("+")
        parts = [clean(p) for p in parts]

        if len(parts) >= 2:
            g1 = parts[0]
            g2 = parts[1]

            pair_interactions[(g1, g2)] = result
            pair_interactions[(g2, g1)] = result

# -----------------------------
# CHECK FUNCTION
# -----------------------------
def check_interaction(med1, med2):
    g1 = mapping.get(clean(med1))
    g2 = mapping.get(clean(med2))

    if not g1 or not g2:
        return "❌ Medicine not found"

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
    return jsonify({"result": check_interaction(data["med1"], data["med2"])})

@app.route("/suggest")
def suggest():
    query = request.args.get("q", "").lower()
    return jsonify([m for m in medicine_list if query in m][:5])

if __name__ == "__main__":
    app.run()
