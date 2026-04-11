from flask import Flask, render_template, request, jsonify
import csv
import re
from itertools import combinations

app = Flask(__name__)

# -----------------------------
# CLEAN
# -----------------------------
def clean(text):
    text = text.lower().strip()
    text = re.sub(r"\s*\+\s*", "+", text)
    text = re.sub(r"\s+", " ", text)
    return text

# -----------------------------
# SMART SPLIT
# -----------------------------
def smart_split(combo):
    combo = combo.lower()

    parts = []
    current = ""
    bracket_level = 0

    for char in combo:
        if char == "(":
            bracket_level += 1
        elif char == ")":
            bracket_level -= 1

        if char == "+" and bracket_level == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += char

    if current:
        parts.append(current.strip())

    return [clean(p) for p in parts if p.strip()]

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

# -----------------------------
# LOAD INTERACTIONS (EXACT YOUR LOGIC)
# -----------------------------
combo_interactions = {}
pair_interactions = {}

with open("Drug_Interaction_Results_Bangladesh.csv", newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        combo = clean(row["Combination (Generic A + Generic B)"])
        result = row["Result"]
        reason = row["Reasoning / Warning"]

        combo_interactions[combo] = (result, reason)

        parts = smart_split(combo)

        if len(parts) >= 2:
            for g1, g2 in combinations(parts, 2):
                pair_interactions[(g1, g2)] = (result, reason)
                pair_interactions[(g2, g1)] = (result, reason)

# -----------------------------
# CORE CHECK (YOUR LOGIC)
# -----------------------------
def check_interaction(med1, med2):
    g1 = mapping.get(clean(med1))
    g2 = mapping.get(clean(med2))

    if not g1 or not g2:
        return "❌ Medicine not found in database"

    full_combo = "+".join(sorted([g1, g2]))

    if full_combo in combo_interactions:
        result, reason = combo_interactions[full_combo]
        return f"{result} | {reason}"

    parts1 = smart_split(g1)
    parts2 = smart_split(g2)

    for p1 in parts1:
        for p2 in parts2:
            if (p1, p2) in pair_interactions:
                result, reason = pair_interactions[(p1, p2)]
                return f"{result} | {reason}"

    return "✅ No interaction found"

# -----------------------------
# FLASK ROUTES
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
    return jsonify([m for m in mapping.keys() if query in m][:5])

if __name__ == "__main__":
    app.run()
