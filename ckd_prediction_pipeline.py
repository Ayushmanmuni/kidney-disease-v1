"""
============================================================
  Chronic Kidney Disease (CKD) Prediction Pipeline
============================================================
  Dataset : UCI Machine Learning Repository – CKD dataset
  Records : ~400 patients · 24 clinical features + 1 target
  Author  : Ayush (college project)
  Python  : 3.x | pandas · numpy · scikit-learn · matplotlib
============================================================
"""

# ─────────────────────────────────────────────
# 0. Import Libraries
# ─────────────────────────────────────────────
"""
We import all necessary libraries at the top:
  • pandas & numpy    – data handling
  • matplotlib        – visualisation
  • scikit-learn      – ML models and evaluation utilities
  • joblib            – saving the trained model to disk
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")                       # non-interactive backend (works without GUI)
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
    classification_report,
)
import joblib

warnings.filterwarnings("ignore")

# Path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "CKD dataset", "chronic_kidney_disease_full.arff")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("  CHRONIC KIDNEY DISEASE – PREDICTION PIPELINE")
print("=" * 60)

# ─────────────────────────────────────────────
# STEP 1 · Load the Dataset
# ─────────────────────────────────────────────
"""
The dataset is in ARFF (Attribute-Relation File Format).
We skip the header lines (comments & @attribute declarations)
and read only the @data section as a CSV.
Column names are assigned manually based on the ARFF header.
"""

print("\n▶ STEP 1 – Loading the dataset …")

column_names = [
    "age", "bp", "sg", "al", "su",
    "rbc", "pc", "pcc", "ba",
    "bgr", "bu", "sc", "sod", "pot",
    "hemo", "pcv", "wc", "rc",
    "htn", "dm", "cad", "appet", "pe", "ane",
    "classification",
]

# Read the ARFF file manually to handle rows with trailing commas / extra fields
with open(DATA_PATH, "r") as f:
    lines = f.readlines()

# Find the @data section
data_start = 0
for i, line in enumerate(lines):
    if line.strip().lower() == "@data":
        data_start = i + 1
        break

# Parse data lines manually
rows = []
num_cols = len(column_names)
for line in lines[data_start:]:
    line = line.strip()
    if not line or line.startswith("%"):
        continue
    # Split and take exactly the expected number of columns
    fields = [f.strip() for f in line.split(",")][:num_cols]
    if len(fields) == num_cols:
        rows.append(fields)

df = pd.DataFrame(rows, columns=column_names)

# Replace '?' with NaN
df.replace(["?", " ?", "? ", ""], np.nan, inplace=True)

# Drop completely empty trailing rows (if any)
df.dropna(how="all", inplace=True)

print(f"   ✅ Dataset loaded successfully — {df.shape[0]} rows × {df.shape[1]} columns")

# ─────────────────────────────────────────────
# STEP 2 · Explore the Dataset
# ─────────────────────────────────────────────
"""
A quick look at the dataset to understand its structure:
  • head()   – first 5 rows
  • info()   – data types & non-null counts
  • isnull() – count of missing values per column
"""

print("\n▶ STEP 2 – Exploring the dataset …")

print("\n── First 5 Rows ──")
print(df.head().to_string())

print("\n── Dataset Info ──")
print(df.info())

print("\n── Missing Values Per Column ──")
missing = df.isnull().sum()
print(missing[missing > 0].to_string())
print(f"\n   Total missing values: {df.isnull().sum().sum()}")

print("\n── Class Distribution ──")
print(df["classification"].value_counts().to_string())

# ─────────────────────────────────────────────
# STEP 3 · Handle Missing Values
# ─────────────────────────────────────────────
"""
Strategy:
  • Numeric columns   → fill with the column **median**
    (median is robust to outliers in medical data)
  • Categorical columns → fill with the column **mode**
    (most frequently occurring value)
"""

print("\n▶ STEP 3 – Handling missing values …")

# Clean up whitespace in string columns first
for col in df.columns:
    if df[col].dtype == object:
        df[col] = df[col].str.strip()

# Clean the classification column (remove trailing punctuation)
df["classification"] = df["classification"].str.replace(r"[^a-zA-Z]", "", regex=True)

# Identify numeric and categorical columns
numeric_cols = [
    "age", "bp", "sg", "al", "su",
    "bgr", "bu", "sc", "sod", "pot",
    "hemo", "pcv", "wc", "rc",
]
categorical_cols = [
    "rbc", "pc", "pcc", "ba",
    "htn", "dm", "cad", "appet", "pe", "ane",
]

# Convert numeric columns that may have been read as strings
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Fill missing values
for col in numeric_cols:
    df[col].fillna(df[col].median(), inplace=True)

for col in categorical_cols:
    df[col].fillna(df[col].mode()[0], inplace=True)

# Also fill classification if needed
df["classification"].fillna(df["classification"].mode()[0], inplace=True)

print(f"   ✅ Missing values after cleaning: {df.isnull().sum().sum()}")

# ─────────────────────────────────────────────
# STEP 4 · Encode Categorical Variables
# ─────────────────────────────────────────────
"""
We convert categorical text values into numbers:
  • normal / abnormal     → 0 / 1
  • yes / no              → 1 / 0
  • present / notpresent  → 1 / 0
  • good / poor           → 0 / 1
  • ckd / notckd          → 1 / 0
Using a mapping dictionary makes the encoding transparent
and easy to document in a report.
"""

print("\n▶ STEP 4 – Encoding categorical variables …")

encoding_map = {
    "rbc":            {"normal": 0, "abnormal": 1},
    "pc":             {"normal": 0, "abnormal": 1},
    "pcc":            {"present": 1, "notpresent": 0},
    "ba":             {"present": 1, "notpresent": 0},
    "htn":            {"yes": 1, "no": 0},
    "dm":             {"yes": 1, "no": 0},
    "cad":            {"yes": 1, "no": 0},
    "appet":          {"good": 0, "poor": 1},
    "pe":             {"yes": 1, "no": 0},
    "ane":            {"yes": 1, "no": 0},
    "classification": {"ckd": 1, "notckd": 0},
}

for col, mapping in encoding_map.items():
    df[col] = df[col].map(mapping)

# In case mapping introduced NaN (unexpected values), fill with mode
for col in encoding_map:
    if df[col].isnull().any():
        df[col].fillna(df[col].mode()[0], inplace=True)

print("   ✅ All categorical columns encoded to numeric")
print("\n── Encoded Data (first 5 rows) ──")
print(df.head().to_string())

# ─────────────────────────────────────────────
# STEP 5 · Separate Features and Target
# ─────────────────────────────────────────────
"""
X = all 24 clinical features (independent variables)
y = classification column (1 = CKD, 0 = Not CKD)
"""

print("\n▶ STEP 5 – Separating features (X) and target (y) …")

X = df.drop("classification", axis=1)
y = df["classification"].astype(int)

print(f"   Features shape : {X.shape}")
print(f"   Target shape   : {y.shape}")
print(f"   CKD patients   : {(y == 1).sum()}")
print(f"   Non-CKD        : {(y == 0).sum()}")

# ─────────────────────────────────────────────
# STEP 6 · Train-Test Split (80 / 20)
# ─────────────────────────────────────────────
"""
We split the dataset into 80% training and 20% testing.
random_state=42 ensures reproducible results.
stratify=y keeps the CKD/non-CKD ratio balanced in both sets.
"""

print("\n▶ STEP 6 – Splitting into train / test sets (80/20) …")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

print(f"   Training set : {X_train.shape[0]} samples")
print(f"   Testing set  : {X_test.shape[0]} samples")

# ─────────────────────────────────────────────
# STEP 7 · Train Machine Learning Models
# ─────────────────────────────────────────────
"""
We train three classification models:
  1. Logistic Regression – a linear model, good baseline
  2. Decision Tree       – interpretable tree-based model
  3. Random Forest       – ensemble of decision trees (usually best)
"""

print("\n▶ STEP 7 – Training machine learning models …")

models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Decision Tree":       DecisionTreeClassifier(random_state=42),
    "Random Forest":       RandomForestClassifier(n_estimators=100, random_state=42),
}

trained_models = {}
for name, model in models.items():
    model.fit(X_train, y_train)
    trained_models[name] = model
    print(f"   ✅ {name} trained successfully")

# ─────────────────────────────────────────────
# STEP 8 · Evaluate the Models
# ─────────────────────────────────────────────
"""
For each model we compute:
  • Accuracy        – overall correct predictions / total
  • Confusion Matrix – TP, TN, FP, FN breakdown
  • Precision       – of all predicted CKD, how many are truly CKD
  • Recall          – of all actual CKD, how many were detected
"""

print("\n▶ STEP 8 – Evaluating model performance …")

results = {}

for name, model in trained_models.items():
    y_pred = model.predict(X_test)
    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec  = recall_score(y_test, y_pred)
    cm   = confusion_matrix(y_test, y_pred)

    results[name] = {
        "Accuracy":  round(acc  * 100, 2),
        "Precision": round(prec * 100, 2),
        "Recall":    round(rec  * 100, 2),
        "Confusion Matrix": cm,
    }

    print(f"\n   ── {name} ──")
    print(f"   Accuracy  : {acc  * 100:.2f}%")
    print(f"   Precision : {prec * 100:.2f}%")
    print(f"   Recall    : {rec  * 100:.2f}%")
    print(f"   Confusion Matrix:\n{cm}")
    print(f"\n   Classification Report:\n{classification_report(y_test, y_pred, target_names=['Not CKD', 'CKD'])}")

# ─────────────────────────────────────────────
# STEP 9 · Compare Models & Identify the Best
# ─────────────────────────────────────────────
"""
We create a comparison table and a bar chart so it's easy
to see which model performs best at a glance.
"""

print("\n▶ STEP 9 – Model comparison …")

comparison_df = pd.DataFrame({
    "Model":     list(results.keys()),
    "Accuracy":  [results[m]["Accuracy"]  for m in results],
    "Precision": [results[m]["Precision"] for m in results],
    "Recall":    [results[m]["Recall"]    for m in results],
})

print("\n" + comparison_df.to_string(index=False))

best_model_name = comparison_df.loc[comparison_df["Accuracy"].idxmax(), "Model"]
best_accuracy   = comparison_df["Accuracy"].max()
print(f"\n   🏆 Best Model: {best_model_name} with {best_accuracy}% accuracy")

# ── Bar chart ──
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(comparison_df))
width = 0.25

bars1 = ax.bar(x - width, comparison_df["Accuracy"],  width, label="Accuracy",  color="#2ecc71")
bars2 = ax.bar(x,         comparison_df["Precision"], width, label="Precision", color="#3498db")
bars3 = ax.bar(x + width, comparison_df["Recall"],    width, label="Recall",    color="#e74c3c")

ax.set_xlabel("Model", fontsize=12)
ax.set_ylabel("Score (%)", fontsize=12)
ax.set_title("CKD Prediction – Model Performance Comparison", fontsize=14, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(comparison_df["Model"], fontsize=10)
ax.set_ylim(0, 110)
ax.legend(fontsize=11)
ax.grid(axis="y", alpha=0.3)

# Add value labels on bars
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height:.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9)

plt.tight_layout()
chart_path = os.path.join(OUTPUT_DIR, "model_comparison.png")
plt.savefig(chart_path, dpi=150)
plt.close()
print(f"   📊 Comparison chart saved → {chart_path}")

# ── Confusion Matrix plots ──
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for idx, (name, res) in enumerate(results.items()):
    cm = res["Confusion Matrix"]
    ax = axes[idx]
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    ax.set_title(name, fontsize=11, fontweight="bold")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Not CKD", "CKD"])
    ax.set_yticklabels(["Not CKD", "CKD"])
    # Annotate cells
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black",
                    fontsize=14, fontweight="bold")

plt.tight_layout()
cm_path = os.path.join(OUTPUT_DIR, "confusion_matrices.png")
plt.savefig(cm_path, dpi=150)
plt.close()
print(f"   📊 Confusion matrices saved → {cm_path}")

# ─────────────────────────────────────────────
# STEP 10 · Save the Best Model as .pkl
# ─────────────────────────────────────────────
"""
We save the best-performing model using joblib so it can
be loaded later in a Flask/Django API or web application:
    model = joblib.load('best_ckd_model.pkl')
    prediction = model.predict(new_patient_data)
"""

print("\n▶ STEP 10 – Saving the best model …")

model_path = os.path.join(OUTPUT_DIR, "best_ckd_model.pkl")
joblib.dump(trained_models[best_model_name], model_path)

print(f"   ✅ {best_model_name} saved as → {model_path}")
print(f"   📦 Model can be loaded with: joblib.load('{model_path}')")

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("  PIPELINE COMPLETE")
print("=" * 60)
print(f"""
  Dataset         : {df.shape[0]} records × {df.shape[1]} columns
  Training set    : {X_train.shape[0]} samples
  Testing set     : {X_test.shape[0]} samples

  Model Results:
""")
for name in results:
    r = results[name]
    marker = " 🏆" if name == best_model_name else ""
    print(f"    {name:25s}  Acc: {r['Accuracy']:6.2f}%  Prec: {r['Precision']:6.2f}%  Rec: {r['Recall']:6.2f}%{marker}")

print(f"""
  Best Model      : {best_model_name}
  Saved to         : {model_path}

  Output files:
    • {chart_path}
    • {cm_path}
    • {model_path}
""")
print("=" * 60)
