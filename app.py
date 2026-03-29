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
import json
import smtplib
import ssl
import numpy as np
import pandas as pd
import joblib
from email.message import EmailMessage
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_from_directory, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

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

# Path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "output", "best_ckd_model.pkl")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Feedback email settings (configure via environment variables)
FEEDBACK_EMAIL_TO = os.environ.get("FEEDBACK_EMAIL_TO", "ayushman.muni.06@gmail.com")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "ayushman.muni.06@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "ncjmpnwddkrniosc")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", SMTP_USERNAME or FEEDBACK_EMAIL_TO)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "ayushman.muni.06@gmail.com").strip().lower()

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

# Safe clinical defaults (median/mode from training data) for missing values
SAFE_DEFAULTS = {
    "age": 51, "bp": 76, "sg": "1.020", "al": "0", "su": "0",
    "rbc": "normal", "pc": "normal", "pcc": "notpresent", "ba": "notpresent",
    "bgr": 121, "bu": 53, "sc": 1.4, "sod": 137, "pot": 4.6,
    "hemo": 12.5, "pcv": 40, "wc": 8406, "rc": 4.7,
    "htn": "no", "dm": "no", "cad": "no", "appet": "good", "pe": "no", "ane": "no"
}

# Valid ranges for numeric features (for edge-case validation warnings)
VALID_RANGES = {
    "age": (1, 120), "bp": (30, 220), "bgr": (10, 600),
    "bu": (1, 500), "sc": (0.1, 100), "sod": (4, 200),
    "pot": (1, 60), "hemo": (2, 20), "pcv": (5, 60),
    "wc": (1000, 40000), "rc": (1, 10),
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
        Missing fields are auto-filled with safe clinical defaults.

    Returns
    -------
    dict
        {
            "prediction" : "CKD" or "Not CKD",
            "probability": {"CKD": 0.92, "Not CKD": 0.08},
            "warnings"   : [list of any auto-fill or edge case warnings]
        }
    """

    warnings_list = []

    # --- 3a. Handle missing values and encode features ---
    processed = {}
    for feature in FEATURE_ORDER:
        value = input_data.get(feature)

        # Handle missing / empty / None values with safe defaults
        if value is None or str(value).strip() == "":
            default_val = SAFE_DEFAULTS.get(feature)
            warnings_list.append(
                f"'{feature}' was missing — auto-filled with default ({default_val})"
            )
            value = default_val

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
                    # Fall back to default instead of crashing
                    default_val = SAFE_DEFAULTS.get(feature, 0)
                    default_encoded = mapping.get(
                        str(default_val).strip().lower(),
                        list(mapping.values())[0]
                    )
                    processed[feature] = default_encoded
                    warnings_list.append(
                        f"Invalid value '{value}' for '{feature}' — used default ({default_val})"
                    )
        else:
            # Numeric feature – convert to float
            try:
                processed[feature] = float(value)
            except (ValueError, TypeError):
                default_val = SAFE_DEFAULTS.get(feature, 0)
                processed[feature] = float(default_val)
                warnings_list.append(
                    f"Invalid value '{value}' for '{feature}' — used default ({default_val})"
                )

        # --- 3b. Edge case validation for extreme values ---
        if feature in VALID_RANGES and feature not in ENCODING_MAP:
            num_val = processed.get(feature)
            if num_val is not None:
                lo, hi = VALID_RANGES[feature]
                if num_val < lo or num_val > hi:
                    warnings_list.append(
                        f"'{feature}' value {num_val} is outside expected range ({lo}–{hi})"
                    )

    # --- 3c. Build a DataFrame with the correct column order ---
    df = pd.DataFrame([processed], columns=FEATURE_ORDER)

    # --- 3d. Make prediction ---
    prediction = model.predict(df)[0]                # 1 = CKD, 0 = Not CKD
    label = "CKD" if prediction == 1 else "Not CKD"

    # --- 3e. Get probability scores (if model supports it) ---
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
        "warnings":    warnings_list,
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
app.secret_key = os.environ.get('SECRET_KEY', 'ckd_super_secret_dev_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ckd_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    predictions = db.relationship('PredictionHistory', backref='user', lazy=True)

class PredictionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_name = db.Column(db.String(100), nullable=True)
    result = db.Column(db.String(50), nullable=False)
    probability_ckd = db.Column(db.Float, nullable=False)
    input_data = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class FeedbackReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    category = db.Column(db.String(30), nullable=False, default='bug')
    message = db.Column(db.Text, nullable=False)
    page_url = db.Column(db.String(500), nullable=True)
    user_agent = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def is_admin_user(user):
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and (user.email or "").strip().lower() == ADMIN_EMAIL
    )


def send_feedback_email(report):
    """Send feedback report notification email. Returns (ok: bool, error: str|None)."""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return False, "SMTP credentials are not configured"

    subject = f"[CKD Feedback] #{report.id} {report.category.upper()}"
    body = (
        f"New feedback report received\n\n"
        f"Report ID: {report.id}\n"
        f"Created At: {report.created_at}\n"
        f"Category: {report.category}\n"
        f"Status: {report.status}\n"
        f"User ID: {report.user_id or 'Anonymous'}\n"
        f"Name: {report.name or 'N/A'}\n"
        f"Email: {report.email or 'N/A'}\n"
        f"Page URL: {report.page_url or 'N/A'}\n"
        f"User Agent: {report.user_agent or 'N/A'}\n\n"
        f"Message:\n{report.message}\n"
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM_EMAIL
    msg["To"] = FEEDBACK_EMAIL_TO
    msg.set_content(body)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)


def send_feedback_reply_email(report, reply_text):
    """Send admin reply to reporter email when available."""
    recipient = (report.email or "").strip()
    if not recipient:
        return False, "Reporter email is not available"
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return False, "SMTP credentials are not configured"

    subject = f"[CKD Feedback Reply] Report #{report.id}"
    body = (
        f"Hello {report.name or 'User'},\n\n"
        f"Thank you for your feedback on CKD Predict.\n"
        f"Report ID: {report.id}\n"
        f"Category: {report.category}\n"
        f"Status: {report.status}\n\n"
        f"Our reply:\n{reply_text}\n\n"
        f"Original message:\n{report.message}\n\n"
        f"Regards,\nCKD Predict Team"
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM_EMAIL
    msg["To"] = recipient
    msg.set_content(body)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls(context=context)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)

with app.app_context():
    db.create_all()

# ── 4a. Web interface ──
@app.route("/", methods=["GET"])
def home():
    """
    Root endpoint – serves the CKD Prediction web interface.
    The static/index.html file contains the complete UI.
    """
    return send_from_directory('static', 'index.html')

# ── Auth Pages ──
@app.route("/login")
def login_page():
    return send_from_directory('static', 'login.html')

@app.route("/signup")
def signup_page():
    return send_from_directory('static', 'signup.html')

@app.route("/profile")
def profile_page():
    return send_from_directory('static', 'profile.html')


@app.route("/about-ckd")
def about_ckd():
    return send_from_directory('static', 'about-ckd.html')


@app.route("/dashboard")
def dashboard_page():
    return send_from_directory('static', 'dashboard.html')


@app.route("/how-it-works")
def how_it_works():
    return send_from_directory('static', 'how-it-works.html')


@app.route("/transparency")
def transparency_page():
    return send_from_directory('static', 'transparency.html')


@app.route("/research-team")
def research_team_page():
    return send_from_directory('static', 'research-team.html')


@app.route("/research")
def research():
    return send_from_directory('static', 'research.html')


# ── Auth Endpoints ──
@app.route("/api/auth/signup", methods=["POST"])
def api_signup():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify({"success": False, "error": "Missing fields"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": "Email already registered"}), 400
        
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(name=name, email=email, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)
    return jsonify({"success": True})

@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    
    if user and bcrypt.check_password_hash(user.password, password):
        login_user(user)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid email or password"}), 401

@app.route("/api/auth/logout", methods=["POST", "GET"])
def api_logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/api/user/status", methods=["GET"])
def api_user_status():
    if current_user.is_authenticated:
        return jsonify({
            "logged_in": True,
            "user": {
                "name": current_user.name,
                "email": current_user.email,
                "initial": current_user.name[0].upper() if current_user.name else "?",
                "profile_pic": f"/static/uploads/{current_user.profile_pic}" if current_user.profile_pic else None
            }
        })
    return jsonify({"logged_in": False})

@app.route("/api/user/profile-pic", methods=["POST"])
@login_required
def upload_profile_pic():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
    if ext not in ('png', 'jpg', 'jpeg', 'gif', 'webp'):
        return jsonify({"success": False, "error": "Invalid file type"}), 400
    filename = f"user_{current_user.id}.{ext}"
    f.save(os.path.join(UPLOAD_FOLDER, filename))
    current_user.profile_pic = filename
    db.session.commit()
    return jsonify({"success": True, "profile_pic": f"/static/uploads/{filename}"})

@app.route("/api/user/history", methods=["GET"])
@login_required
def api_user_history():
    history = PredictionHistory.query.filter_by(user_id=current_user.id).order_by(PredictionHistory.timestamp.desc()).limit(50).all()
    results = [{
        "id": h.id,
        "patient_name": h.patient_name or "Unknown Patient",
        "result": h.result,
        "probability_ckd": h.probability_ckd,
        "input_data": json.loads(h.input_data) if h.input_data else None,
        "date": h.timestamp.strftime("%Y-%m-%d %H:%M")
    } for h in history]
    return jsonify({"success": True, "history": results})

@app.route("/api/user/history/<int:record_id>", methods=["DELETE"])
@login_required
def delete_history_record(record_id):
    record = PredictionHistory.query.filter_by(id=record_id, user_id=current_user.id).first()
    if record:
        db.session.delete(record)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Record not found"}), 404

@app.route("/api/user/history", methods=["DELETE"])
@login_required
def clear_user_history():
    PredictionHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json(silent=True) or {}

    message = str(data.get("message", "")).strip()
    if len(message) < 10:
        return jsonify({
            "success": False,
            "error": "Please describe the issue in at least 10 characters."
        }), 400

    category = str(data.get("category", "bug")).strip().lower()
    if category not in {"bug", "ui", "feature", "other"}:
        category = "other"

    name = str(data.get("name", "")).strip()[:100] or None
    email = str(data.get("email", "")).strip()[:120] or None
    page_url = str(data.get("page_url", "")).strip()[:500] or request.referrer
    user_agent = request.headers.get("User-Agent", "")[:300] or None

    report = FeedbackReport(
        user_id=current_user.id if current_user.is_authenticated else None,
        name=name,
        email=email,
        category=category,
        message=message[:4000],
        page_url=page_url,
        user_agent=user_agent,
        status="open",
    )
    db.session.add(report)
    db.session.commit()

    mail_ok, mail_err = send_feedback_email(report)

    response = {
        "success": True,
        "message": "Thanks! Your feedback has been submitted.",
        "report_id": report.id,
        "email_sent": mail_ok,
    }
    if not mail_ok:
        response["email_error"] = mail_err

    return jsonify(response)


@app.route("/api/feedback/reports", methods=["GET"])
@login_required
def list_feedback_reports():
    if not is_admin_user(current_user):
        return jsonify({"success": False, "error": "Admin access required"}), 403

    reports = FeedbackReport.query.order_by(FeedbackReport.created_at.desc()).limit(300).all()
    rows = []
    for r in reports:
        reporter_user = User.query.get(r.user_id) if r.user_id else None
        rows.append({
            "id": r.id,
            "category": r.category,
            "status": r.status,
            "message": r.message,
            "page_url": r.page_url,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "reported_by": {
                "user_id": r.user_id,
                "name": r.name or (reporter_user.name if reporter_user else None),
                "email": r.email or (reporter_user.email if reporter_user else None),
            },
        })

    return jsonify({"success": True, "reports": rows})


@app.route("/api/feedback/reports/<int:report_id>/status", methods=["PATCH"])
@login_required
def update_feedback_status(report_id):
    if not is_admin_user(current_user):
        return jsonify({"success": False, "error": "Admin access required"}), 403

    report = FeedbackReport.query.get(report_id)
    if not report:
        return jsonify({"success": False, "error": "Report not found"}), 404

    data = request.get_json(silent=True) or {}
    next_status = str(data.get("status", "")).strip().lower()
    if next_status not in {"open", "closed"}:
        return jsonify({"success": False, "error": "Invalid status"}), 400

    report.status = next_status
    db.session.commit()
    return jsonify({"success": True, "status": report.status})


@app.route("/api/feedback/reports/<int:report_id>", methods=["DELETE"])
@login_required
def delete_feedback_report(report_id):
    if not is_admin_user(current_user):
        return jsonify({"success": False, "error": "Admin access required"}), 403

    report = FeedbackReport.query.get(report_id)
    if not report:
        return jsonify({"success": False, "error": "Report not found"}), 404

    db.session.delete(report)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/feedback/reports/<int:report_id>/reply", methods=["POST"])
@login_required
def reply_feedback_report(report_id):
    if not is_admin_user(current_user):
        return jsonify({"success": False, "error": "Admin access required"}), 403

    report = FeedbackReport.query.get(report_id)
    if not report:
        return jsonify({"success": False, "error": "Report not found"}), 404

    data = request.get_json(silent=True) or {}
    reply_text = str(data.get("reply", "")).strip()
    if len(reply_text) < 3:
        return jsonify({"success": False, "error": "Reply is too short"}), 400

    ok, err = send_feedback_reply_email(report, reply_text)
    if not ok:
        return jsonify({"success": False, "error": err or "Failed to send reply"}), 400

    report.status = "closed"
    db.session.commit()
    return jsonify({"success": True, "status": report.status})


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
        response = {
            "success":          True,
            "prediction":       result["prediction"],
            "probability":      result["probability"],
            "feature_importance": FEATURE_IMPORTANCES,
            "message":          f"The patient is predicted as: {result['prediction']}",
        }
        # Include warnings if any missing/edge-case values were auto-filled
        if result.get("warnings"):
            response["warnings"] = result["warnings"]
        # Track prediction if user is logged in
        if current_user.is_authenticated:
            safe_input = {k: v for k, v in patient_data.items() if k != 'patient_name'}
            new_pred = PredictionHistory(
                user_id=current_user.id,
                patient_name=patient_data.get("patient_name", "Unknown Patient"),
                result=result["prediction"],
                probability_ckd=result["probability"].get("CKD", 0.0),
                input_data=json.dumps(safe_input)
            )
            db.session.add(new_pred)
            db.session.commit()
            
        return jsonify(response)

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
