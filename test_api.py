"""
============================================================
  CKD Prediction API – Test Script
============================================================
  This script sends sample patient data to the Flask API
  and prints the prediction results.

  How to use:
    1. Start the API server:   python app.py
    2. In another terminal:    python test_api.py

  Author : Ayush (college project)
============================================================
"""

import requests
import json

# ─────────────────────────────────────────────
# API endpoint URL
# ─────────────────────────────────────────────
API_URL = "http://localhost:5000/predict"


# ─────────────────────────────────────────────
# Test Case 1: Patient likely to have CKD
# ─────────────────────────────────────────────
"""
This patient has several indicators of kidney disease:
  - High blood sugar (bgr=490), high blood urea (bu=100)
  - Low hemoglobin (hemo=9.4), low red blood cell count (rc=3.7)
  - Abnormal RBC and PC, albumin present in urine (al=4)
  - Hypertension (htn=yes), diabetes (dm=yes), anemia (ane=yes)
"""

ckd_patient = {
    "age": 60,
    "bp": 90,
    "sg": 1.010,
    "al": 4,
    "su": 0,
    "rbc": "abnormal",
    "pc": "abnormal",
    "pcc": "present",
    "ba": "present",
    "bgr": 490,
    "bu": 100,
    "sc": 4.0,
    "sod": 125,
    "pot": 4.0,
    "hemo": 9.4,
    "pcv": 28,
    "wc": 12200,
    "rc": 3.7,
    "htn": "yes",
    "dm": "yes",
    "cad": "no",
    "appet": "poor",
    "pe": "yes",
    "ane": "yes",
}

# ─────────────────────────────────────────────
# Test Case 2: Healthy patient (Not CKD)
# ─────────────────────────────────────────────
"""
This patient has normal indicators across the board:
  - Normal blood sugar, creatinine, and urea levels
  - Good hemoglobin and RBC counts
  - No hypertension, diabetes, or edema
"""

healthy_patient = {
    "age": 30,
    "bp": 70,
    "sg": 1.025,
    "al": 0,
    "su": 0,
    "rbc": "normal",
    "pc": "normal",
    "pcc": "notpresent",
    "ba": "notpresent",
    "bgr": 100,
    "bu": 20,
    "sc": 0.8,
    "sod": 140,
    "pot": 4.5,
    "hemo": 15.0,
    "pcv": 44,
    "wc": 7500,
    "rc": 5.0,
    "htn": "no",
    "dm": "no",
    "cad": "no",
    "appet": "good",
    "pe": "no",
    "ane": "no",
}


# ─────────────────────────────────────────────
# Helper function to send a request and print results
# ─────────────────────────────────────────────
def test_prediction(label, patient_data):
    """
    Sends patient data to the API and prints the response.

    Parameters
    ----------
    label : str
        A description for this test case (e.g. "CKD Patient")
    patient_data : dict
        The 24-feature patient dictionary
    """
    print(f"\n{'─' * 50}")
    print(f"  TEST: {label}")
    print(f"{'─' * 50}")

    try:
        # Send POST request with JSON data
        response = requests.post(
            API_URL,
            json=patient_data,               # automatically sets Content-Type
            headers={"Content-Type": "application/json"},
        )

        # Parse the JSON response
        result = response.json()

        # Pretty-print the result
        print(f"  Status Code : {response.status_code}")
        print(f"  Prediction  : {result.get('prediction', 'N/A')}")
        print(f"  Message     : {result.get('message', 'N/A')}")

        # Print probability scores if available
        prob = result.get("probability", {})
        if prob:
            print(f"  Probability :")
            print(f"      CKD     : {prob.get('CKD', 'N/A')}")
            print(f"      Not CKD : {prob.get('Not CKD', 'N/A')}")

        print(f"\n  Full Response:")
        print(f"  {json.dumps(result, indent=4)}")

    except requests.exceptions.ConnectionError:
        print("  ❌ ERROR: Could not connect to the API.")
        print("     Make sure the server is running: python app.py")


# ─────────────────────────────────────────────
# Run the tests
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  CKD PREDICTION API – TEST SUITE")
    print("=" * 50)

    # Test 1: CKD patient → should predict "CKD"
    test_prediction("CKD Patient (expected: CKD)", ckd_patient)

    # Test 2: Healthy patient → should predict "Not CKD"
    test_prediction("Healthy Patient (expected: Not CKD)", healthy_patient)

    print(f"\n{'=' * 50}")
    print("  TESTS COMPLETE")
    print(f"{'=' * 50}")
