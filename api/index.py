"""
============================================================
  CKD Prediction – Vercel Serverless API (Pure Python)
============================================================
  Zero heavy dependencies: no scikit-learn, numpy, pandas, scipy.
  Model loaded from JSON, prediction via pure Python tree traversal.
============================================================
"""

import os
import json
import smtplib
import ssl
import bcrypt as bcrypt_lib
from email.message import EmailMessage
from flask import Flask, request, jsonify, redirect
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user, login_required, current_user,
)
from supabase import create_client

# ─────────────────────────────────────────────
# 0. Configuration
# ─────────────────────────────────────────────

API_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(API_DIR)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# Graceful init — don't crash function if env vars not yet configured
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        pass

FEEDBACK_EMAIL_TO = os.environ.get("FEEDBACK_EMAIL_TO", "ayushman.muni.06@gmail.com")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "ayushman.muni.06@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", SMTP_USERNAME or FEEDBACK_EMAIL_TO)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "ayushman.muni.06@gmail.com").strip().lower()

FEATURE_ORDER = [
    "age", "bp", "sg", "al", "su",
    "rbc", "pc", "pcc", "ba",
    "bgr", "bu", "sc", "sod", "pot",
    "hemo", "pcv", "wc", "rc",
    "htn", "dm", "cad", "appet", "pe", "ane",
]

ENCODING_MAP = {
    "rbc": {"normal": 0, "abnormal": 1},
    "pc": {"normal": 0, "abnormal": 1},
    "pcc": {"present": 1, "notpresent": 0},
    "ba": {"present": 1, "notpresent": 0},
    "htn": {"yes": 1, "no": 0},
    "dm": {"yes": 1, "no": 0},
    "cad": {"yes": 1, "no": 0},
    "appet": {"good": 0, "poor": 1},
    "pe": {"yes": 1, "no": 0},
    "ane": {"yes": 1, "no": 0},
}

SAFE_DEFAULTS = {
    "age": 51, "bp": 76, "sg": "1.020", "al": "0", "su": "0",
    "rbc": "normal", "pc": "normal", "pcc": "notpresent", "ba": "notpresent",
    "bgr": 121, "bu": 53, "sc": 1.4, "sod": 137, "pot": 4.6,
    "hemo": 12.5, "pcv": 40, "wc": 8406, "rc": 4.7,
    "htn": "no", "dm": "no", "cad": "no", "appet": "good", "pe": "no", "ane": "no",
}

VALID_RANGES = {
    "age": (1, 120), "bp": (30, 220), "bgr": (10, 600),
    "bu": (1, 500), "sc": (0.1, 100), "sod": (4, 200),
    "pot": (1, 60), "hemo": (2, 20), "pcv": (5, 60),
    "wc": (1000, 40000), "rc": (1, 10),
}

# ─────────────────────────────────────────────
# 1. Load JSON Model + Pure Python Prediction
# ─────────────────────────────────────────────

MODEL_JSON_PATH = os.path.join(API_DIR, "model.json")
with open(MODEL_JSON_PATH, "r") as f:
    MODEL_DATA = json.load(f)

FEATURE_IMPORTANCES = {
    FEATURE_ORDER[i]: round(MODEL_DATA["feature_importances"][i], 4)
    for i in range(len(FEATURE_ORDER))
}


def _traverse_tree(tree, features):
    """Walk a single decision tree to its leaf and return class counts."""
    node = 0
    while tree["cl"][node] != -1:
        if features[tree["f"][node]] <= tree["t"][node]:
            node = tree["cl"][node]
        else:
            node = tree["cr"][node]
    return tree["v"][node]


def _predict_rf(features_list):
    """
    Pure Python Random Forest predict + predict_proba.
    features_list: list of 24 numeric values in FEATURE_ORDER.
    Returns (predicted_class, {class_label: probability}).
    """
    n_classes = MODEL_DATA["n_classes"]
    avg_proba = [0.0] * n_classes
    n_trees = MODEL_DATA["n_estimators"]

    for tree in MODEL_DATA["trees"]:
        dist = _traverse_tree(tree, features_list)
        total = sum(dist)
        if total > 0:
            for i in range(n_classes):
                avg_proba[i] += dist[i] / total

    for i in range(n_classes):
        avg_proba[i] /= n_trees

    pred_idx = avg_proba.index(max(avg_proba))
    pred_class = MODEL_DATA["classes"][pred_idx]

    prob_dict = {}
    for i, cls in enumerate(MODEL_DATA["classes"]):
        label = "CKD" if cls == 1 else "Not CKD"
        prob_dict[label] = round(avg_proba[i], 4)

    return pred_class, prob_dict


# ─────────────────────────────────────────────
# 2. Feature Processing + Prediction
# ─────────────────────────────────────────────

def predict_ckd(input_data):
    warnings_list = []
    processed = {}

    for feature in FEATURE_ORDER:
        value = input_data.get(feature)
        if value is None or str(value).strip() == "":
            default_val = SAFE_DEFAULTS.get(feature)
            warnings_list.append(f"'{feature}' was missing - auto-filled with default ({default_val})")
            value = default_val

        if feature in ENCODING_MAP:
            mapping = ENCODING_MAP[feature]
            str_value = str(value).strip().lower()
            if str_value in mapping:
                processed[feature] = mapping[str_value]
            else:
                try:
                    processed[feature] = float(value)
                except (ValueError, TypeError):
                    default_val = SAFE_DEFAULTS.get(feature, 0)
                    default_encoded = mapping.get(str(default_val).strip().lower(), list(mapping.values())[0])
                    processed[feature] = default_encoded
                    warnings_list.append(f"Invalid value '{value}' for '{feature}' - used default ({default_val})")
        else:
            try:
                processed[feature] = float(value)
            except (ValueError, TypeError):
                default_val = SAFE_DEFAULTS.get(feature, 0)
                processed[feature] = float(default_val)
                warnings_list.append(f"Invalid value '{value}' for '{feature}' - used default ({default_val})")

        if feature in VALID_RANGES and feature not in ENCODING_MAP:
            num_val = processed.get(feature)
            if num_val is not None:
                lo, hi = VALID_RANGES[feature]
                if num_val < lo or num_val > hi:
                    warnings_list.append(f"'{feature}' value {num_val} is outside expected range ({lo}-{hi})")

    features_list = [processed[f] for f in FEATURE_ORDER]
    pred_class, probability = _predict_rf(features_list)
    label = "CKD" if pred_class == 1 else "Not CKD"

    return {"prediction": label, "probability": probability, "warnings": warnings_list}


# ─────────────────────────────────────────────
# 3. Flask App
# ─────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ckd_super_secret_dev_key")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True

login_manager = LoginManager(app)


class User(UserMixin):
    def __init__(self, id, name, email, password, profile_pic=None, created_at=None):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.profile_pic = profile_pic
        self.created_at = created_at


def _row_to_user(row):
    if not row:
        return None
    return User(
        id=row["id"], name=row["name"], email=row["email"],
        password=row["password"], profile_pic=row.get("profile_pic"),
        created_at=row.get("created_at"),
    )


@login_manager.user_loader
def load_user(user_id):
    try:
        result = supabase.table("users").select("*").eq("id", int(user_id)).execute()
        if result.data:
            return _row_to_user(result.data[0])
    except Exception:
        pass
    return None


def is_admin_user(user):
    return bool(
        user and getattr(user, "is_authenticated", False)
        and (user.email or "").strip().lower() == ADMIN_EMAIL
    )


# ── Email helpers ──

def send_feedback_email(report_dict):
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return False, "SMTP credentials are not configured"
    subject = f"[CKD Feedback] #{report_dict['id']} {report_dict['category'].upper()}"
    body = (
        f"New feedback report received\n\n"
        f"Report ID: {report_dict['id']}\nCategory: {report_dict['category']}\n"
        f"Status: {report_dict['status']}\nName: {report_dict.get('name') or 'N/A'}\n"
        f"Email: {report_dict.get('email') or 'N/A'}\n\nMessage:\n{report_dict['message']}\n"
    )
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, SMTP_FROM_EMAIL, FEEDBACK_EMAIL_TO
    msg.set_content(body)
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            s.starttls(context=ctx)
            s.login(SMTP_USERNAME, SMTP_PASSWORD)
            s.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)


def send_feedback_reply_email(report_dict, reply_text):
    recipient = (report_dict.get("email") or "").strip()
    if not recipient:
        return False, "Reporter email is not available"
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return False, "SMTP credentials are not configured"
    subject = f"[CKD Feedback Reply] Report #{report_dict['id']}"
    body = (
        f"Hello {report_dict.get('name') or 'User'},\n\n"
        f"Thank you for your feedback.\nReport ID: {report_dict['id']}\n\n"
        f"Our reply:\n{reply_text}\n\nOriginal message:\n{report_dict['message']}\n\n"
        f"Regards,\nCKD Predict Team"
    )
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, SMTP_FROM_EMAIL, recipient
    msg.set_content(body)
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            s.starttls(context=ctx)
            s.login(SMTP_USERNAME, SMTP_PASSWORD)
            s.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────
# 4. Root + Auth Endpoints
# ─────────────────────────────────────────────

@app.route("/")
def serve_home():
    """Serve homepage — fallback if Vercel routes / through Flask."""
    public_dir = os.path.join(BASE_DIR, "public")
    index_path = os.path.join(public_dir, "index.html")
    if os.path.exists(index_path):
        from flask import send_from_directory
        return send_from_directory(public_dir, "index.html")
    return jsonify({"status": "CKD Prediction API is running", "docs": "/api/info"})

@app.route("/api/auth/signup", methods=["POST"])
def api_signup():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    if not name or not email or not password:
        return jsonify({"success": False, "error": "Missing fields"}), 400
    existing = supabase.table("users").select("id").eq("email", email).execute()
    if existing.data:
        return jsonify({"success": False, "error": "Email already registered"}), 400
    hashed_pw = bcrypt_lib.hashpw(password.encode("utf-8"), bcrypt_lib.gensalt()).decode("utf-8")
    result = supabase.table("users").insert({"name": name, "email": email, "password": hashed_pw}).execute()
    if result.data:
        login_user(_row_to_user(result.data[0]))
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Failed to create account"}), 500


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    result = supabase.table("users").select("*").eq("email", email).execute()
    if not result.data:
        return jsonify({"success": False, "error": "Invalid email or password"}), 401
    row = result.data[0]
    if bcrypt_lib.checkpw(password.encode("utf-8"), row["password"].encode("utf-8")):
        login_user(_row_to_user(row))
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid email or password"}), 401


@app.route("/api/auth/logout", methods=["POST", "GET"])
def api_logout():
    logout_user()
    return redirect("/")


# ─────────────────────────────────────────────
# 5. User Endpoints
# ─────────────────────────────────────────────

@app.route("/api/user/status", methods=["GET"])
def api_user_status():
    if current_user.is_authenticated:
        return jsonify({
            "logged_in": True,
            "user": {
                "name": current_user.name, "email": current_user.email,
                "initial": current_user.name[0].upper() if current_user.name else "?",
                "profile_pic": None,
            },
        })
    return jsonify({"logged_in": False})


@app.route("/api/user/history", methods=["GET"])
@login_required
def api_user_history():
    result = (
        supabase.table("prediction_history").select("*")
        .eq("user_id", current_user.id).order("timestamp", desc=True).limit(50).execute()
    )
    history = []
    for h in result.data or []:
        history.append({
            "id": h["id"], "patient_name": h.get("patient_name") or "Unknown Patient",
            "result": h["result"], "probability_ckd": h["probability_ckd"],
            "input_data": json.loads(h["input_data"]) if h.get("input_data") else None,
            "date": h.get("timestamp", "")[:16].replace("T", " "),
        })
    return jsonify({"success": True, "history": history})


@app.route("/api/user/history/<int:record_id>", methods=["DELETE"])
@login_required
def delete_history_record(record_id):
    supabase.table("prediction_history").delete().eq("id", record_id).eq("user_id", current_user.id).execute()
    return jsonify({"success": True})


@app.route("/api/user/history", methods=["DELETE"])
@login_required
def clear_user_history():
    supabase.table("prediction_history").delete().eq("user_id", current_user.id).execute()
    return jsonify({"success": True})


# ─────────────────────────────────────────────
# 6. Prediction Endpoint
# ─────────────────────────────────────────────

@app.route("/api/info", methods=["GET"])
def api_info():
    return jsonify({
        "status": "CKD Prediction API is running",
        "expected_features": FEATURE_ORDER,
        "categorical_features": {f: list(m.keys()) for f, m in ENCODING_MAP.items()},
        "feature_importance": FEATURE_IMPORTANCES,
    })


@app.route("/predict", methods=["POST"])
def predict():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON. Set Content-Type: application/json"}), 400
    patient_data = request.get_json()
    try:
        result = predict_ckd(patient_data)
        response = {
            "success": True, "prediction": result["prediction"],
            "probability": result["probability"], "feature_importance": FEATURE_IMPORTANCES,
            "message": f"The patient is predicted as: {result['prediction']}",
        }
        if result.get("warnings"):
            response["warnings"] = result["warnings"]
        if current_user.is_authenticated:
            safe_input = {k: v for k, v in patient_data.items() if k != "patient_name"}
            supabase.table("prediction_history").insert({
                "user_id": current_user.id,
                "patient_name": patient_data.get("patient_name", "Unknown Patient"),
                "result": result["prediction"],
                "probability_ckd": result["probability"].get("CKD", 0.0),
                "input_data": json.dumps(safe_input),
            }).execute()
        return jsonify(response)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


# ─────────────────────────────────────────────
# 7. Feedback Endpoints
# ─────────────────────────────────────────────

@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    if len(message) < 10:
        return jsonify({"success": False, "error": "Please describe the issue in at least 10 characters."}), 400
    category = str(data.get("category", "bug")).strip().lower()
    if category not in {"bug", "ui", "feature", "other"}:
        category = "other"
    row = {
        "user_id": current_user.id if current_user.is_authenticated else None,
        "name": str(data.get("name", "")).strip()[:100] or None,
        "email": str(data.get("email", "")).strip()[:120] or None,
        "category": category, "message": message[:4000],
        "page_url": str(data.get("page_url", "")).strip()[:500] or request.referrer,
        "user_agent": request.headers.get("User-Agent", "")[:300] or None,
        "status": "open",
    }
    result = supabase.table("feedback_reports").insert(row).execute()
    report = result.data[0] if result.data else row
    mail_ok, mail_err = send_feedback_email(report)
    resp = {"success": True, "message": "Thanks! Your feedback has been submitted.", "report_id": report.get("id"), "email_sent": mail_ok}
    if not mail_ok:
        resp["email_error"] = mail_err
    return jsonify(resp)


@app.route("/api/feedback/reports", methods=["GET"])
@login_required
def list_feedback_reports():
    if not is_admin_user(current_user):
        return jsonify({"success": False, "error": "Admin access required"}), 403
    result = supabase.table("feedback_reports").select("*").order("created_at", desc=True).limit(300).execute()
    rows = []
    for r in result.data or []:
        reporter = None
        if r.get("user_id"):
            u_res = supabase.table("users").select("name, email").eq("id", r["user_id"]).execute()
            reporter = u_res.data[0] if u_res.data else None
        rows.append({
            "id": r["id"], "category": r["category"], "status": r["status"],
            "message": r["message"], "page_url": r.get("page_url"),
            "created_at": (r.get("created_at") or "")[:16].replace("T", " "),
            "reported_by": {
                "user_id": r.get("user_id"),
                "name": r.get("name") or (reporter["name"] if reporter else None),
                "email": r.get("email") or (reporter["email"] if reporter else None),
            },
        })
    return jsonify({"success": True, "reports": rows})


@app.route("/api/feedback/reports/<int:report_id>/status", methods=["PATCH"])
@login_required
def update_feedback_status(report_id):
    if not is_admin_user(current_user):
        return jsonify({"success": False, "error": "Admin access required"}), 403
    data = request.get_json(silent=True) or {}
    next_status = str(data.get("status", "")).strip().lower()
    if next_status not in {"open", "closed"}:
        return jsonify({"success": False, "error": "Invalid status"}), 400
    supabase.table("feedback_reports").update({"status": next_status}).eq("id", report_id).execute()
    return jsonify({"success": True, "status": next_status})


@app.route("/api/feedback/reports/<int:report_id>", methods=["DELETE"])
@login_required
def delete_feedback_report(report_id):
    if not is_admin_user(current_user):
        return jsonify({"success": False, "error": "Admin access required"}), 403
    supabase.table("feedback_reports").delete().eq("id", report_id).execute()
    return jsonify({"success": True})


@app.route("/api/feedback/reports/<int:report_id>/reply", methods=["POST"])
@login_required
def reply_feedback_report(report_id):
    if not is_admin_user(current_user):
        return jsonify({"success": False, "error": "Admin access required"}), 403
    result = supabase.table("feedback_reports").select("*").eq("id", report_id).execute()
    if not result.data:
        return jsonify({"success": False, "error": "Report not found"}), 404
    report = result.data[0]
    data = request.get_json(silent=True) or {}
    reply_text = str(data.get("reply", "")).strip()
    if len(reply_text) < 3:
        return jsonify({"success": False, "error": "Reply is too short"}), 400
    ok, err = send_feedback_reply_email(report, reply_text)
    if not ok:
        return jsonify({"success": False, "error": err or "Failed to send reply"}), 400
    supabase.table("feedback_reports").update({"status": "closed"}).eq("id", report_id).execute()
    return jsonify({"success": True, "status": "closed"})


# ─────────────────────────────────────────────
# Vercel: rewrites land on /api/index but WSGI PATH_INFO stays "/api/index".
# Rewrites pass the real URL path as __vp=... so Flask routing matches.
# ─────────────────────────────────────────────

def _vercel_path_wsgi(app):
    from urllib.parse import parse_qsl, unquote, urlencode

    def middleware(environ, start_response):
        qs = environ.get("QUERY_STRING") or ""
        new_path = None
        rest_pairs = []
        for key, val in parse_qsl(qs, keep_blank_values=True):
            if key == "__vp":
                new_path = unquote(val)
            else:
                rest_pairs.append((key, val))
        if new_path:
            if not new_path.startswith("/"):
                new_path = "/" + new_path
            environ["PATH_INFO"] = new_path
            environ["QUERY_STRING"] = urlencode(rest_pairs) if rest_pairs else ""
        return app(environ, start_response)

    return middleware


app.wsgi_app = _vercel_path_wsgi(app.wsgi_app)
