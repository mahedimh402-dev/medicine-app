from flask import Flask, render_template, request
import csv
import re
from itertools import combinations

app = Flask(__name__)

# -----------------------------
# CLEAN FUNCTION
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
# LOAD INTERACTIONS
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
# MAIN LOGIC FUNCTION
# -----------------------------
def check_interaction(med1, med2):
    med1 = clean(med1)
    med2 = clean(med2)

    g1 = mapping.get(med1)
    g2 = mapping.get(med2)

    if not g1 or not g2:
        return "❌ Medicine not found in database."

    # FULL COMBO CHECK
    full_combo = "+".join(sorted([g1, g2]))

    if full_combo in combo_interactions:
        result, reason = combo_interactions[full_combo]
        return f"⚠️ {result} — {reason}"

    # PAIRWISE CHECK
    parts1 = smart_split(g1)
    parts2 = smart_split(g2)

    messages = []

    for p1 in parts1:
        for p2 in parts2:
            if (p1, p2) in pair_interactions:
                result, reason = pair_interactions[(p1, p2)]
                messages.append(f"{p1} + {p2}: {result} ({reason})")

    if messages:
        return "<br>".join(messages)

    return "✅ No interaction found."

# -----------------------------
# FLASK ROUTE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    result = ""

    if request.method == "POST":
        med1 = request.form.get("med1")
        med2 = request.form.get("med2")

        result = check_interaction(med1, med2)

    return render_template("index.html", result=result)

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)