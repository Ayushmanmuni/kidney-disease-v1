"""
============================================================
  CKD Prediction – Flask REST API
============================================================
  This module loads the trained Random Forest model and
  exposes a POST /predict endpoint for real-time chronic
  kidney disease predictions.

  Usage:
      python app.py          → starts the server on port 5000
      POST /predict           → send patient JSON, get prediction

  Author : Ayush (college project)
  Python : 3.x | Flask · joblib · numpy · pandas
============================================================
"""

# ─────────────────────────────────────────────
# 0. Import Libraries
# ─────────────────────────────────────────────
"""
Flask       – lightweight web framework for building the API
joblib      – loads the saved .pkl model from disk
numpy       – numerical operations on input arrays
pandas      – creates a DataFrame matching the training format
os          – file-path handling
"""

import os
import numpy as np
import pandas as pd
import joblib
from flask import Flask, request, jsonify, send_from_directory

# ─────────────────────────────────────────────
# 1. Configuration
# ─────────────────────────────────────────────
"""
BASE_DIR   – root directory of this project
MODEL_PATH – path to the saved Random Forest .pkl file

FEATURE_ORDER – the exact 24 features the model was trained on,
  in the same order used during training.  Changing this order
  will produce wrong predictions!

ENCODING_MAP – maps categorical text values to the same numeric
  codes used while training (see ckd_prediction_pipeline.py STEP 4).
"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "output", "best_ckd_model.pkl")

# 24 features in the exact order used during training
FEATURE_ORDER = [
    "age", "bp", "sg", "al", "su",          # numeric vitals
    "rbc", "pc", "pcc", "ba",                # categorical blood / urine tests
    "bgr", "bu", "sc", "sod", "pot",         # numeric blood chemistry
    "hemo", "pcv", "wc", "rc",               # numeric blood counts
    "htn", "dm", "cad", "appet", "pe", "ane" # categorical medical history
]

# Encoding map for categorical features (must match the training pipeline)
ENCODING_MAP = {
    "rbc":   {"normal": 0, "abnormal": 1},
    "pc":    {"normal": 0, "abnormal": 1},
    "pcc":   {"present": 1, "notpresent": 0},
    "ba":    {"present": 1, "notpresent": 0},
    "htn":   {"yes": 1, "no": 0},
    "dm":    {"yes": 1, "no": 0},
    "cad":   {"yes": 1, "no": 0},
    "appet": {"good": 0, "poor": 1},
    "pe":    {"yes": 1, "no": 0},
    "ane":   {"yes": 1, "no": 0},
}

# ─────────────────────────────────────────────
# 2. Load the Trained Model
# ─────────────────────────────────────────────
"""
We load the model once when the server starts so every
request reuses the same in-memory model (fast inference).
"""

print(f"Loading model from: {MODEL_PATH}")
model = joblib.load(MODEL_PATH)
print("✅ Model loaded successfully!")

# Pre-compute global feature importances from the Random Forest model
# These values indicate how much each feature contributes to predictions
FEATURE_IMPORTANCES = {}
if hasattr(model, 'feature_importances_'):
    importances = model.feature_importances_
    FEATURE_IMPORTANCES = {
        FEATURE_ORDER[i]: round(float(importances[i]), 4)
        for i in range(len(FEATURE_ORDER))
    }
    print(f"   Feature importances computed for {len(FEATURE_IMPORTANCES)} features")
print()


# ─────────────────────────────────────────────
# 3. Prediction Function
# ─────────────────────────────────────────────
def predict_ckd(input_data):
    """
    Predict whether a patient has Chronic Kidney Disease.

    Parameters
    ----------
    input_data : dict
        A dictionary of patient parameters, e.g.
        {"age": 48, "bp": 80, "sg": 1.020, "rbc": "normal", ...}

    Returns
    -------
    dict
        {
            "prediction" : "CKD" or "Not CKD",
            "probability": {"CKD": 0.92, "Not CKD": 0.08}
        }
    """

    # --- 3a. Encode categorical features ---
    # Convert text values (e.g. "normal", "yes") to numbers
    # using the same mapping that was used during training.
    processed = {}
    for feature in FEATURE_ORDER:
        value = input_data.get(feature)

        if value is None:
            raise ValueError(f"Missing required feature: '{feature}'")

        # If this feature has a categorical mapping, apply it
        if feature in ENCODING_MAP:
            mapping = ENCODING_MAP[feature]
            str_value = str(value).strip().lower()
            if str_value in mapping:
                processed[feature] = mapping[str_value]
            else:
                # If numeric value is already provided, keep it as-is
                try:
                    processed[feature] = float(value)
                except (ValueError, TypeError):
                    valid = list(mapping.keys())
                    raise ValueError(
                        f"Invalid value '{value}' for '{feature}'. "
                        f"Expected one of: {valid}"
                    )
        else:
            # Numeric feature – convert to float
            try:
                processed[feature] = float(value)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Invalid numeric value '{value}' for feature '{feature}'"
                )

    # --- 3b. Build a DataFrame with the correct column order ---
    # The model expects features in the exact same order as training
    df = pd.DataFrame([processed], columns=FEATURE_ORDER)

    # --- 3c. Make prediction ---
    prediction = model.predict(df)[0]                # 1 = CKD, 0 = Not CKD
    label = "CKD" if prediction == 1 else "Not CKD"

    # --- 3d. Get probability scores (if model supports it) ---
    probability = {}
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(df)[0]           # [P(Not CKD), P(CKD)]
        probability = {
            "Not CKD": round(float(proba[0]), 4),
            "CKD":     round(float(proba[1]), 4),
        }

    return {
        "prediction":  label,
        "probability": probability,
    }


# ─────────────────────────────────────────────
# 4. Flask Application
# ─────────────────────────────────────────────
"""
We create a Flask app with two routes:
  GET  /         → health check & feature list
  POST /predict  → accepts patient JSON, returns prediction
"""

app = Flask(__name__, static_folder='static', static_url_path='/static')


# ── 4a. Web interface ──
@app.route("/", methods=["GET"])
def home():
    """
    Root endpoint – serves the CKD Prediction web interface.
    The static/index.html file contains the complete UI.
    """
    return send_from_directory('static', 'index.html')


@app.route("/about-ckd")
def about_ckd():
    return send_from_directory('static', 'about-ckd.html')


@app.route("/how-it-works")
def how_it_works():
    return send_from_directory('static', 'how-it-works.html')


@app.route("/research")
def research():
    return send_from_directory('static', 'research.html')


# ── 4b. API info endpoint ──
@app.route("/api/info", methods=["GET"])
def api_info():
    """
    Returns model metadata, expected features, and feature importances.
    Used by the frontend to stay in sync with the backend.
    """
    return jsonify({
        "status": "CKD Prediction API is running",
        "expected_features": FEATURE_ORDER,
        "categorical_features": {
            feature: list(mapping.keys())
            for feature, mapping in ENCODING_MAP.items()
        },
        "feature_importance": FEATURE_IMPORTANCES,
    })


# ── 4c. Prediction endpoint ──
@app.route("/predict", methods=["POST"])
def predict():
    """
    POST /predict

    Expects JSON body with 24 patient features.
    Returns prediction result and probability scores.

    Example request body:
    {
        "age": 48, "bp": 80, "sg": 1.020, "al": 1, "su": 0,
        "rbc": "normal", "pc": "normal", "pcc": "notpresent",
        "ba": "notpresent", "bgr": 121, "bu": 36, "sc": 1.2,
        "sod": 138, "pot": 4.5, "hemo": 15.4, "pcv": 44,
        "wc": 7800, "rc": 5.2, "htn": "yes", "dm": "no",
        "cad": "no", "appet": "good", "pe": "no", "ane": "no"
    }
    """

    # Validate that the request contains JSON
    if not request.is_json:
        return jsonify({
            "error": "Request must be JSON. Set Content-Type: application/json"
        }), 400

    # Get the patient data from the request body
    patient_data = request.get_json()

    try:
        result = predict_ckd(patient_data)
        return jsonify({
            "success":          True,
            "prediction":       result["prediction"],
            "probability":      result["probability"],
            "feature_importance": FEATURE_IMPORTANCES,
            "message":          f"The patient is predicted as: {result['prediction']}",
        })

    except ValueError as e:
        # Input validation errors (missing features, bad values)
        return jsonify({"success": False, "error": str(e)}), 400

    except Exception as e:
        # Unexpected errors
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


# ─────────────────────────────────────────────
# 5. Run the Server
# ─────────────────────────────────────────────
"""
Start the Flask development server.
  - debug=True  → auto-reloads on code changes (dev only)
  - port=5000   → accessible at http://localhost:5000

For production, use a WSGI server like gunicorn instead:
    gunicorn app:app --bind 0.0.0.0:5000
"""

if __name__ == "__main__":
    print("=" * 50)
    print("  CKD Prediction API")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
