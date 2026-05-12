"""
Convert the scikit-learn Random Forest .pkl model to a pure JSON format.
This eliminates the need for scikit-learn/numpy/pandas at runtime.
Run once locally: python convert_model.py
"""
import joblib
import json
import os

MODEL_PATH = os.path.join("output", "best_ckd_model.pkl")
OUTPUT_PATH = os.path.join("api", "model.json")

print(f"Loading model from {MODEL_PATH}...")
model = joblib.load(MODEL_PATH)

trees_data = []
for i, estimator in enumerate(model.estimators_):
    tree = estimator.tree_
    trees_data.append({
        "cl": tree.children_left.tolist(),
        "cr": tree.children_right.tolist(),
        "f": tree.feature.tolist(),
        "t": [round(float(x), 6) for x in tree.threshold],
        "v": [[round(float(c), 1) for c in node[0]] for node in tree.value],
    })

model_data = {
    "n_classes": int(model.n_classes_),
    "classes": model.classes_.tolist(),
    "n_estimators": len(model.estimators_),
    "feature_importances": [round(float(x), 6) for x in model.feature_importances_],
    "trees": trees_data,
}

with open(OUTPUT_PATH, "w") as f:
    json.dump(model_data, f, separators=(",", ":"))

size_kb = os.path.getsize(OUTPUT_PATH) / 1024
print(f"✅ Model exported to {OUTPUT_PATH} ({size_kb:.1f} KB)")
print(f"   {model_data['n_estimators']} trees, {model_data['n_classes']} classes")
