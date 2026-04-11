from flask import Flask, render_template, request, jsonify
import csv
import difflib

app = Flask(__name__)

# -----------------------------
# LOAD DATA
# -----------------------------
brand_to_generic = {}
interactions = {}
medicine_list = []

with open("brand_generic_interactions.csv", newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        brand = row["Brand Name"].strip().lower()
        generic = row["Generic Name"].strip().lower()
        medicine_list.append(brand)
        brand_to_generic[brand] = generic

# Remove duplicates
medicine_list = list(set(medicine_list))

# Load interaction pairs (you must have Drug1, Drug2, Severity)
with open("drug_interactions.csv", newline='', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        d1 = row["Drug1"].strip().lower()
        d2 = row["Drug2"].strip().lower()
        severity = row["Severity"].strip().lower()

        interactions[(d1, d2)] = severity
        interactions[(d2, d1)] = severity


# -----------------------------
# SPELL CORRECTION
# -----------------------------
def correct_name(name):
    matches = difflib.get_close_matches(name.lower(), medicine_list, n=1, cutoff=0.5)
    return matches[0] if matches else name.lower()


# -----------------------------
# ROUTES
# -----------------------------
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/suggest')
def suggest():
    query = request.args.get('q', '').lower()
    suggestions = [m for m in medicine_list if query in m][:5]
    return jsonify(suggestions)


@app.route('/check', methods=['POST'])
def check():
    med1 = request.form['med1']
    med2 = request.form['med2']

    # Spell correction
    med1_corrected = correct_name(med1)
    med2_corrected = correct_name(med2)

    gen1 = brand_to_generic.get(med1_corrected)
    gen2 = brand_to_generic.get(med2_corrected)

    if not gen1 or not gen2:
        return render_template('index.html',
                               result="❌ Medicine not found",
                               color="gray")

    # Check interaction
    severity = interactions.get((gen1, gen2))

    if severity == "high":
        result = f"🔴 HIGH RISK interaction between {gen1} and {gen2}"
        color = "red"
    elif severity == "moderate":
        result = f"🟡 MODERATE interaction between {gen1} and {gen2}"
        color = "orange"
    elif severity == "low":
        result = f"🟢 LOW interaction between {gen1} and {gen2}"
        color = "green"
    else:
        result = f"🟢 No known interaction between {gen1} and {gen2}"
        color = "green"

    return render_template('index.html',
                           result=result,
                           color=color,
                           med1=med1_corrected,
                           med2=med2_corrected)


if __name__ == '__main__':
    app.run(debug=True)
