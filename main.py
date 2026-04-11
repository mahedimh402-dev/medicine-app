from flask import Flask, render_template, request, jsonify
import csv
import re
from itertools import combinations
from fuzzywuzzy import process

app = Flask(__name__)

# -----------------------------
# CLEAN TEXT
# -----------------------------
def clean(text):
    return re.sub(r"\s+", " ", text.lower().strip())

# -----------------------------
# LOAD BRAND → GENERIC MAP
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
# LOAD INTERACTIONS (FIXED)
# -----------------------------
pair_interactions = {}

with open("Drug_Interaction_Results_Bangladesh.csv", newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        combo = clean(row["Combination (Generic A + Generic B)"])
        result = row["Result"]

        parts = re.split(r"\+|and|,|/", combo)
        parts = [clean(p) for p in parts if p.strip()]

        if len(parts) >= 2:
            for i in range(len(parts)):
                for j in range(i + 1, len(parts)):
                    g1 = parts[i]
                    g2 = parts[j]

                    pair_interactions[(g1, g2)] = result
                    pair_interactions[(g2, g1)] = result

# -----------------------------
# AUTO CORRECTION
# -----------------------------
def correct_medicine(name):
    name = clean(name)

    if name in medicine_list:
        return name

    match, score = process.extractOne(name, medicine_list)

    if score >= 75:
        return match

    return None

# -----------------------------
# CHECK INTERACTION
# -----------------------------
def check_interaction(med1, med2):
    g1 = correct_medicine(med1)
    g2 = correct_medicine(med2)

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
