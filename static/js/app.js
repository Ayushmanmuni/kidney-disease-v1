/**
 * ============================================================
 *  CKD Prediction System — Frontend Application Logic
 * ============================================================
 *  Handles: dual-mode (Patient/Doctor) forms, tooltips,
 *  health indicators, API calls, result rendering, easter egg.
 *
 *  Author: Ayushmaan Muni (B.Tech IT Project)
 * ============================================================
 */

/* ─────────────────────────────────────────────
   1. FIELD CONFIGURATION (Doctor Mode — 24 features)
   ───────────────────────────────────────────── */

const STEPS = [
  { id: 1, label: "Basic Vitals", icon: "💉" },
  { id: 2, label: "Lab Tests", icon: "🔬" },
  { id: 3, label: "Blood Work", icon: "🧪" },
  { id: 4, label: "Medical History", icon: "📋" },
];

const FIELDS = {
  age: {
    step: 1, label: "Age", unit: "years", type: "number", min: 1, max: 100, step_val: 1, placeholder: "e.g. 48",
    tooltip: "Patient's age in years. CKD risk increases significantly after age 60.",
    ranges: [{ max: 40, lbl: "Young", cls: "success" }, { max: 60, lbl: "Middle-aged", cls: "warning" }, { max: 100, lbl: "Senior", cls: "danger" }]
  },
  bp: {
    step: 1, label: "Blood Pressure", unit: "mm/Hg", type: "number", min: 50, max: 180, step_val: 1, placeholder: "e.g. 80",
    tooltip: "Diastolic blood pressure. Normal: 60–80 mm/Hg. High BP damages kidney blood vessels over time.",
    normalRange: "60–80", ranges: [{ max: 60, lbl: "Low", cls: "warning" }, { max: 80, lbl: "Normal", cls: "success" }, { max: 90, lbl: "Elevated", cls: "warning" }, { max: 180, lbl: "High", cls: "danger" }]
  },
  sg: {
    step: 1, label: "Specific Gravity", unit: "", type: "select", options: ["1.005", "1.010", "1.015", "1.020", "1.025"],
    tooltip: "Urine specific gravity measures kidney's ability to concentrate urine. Normal: 1.015–1.025."
  },
  al: {
    step: 1, label: "Albumin", unit: "0–5", type: "select", options: [
      { v: "0", t: "0 – Normal" }, { v: "1", t: "1 – Trace" }, { v: "2", t: "2 – Mild" },
      { v: "3", t: "3 – Moderate" }, { v: "4", t: "4 – High" }, { v: "5", t: "5 – Very High" }],
    tooltip: "Albumin in urine (0–5). 0 is healthy. Higher levels may indicate kidney damage (proteinuria)."
  },
  su: {
    step: 1, label: "Sugar", unit: "0–5", type: "select", options: [
      { v: "0", t: "0 – Normal" }, { v: "1", t: "1 – Trace" }, { v: "2", t: "2 – Mild" },
      { v: "3", t: "3 – Moderate" }, { v: "4", t: "4 – High" }, { v: "5", t: "5 – Very High" }],
    tooltip: "Sugar in urine (0–5). 0 is normal. Presence may indicate diabetes or a kidney threshold issue."
  },
  rbc: {
    step: 2, label: "Red Blood Cells (RBC)", type: "toggle", options: ["normal", "abnormal"],
    tooltip: "RBC in urine. Normally not present. Abnormal may indicate kidney stones, infection, or glomerular damage."
  },
  pc: {
    step: 2, label: "Pus Cells (PC)", type: "toggle", options: ["normal", "abnormal"],
    tooltip: "Pus cells in urine. Normal is healthy. Abnormal suggests urinary tract infection or kidney inflammation."
  },
  pcc: {
    step: 2, label: "Pus Cell Clumps (PCC)", type: "toggle", options: ["notpresent", "present"],
    labels: { notpresent: "Not Present", present: "Present" },
    tooltip: "Pus cell clumps indicate severe infection. Not Present is the healthy condition."
  },
  ba: {
    step: 2, label: "Bacteria (BA)", type: "toggle", options: ["notpresent", "present"],
    labels: { notpresent: "Not Present", present: "Present" },
    tooltip: "Bacteria in urine. Not Present is normal. Presence indicates urinary tract infection (UTI)."
  },
  bgr: {
    step: 3, label: "Blood Glucose Random", unit: "mg/dL", type: "number", min: 20, max: 500, step_val: 1, placeholder: "e.g. 120",
    tooltip: "Random blood glucose level. Normal: 70–140 mg/dL. High values suggest diabetes, a key CKD risk factor.",
    normalRange: "70–140", ranges: [{ max: 70, lbl: "Low", cls: "warning" }, { max: 140, lbl: "Normal", cls: "success" }, { max: 200, lbl: "Elevated", cls: "warning" }, { max: 500, lbl: "High", cls: "danger" }]
  },
  bu: {
    step: 3, label: "Blood Urea", unit: "mg/dL", type: "number", min: 1, max: 400, step_val: 0.1, placeholder: "e.g. 36",
    tooltip: "Blood urea nitrogen. Normal: 7–20 mg/dL. Elevated levels indicate kidneys are not filtering urea properly.",
    normalRange: "7–20", ranges: [{ max: 7, lbl: "Low", cls: "warning" }, { max: 20, lbl: "Normal", cls: "success" }, { max: 40, lbl: "Elevated", cls: "warning" }, { max: 400, lbl: "High", cls: "danger" }]
  },
  sc: {
    step: 3, label: "Serum Creatinine", unit: "mg/dL", type: "number", min: 0.1, max: 80, step_val: 0.1, placeholder: "e.g. 1.2",
    tooltip: "Serum creatinine is a key kidney function marker. Normal: 0.6–1.2 mg/dL. High values are a strong CKD indicator.",
    normalRange: "0.6–1.2", ranges: [{ max: 0.6, lbl: "Low", cls: "warning" }, { max: 1.2, lbl: "Normal", cls: "success" }, { max: 2.0, lbl: "Elevated", cls: "warning" }, { max: 80, lbl: "High", cls: "danger" }]
  },
  sod: {
    step: 3, label: "Sodium", unit: "mEq/L", type: "number", min: 4, max: 165, step_val: 0.1, placeholder: "e.g. 138",
    tooltip: "Blood sodium level. Normal: 136–145 mEq/L. Abnormal sodium may indicate kidney dysfunction.",
    normalRange: "136–145", ranges: [{ max: 136, lbl: "Low", cls: "warning" }, { max: 145, lbl: "Normal", cls: "success" }, { max: 165, lbl: "High", cls: "danger" }]
  },
  pot: {
    step: 3, label: "Potassium", unit: "mEq/L", type: "number", min: 2, max: 50, step_val: 0.1, placeholder: "e.g. 4.5",
    tooltip: "Blood potassium. Normal: 3.5–5.0 mEq/L. Kidneys regulate potassium; abnormal levels are concerning.",
    normalRange: "3.5–5.0", ranges: [{ max: 3.5, lbl: "Low", cls: "warning" }, { max: 5.0, lbl: "Normal", cls: "success" }, { max: 50, lbl: "High", cls: "danger" }]
  },
  hemo: {
    step: 3, label: "Hemoglobin", unit: "g/dL", type: "number", min: 3, max: 18, step_val: 0.1, placeholder: "e.g. 15.4",
    tooltip: "Hemoglobin level. Normal: 12–17 g/dL. Low hemoglobin (anemia) is common in CKD patients.",
    normalRange: "12–17", ranges: [{ max: 12, lbl: "Low", cls: "danger" }, { max: 17, lbl: "Normal", cls: "success" }, { max: 18, lbl: "High", cls: "warning" }]
  },
  pcv: {
    step: 3, label: "Packed Cell Volume", unit: "%", type: "number", min: 9, max: 55, step_val: 1, placeholder: "e.g. 44",
    tooltip: "PCV (hematocrit). Normal: 36–50%. Low PCV suggests anemia, which is a CKD complication.",
    normalRange: "36–50", ranges: [{ max: 36, lbl: "Low", cls: "danger" }, { max: 50, lbl: "Normal", cls: "success" }, { max: 55, lbl: "High", cls: "warning" }]
  },
  wc: {
    step: 3, label: "White Blood Cell Count", unit: "/cmm", type: "number", min: 2000, max: 27000, step_val: 100, placeholder: "e.g. 7800",
    tooltip: "WBC count. Normal: 4000–11000 /cmm. Elevated WBC may indicate infection or inflammation.",
    normalRange: "4000–11000", ranges: [{ max: 4000, lbl: "Low", cls: "warning" }, { max: 11000, lbl: "Normal", cls: "success" }, { max: 27000, lbl: "High", cls: "danger" }]
  },
  rc: {
    step: 3, label: "Red Blood Cell Count", unit: "mill/cmm", type: "number", min: 2, max: 8, step_val: 0.1, placeholder: "e.g. 5.2",
    tooltip: "RBC count in blood. Normal: 4.5–5.5 million/cmm. Low RBC is a sign of anemia related to CKD.",
    normalRange: "4.5–5.5", ranges: [{ max: 4.5, lbl: "Low", cls: "danger" }, { max: 5.5, lbl: "Normal", cls: "success" }, { max: 8, lbl: "High", cls: "warning" }]
  },
  htn: {
    step: 4, label: "Hypertension", type: "toggle", options: ["no", "yes"],
    tooltip: "Does the patient have high blood pressure? Hypertension is both a cause and consequence of CKD."
  },
  dm: {
    step: 4, label: "Diabetes Mellitus", type: "toggle", options: ["no", "yes"],
    tooltip: "Does the patient have diabetes? Diabetes is the leading cause of kidney disease worldwide."
  },
  cad: {
    step: 4, label: "Coronary Artery Disease", type: "toggle", options: ["no", "yes"],
    tooltip: "Heart disease history. CAD shares risk factors with CKD (hypertension, diabetes, obesity)."
  },
  appet: {
    step: 4, label: "Appetite", type: "toggle", options: ["good", "poor"],
    tooltip: "Patient's appetite status. Poor appetite is a common symptom in advanced CKD (uremia)."
  },
  pe: {
    step: 4, label: "Pedal Edema", type: "toggle", options: ["no", "yes"],
    tooltip: "Swelling in legs/feet. Indicates fluid retention, which occurs when kidneys can't remove excess fluid."
  },
  ane: {
    step: 4, label: "Anemia", type: "toggle", options: ["no", "yes"],
    tooltip: "Is the patient anemic? Kidneys produce erythropoietin; CKD reduces this, causing anemia."
  },
};

const FEATURE_NAMES = {
  age: "Age", bp: "Blood Pressure", sg: "Specific Gravity", al: "Albumin", su: "Sugar",
  rbc: "RBC (Urine)", pc: "Pus Cells", pcc: "Pus Cell Clumps", ba: "Bacteria",
  bgr: "Blood Glucose", bu: "Blood Urea", sc: "Serum Creatinine", sod: "Sodium", pot: "Potassium",
  hemo: "Hemoglobin", pcv: "Packed Cell Vol.", wc: "WBC Count", rc: "RBC Count",
  htn: "Hypertension", dm: "Diabetes", cad: "Heart Disease", appet: "Appetite", pe: "Pedal Edema", ane: "Anemia"
};

/* ─────────────────────────────────────────────
   1b. PATIENT MODE CONFIGURATION
   Simplified fields for non-medical users
   ───────────────────────────────────────────── */

const PATIENT_FIELDS = {
  age: {
    label: "Your Age", unit: "years", type: "number", min: 1, max: 100, step_val: 1,
    placeholder: "e.g. 48",
    tooltip: "Your age in years. CKD risk increases after age 60.",
    ranges: [{ max: 40, lbl: "Young", cls: "success" }, { max: 60, lbl: "Middle-aged", cls: "warning" }, { max: 100, lbl: "Senior", cls: "danger" }]
  },
  bp: {
    label: "Blood Pressure (Diastolic)", unit: "mm/Hg", type: "number", min: 50, max: 180, step_val: 1,
    placeholder: "e.g. 80",
    tooltip: "Your diastolic blood pressure reading. Normal: 60–80 mm/Hg.",
    normalRange: "60–80",
    ranges: [{ max: 60, lbl: "Low", cls: "warning" }, { max: 80, lbl: "Normal", cls: "success" }, { max: 90, lbl: "Elevated", cls: "warning" }, { max: 180, lbl: "High", cls: "danger" }]
  },
  htn: {
    label: "Do you have High Blood Pressure?", type: "toggle", options: ["no", "yes"],
    tooltip: "Have you been diagnosed with hypertension (high blood pressure)?"
  },
  dm: {
    label: "Do you have Diabetes?", type: "toggle", options: ["no", "yes"],
    tooltip: "Have you been diagnosed with diabetes mellitus?"
  },
  hemo: {
    label: "Hemoglobin Level", unit: "g/dL", type: "number", min: 3, max: 18, step_val: 0.1,
    placeholder: "e.g. 15.4",
    tooltip: "Hemoglobin from your recent blood test. Normal: 12–17 g/dL.",
    normalRange: "12–17",
    ranges: [{ max: 12, lbl: "Low", cls: "danger" }, { max: 17, lbl: "Normal", cls: "success" }, { max: 18, lbl: "High", cls: "warning" }]
  },
  sc: {
    label: "Serum Creatinine", unit: "mg/dL", type: "number", min: 0.1, max: 80, step_val: 0.1,
    placeholder: "e.g. 1.2",
    tooltip: "Serum creatinine from your blood test. Normal: 0.6–1.2 mg/dL. A key kidney function marker.",
    normalRange: "0.6–1.2",
    ranges: [{ max: 0.6, lbl: "Low", cls: "warning" }, { max: 1.2, lbl: "Normal", cls: "success" }, { max: 2.0, lbl: "Elevated", cls: "warning" }, { max: 80, lbl: "High", cls: "danger" }]
  },
  pe: {
    label: "Swelling in Legs/Feet?", type: "toggle", options: ["no", "yes"],
    tooltip: "Do you experience swelling (edema) in your legs or feet? This can indicate fluid retention."
  },
  ane: {
    label: "Diagnosed with Anemia?", type: "toggle", options: ["no", "yes"],
    tooltip: "Have you been told you are anemic (low red blood cells)?"
  }
};

const PATIENT_DEFAULTS = {
  sg: "1.020", al: "0", su: "0",
  rbc: "normal", pc: "normal", pcc: "notpresent", ba: "notpresent",
  bgr: 120, bu: 18, sod: 140, pot: 4.5,
  pcv: 44, wc: 7800, rc: 5.0,
  cad: "no", appet: "good"
};

/* ─────────────────────────────────────────────
   2. STATE
   ───────────────────────────────────────────── */
let currentStep = 1;
const totalSteps = 4;
let currentMode = "";  // "patient" or "doctor"
let submittedData = {};

/* ─────────────────────────────────────────────
   3. THEME TOGGLE
   ───────────────────────────────────────────── */
function initTheme() {
  const saved = localStorage.getItem("ckd-theme");
  if (saved === "dark") document.documentElement.setAttribute("data-theme", "dark");
  document.getElementById("theme-toggle").addEventListener("click", () => {
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    document.documentElement.setAttribute("data-theme", isDark ? "light" : "dark");
    localStorage.setItem("ckd-theme", isDark ? "light" : "dark");
  });
}

/* ─────────────────────────────────────────────
   4. FORM GENERATION (Doctor Mode)
   Dynamically builds form fields from FIELDS config
   ───────────────────────────────────────────── */
function buildForm() {
  for (const [key, f] of Object.entries(FIELDS)) {
    const container = document.getElementById(`fields-step-${f.step}`);
    if (!container) continue;
    const wrapper = document.createElement("div");
    wrapper.className = "field-wrapper";

    const label = document.createElement("label");
    label.setAttribute("for", key);
    label.innerHTML = f.label;
    if (f.unit) label.innerHTML += ` <span class="field-unit">(${f.unit})</span>`;
    if (f.tooltip) {
      const tip = document.createElement("span");
      tip.className = "field-tooltip-icon";
      tip.textContent = "?";
      tip.dataset.tip = f.tooltip;
      if (f.normalRange) tip.dataset.tip += `\n\n✅ Normal range: ${f.normalRange}`;
      tip.addEventListener("mouseenter", showTooltip);
      tip.addEventListener("mouseleave", hideTooltip);
      tip.addEventListener("focus", showTooltip);
      tip.addEventListener("blur", hideTooltip);
      tip.tabIndex = 0;
      label.appendChild(tip);
    }
    wrapper.appendChild(label);

    if (f.type === "number") {
      const input = document.createElement("input");
      input.type = "number"; input.id = key; input.name = key; input.required = true;
      input.min = f.min; input.max = f.max; input.step = f.step_val;
      input.placeholder = f.placeholder || "";
      if (f.ranges) {
        input.addEventListener("input", () => updateHealthBadge(key, input.value, f.ranges, wrapper));
      }
      wrapper.appendChild(input);
    } else if (f.type === "select") {
      const sel = document.createElement("select");
      sel.id = key; sel.name = key; sel.required = true;
      const def = document.createElement("option"); def.value = ""; def.textContent = "Select value"; def.disabled = true; def.selected = true;
      sel.appendChild(def);
      f.options.forEach(opt => {
        const o = document.createElement("option");
        if (typeof opt === "object") { o.value = opt.v; o.textContent = opt.t; }
        else { o.value = opt; o.textContent = opt; }
        sel.appendChild(o);
      });
      wrapper.appendChild(sel);
    } else if (f.type === "toggle") {
      const group = document.createElement("div");
      group.className = "toggle-group"; group.dataset.field = key;
      f.options.forEach((val, i) => {
        const btn = document.createElement("button");
        btn.type = "button"; btn.className = "toggle-btn" + (i === 0 ? " active" : "");
        btn.dataset.value = val;
        const displayLabel = f.labels ? f.labels[val] : val.charAt(0).toUpperCase() + val.slice(1);
        btn.textContent = displayLabel;
        btn.addEventListener("click", () => {
          group.querySelectorAll(".toggle-btn").forEach(b => b.classList.remove("active"));
          btn.classList.add("active");
        });
        group.appendChild(btn);
      });
      wrapper.appendChild(group);
    }

    if (f.ranges) {
      const badge = document.createElement("div");
      badge.className = "field-health-badge-container"; badge.id = `badge-${key}`;
      wrapper.appendChild(badge);
    }

    container.appendChild(wrapper);
  }
}

function updateHealthBadge(key, value, ranges, wrapper) {
  const container = wrapper.querySelector(".field-health-badge-container");
  if (!container) return;
  const val = parseFloat(value);
  if (isNaN(val)) { container.innerHTML = ""; return; }
  for (const r of ranges) {
    if (val <= r.max) {
      container.innerHTML = `<span class="field-health-badge badge-${r.cls}">${r.lbl}</span>`;
      return;
    }
  }
  container.innerHTML = "";
}

/* ─────────────────────────────────────────────
   4b. FORM GENERATION (Patient Mode)
   Simplified form for non-medical users
   ───────────────────────────────────────────── */
function buildPatientForm() {
  const container = document.getElementById("patient-fields");
  if (!container) return;

  for (const [key, f] of Object.entries(PATIENT_FIELDS)) {
    const wrapper = document.createElement("div");
    wrapper.className = "field-wrapper";

    const label = document.createElement("label");
    label.setAttribute("for", `patient-${key}`);
    label.innerHTML = f.label;
    if (f.unit) label.innerHTML += ` <span class="field-unit">(${f.unit})</span>`;
    if (f.tooltip) {
      const tip = document.createElement("span");
      tip.className = "field-tooltip-icon";
      tip.textContent = "?";
      tip.dataset.tip = f.tooltip;
      if (f.normalRange) tip.dataset.tip += `\n\n✅ Normal range: ${f.normalRange}`;
      tip.addEventListener("mouseenter", showTooltip);
      tip.addEventListener("mouseleave", hideTooltip);
      tip.addEventListener("focus", showTooltip);
      tip.addEventListener("blur", hideTooltip);
      tip.tabIndex = 0;
      label.appendChild(tip);
    }
    wrapper.appendChild(label);

    if (f.type === "number") {
      const input = document.createElement("input");
      input.type = "number"; input.id = `patient-${key}`; input.name = key; input.required = true;
      input.min = f.min; input.max = f.max; input.step = f.step_val;
      input.placeholder = f.placeholder || "";
      if (f.ranges) {
        input.addEventListener("input", () => updateHealthBadge(`patient-${key}`, input.value, f.ranges, wrapper));
      }
      wrapper.appendChild(input);
    } else if (f.type === "toggle") {
      const group = document.createElement("div");
      group.className = "toggle-group"; group.dataset.field = `patient-${key}`;
      f.options.forEach((val, i) => {
        const btn = document.createElement("button");
        btn.type = "button"; btn.className = "toggle-btn" + (i === 0 ? " active" : "");
        btn.dataset.value = val;
        btn.textContent = val.charAt(0).toUpperCase() + val.slice(1);
        btn.addEventListener("click", () => {
          group.querySelectorAll(".toggle-btn").forEach(b => b.classList.remove("active"));
          btn.classList.add("active");
        });
        group.appendChild(btn);
      });
      wrapper.appendChild(group);
    }

    if (f.ranges) {
      const badge = document.createElement("div");
      badge.className = "field-health-badge-container"; badge.id = `badge-patient-${key}`;
      wrapper.appendChild(badge);
    }

    container.appendChild(wrapper);
  }
}

/* ─────────────────────────────────────────────
   5. WIZARD PROGRESS BAR
   ───────────────────────────────────────────── */
function buildProgress() {
  const container = document.getElementById("progress-steps");
  STEPS.forEach((s, i) => {
    const el = document.createElement("div");
    el.className = "p-step" + (i === 0 ? " active" : "");
    el.dataset.step = s.id;
    el.innerHTML = `<div class="p-step-circle">${s.id}</div><span class="p-step-label">${s.label}</span>`;
    container.appendChild(el);
  });
}

function updateProgress() {
  document.querySelectorAll(".p-step").forEach(el => {
    const s = parseInt(el.dataset.step);
    el.classList.toggle("active", s === currentStep);
    el.classList.toggle("done", s < currentStep);
    if (s < currentStep) el.querySelector(".p-step-circle").textContent = "✓";
    else el.querySelector(".p-step-circle").textContent = s;
  });
  const pct = ((currentStep - 1) / (totalSteps - 1)) * 100;
  document.getElementById("progress-fill").style.width = pct + "%";
  document.getElementById("step-counter").textContent = `Step ${currentStep} of ${totalSteps}`;
}

/* ─────────────────────────────────────────────
   6. FORM NAVIGATION (Doctor Mode)
   ───────────────────────────────────────────── */
function initNavigation() {
  const prevBtn = document.getElementById("prev-btn");
  const nextBtn = document.getElementById("next-btn");

  nextBtn.addEventListener("click", () => {
    if (currentStep < totalSteps) {
      if (!validateStep(currentStep)) return;
      currentStep++;
      showStep(currentStep);
    } else {
      if (!validateStep(currentStep)) return;
      submitForm();
    }
  });

  prevBtn.addEventListener("click", () => {
    if (currentStep > 1) { currentStep--; showStep(currentStep); }
  });
}

function showStep(n) {
  document.querySelectorAll(".form-step").forEach(el => el.classList.remove("active"));
  const target = document.getElementById(`step-${n}`);
  if (target) target.classList.add("active");

  document.getElementById("prev-btn").disabled = (n === 1);
  const nextBtn = document.getElementById("next-btn");
  if (n === totalSteps) {
    nextBtn.textContent = "🔬 Analyze Risk";
    nextBtn.className = "btn btn-submit";
  } else {
    nextBtn.textContent = "Next Step →";
    nextBtn.className = "btn btn-primary";
  }
  updateProgress();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function validateStep(stepNum) {
  const container = document.getElementById(`fields-step-${stepNum}`);
  const inputs = container.querySelectorAll("input, select");
  let valid = true;
  inputs.forEach(input => {
    if (input.required && !input.value) {
      input.style.borderColor = "var(--danger)";
      valid = false;
      setTimeout(() => { input.style.borderColor = ""; }, 2000);
    }
  });
  if (!valid) {
    container.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  return valid;
}

/* ─────────────────────────────────────────────
   7. TOOLTIP SYSTEM
   ───────────────────────────────────────────── */
function showTooltip(e) {
  const tip = document.getElementById("tooltip");
  const content = document.getElementById("tooltip-content");
  content.textContent = e.target.dataset.tip;
  tip.style.display = "block";
  const rect = e.target.getBoundingClientRect();
  tip.style.left = Math.min(rect.left, window.innerWidth - 320) + "px";
  tip.style.top = (rect.bottom + 8) + "px";
}

function hideTooltip() {
  document.getElementById("tooltip").style.display = "none";
}

/* ─────────────────────────────────────────────
   8. FORM SUBMISSION & API CALL
   ───────────────────────────────────────────── */
function collectFormData() {
  const data = {};
  for (const key of Object.keys(FIELDS)) {
    const f = FIELDS[key];
    if (f.type === "toggle") {
      const group = document.querySelector(`.toggle-group[data-field="${key}"]`);
      const active = group ? group.querySelector(".toggle-btn.active") : null;
      data[key] = active ? active.dataset.value : f.options[0];
    } else {
      const el = document.getElementById(key);
      data[key] = el ? el.value : "";
    }
  }
  console.log("[CKD] Doctor mode — collected form data:", data);
  return data;
}

function collectPatientData() {
  const data = {};
  for (const key of Object.keys(PATIENT_FIELDS)) {
    const f = PATIENT_FIELDS[key];
    if (f.type === "toggle") {
      const group = document.querySelector(`.toggle-group[data-field="patient-${key}"]`);
      const active = group ? group.querySelector(".toggle-btn.active") : null;
      data[key] = active ? active.dataset.value : f.options[0];
    } else {
      const el = document.getElementById(`patient-${key}`);
      data[key] = el ? el.value : "";
    }
  }
  console.log("[CKD] Patient mode — collected patient data:", data);
  return data;
}

function buildPatientPayload(patientData) {
  const payload = {};

  // Start with safe defaults for all 24 parameters
  for (const [key, val] of Object.entries(PATIENT_DEFAULTS)) {
    payload[key] = val;
  }

  // Override with patient-provided values
  for (const [key, val] of Object.entries(patientData)) {
    if (val !== "" && val !== undefined && val !== null) {
      payload[key] = val;
    }
  }

  // Smart adjustments based on provided data
  const hemo = parseFloat(patientData.hemo);
  if (!isNaN(hemo)) {
    payload.pcv = Math.round(hemo * 3);
    payload.rc = Math.round((hemo / 3) * 10) / 10;
  }

  if (patientData.dm === "yes") {
    payload.bgr = 200;  // diabetic patients tend to have higher glucose
    payload.su = "2";
  }

  if (patientData.pe === "yes" || patientData.ane === "yes") {
    payload.appet = "poor";
  }

  const sc = parseFloat(patientData.sc);
  if (!isNaN(sc) && sc > 1.5) {
    payload.al = "2";   // elevated creatinine often correlates with albumin in urine
    payload.bu = Math.max(payload.bu, sc * 15);
  }

  if (patientData.htn === "yes" && patientData.dm === "yes") {
    payload.cad = "yes";  // comorbidity correlation
  }

  console.log("[CKD] Patient mode — full payload (with defaults):", payload);
  return payload;
}

function validatePatientForm() {
  const container = document.getElementById("patient-fields");
  const inputs = container.querySelectorAll("input[type='number']");
  let valid = true;
  inputs.forEach(input => {
    if (input.required && !input.value) {
      input.style.borderColor = "var(--danger)";
      valid = false;
      setTimeout(() => { input.style.borderColor = ""; }, 2000);
    }
  });
  if (!valid) {
    container.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  return valid;
}

async function submitForm() {
  const data = collectFormData();
  submittedData = data;
  console.log("[CKD] Submitting doctor mode data to /predict...");

  showSection("loading");

  try {
    const resp = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    console.log("[CKD] API response status:", resp.status);

    const result = await resp.json();
    console.log("[CKD] API response body:", result);

    if (!resp.ok || !result.success) {
      console.error("[CKD] API error:", result.error);
      alert("Error: " + (result.error || "Prediction failed. Please check your inputs."));
      showSection("prediction");
      return;
    }

    setTimeout(() => {
      try {
        renderResults(result);
      } catch (err) {
        console.error("[CKD] Error rendering results:", err);
        alert("Error displaying results: " + err.message);
        showSection("prediction");
      }
    }, 1200);
  } catch (err) {
    console.error("[CKD] Fetch error:", err);
    alert("Connection error: Could not reach the prediction server. Is it running?");
    showSection("prediction");
  }
}

async function submitPatientForm() {
  if (!validatePatientForm()) return;

  const patientData = collectPatientData();
  const fullPayload = buildPatientPayload(patientData);
  submittedData = fullPayload;
  console.log("[CKD] Submitting patient mode data to /predict...");

  showSection("loading");

  try {
    const resp = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fullPayload),
    });
    console.log("[CKD] API response status:", resp.status);

    const result = await resp.json();
    console.log("[CKD] API response body:", result);

    if (!resp.ok || !result.success) {
      console.error("[CKD] API error:", result.error);
      alert("Error: " + (result.error || "Prediction failed. Please try again."));
      showSection("patient-prediction");
      return;
    }

    setTimeout(() => {
      try {
        renderResults(result);
      } catch (err) {
        console.error("[CKD] Error rendering results:", err);
        alert("Error displaying results: " + err.message);
        showSection("patient-prediction");
      }
    }, 1200);
  } catch (err) {
    console.error("[CKD] Fetch error:", err);
    alert("Connection error: Could not reach the prediction server. Is it running?");
    showSection("patient-prediction");
  }
}

/* ─────────────────────────────────────────────
   9. SECTION VISIBILITY
   ───────────────────────────────────────────── */
function showSection(id) {
  console.log("[CKD] showSection:", id);
  const homepage = document.getElementById("homepage");
  const allSections = ["prediction", "patient-prediction", "loading", "results"];

  if (id === "homepage") {
    homepage.style.display = "";
    allSections.forEach(s => {
      const el = document.getElementById(s);
      if (el) el.style.display = "none";
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }

  homepage.style.display = "none";
  allSections.forEach(s => {
    const el = document.getElementById(s);
    if (el) el.style.display = s === id ? "" : "none";
  });
}

function goHome() {
  currentMode = "";
  showSection("homepage");

  // Reset doctor form
  const ckdForm = document.getElementById("ckd-form");
  if (ckdForm) ckdForm.reset();
  document.querySelectorAll("#prediction .toggle-group").forEach(g => {
    g.querySelectorAll(".toggle-btn").forEach((b, i) => b.classList.toggle("active", i === 0));
  });
  document.querySelectorAll(".field-health-badge-container").forEach(c => c.innerHTML = "");
  currentStep = 1;
  showStep(1);

  // Reset patient form
  const patientForm = document.getElementById("patient-form");
  if (patientForm) patientForm.reset();
  document.querySelectorAll("#patient-prediction .toggle-group").forEach(g => {
    g.querySelectorAll(".toggle-btn").forEach((b, i) => b.classList.toggle("active", i === 0));
  });
}

/* ─────────────────────────────────────────────
   9b. DEMO AUTO-FILL
   Pre-fills form with sample patient data (Doctor Mode)
   ───────────────────────────────────────────── */
const DEMO_DATA = {
  ckd: {
    age: 60, bp: 90, sg: "1.010", al: "4", su: "0",
    rbc: "abnormal", pc: "abnormal", pcc: "present", ba: "present",
    bgr: 490, bu: 100, sc: 4.0, sod: 125, pot: 4.0,
    hemo: 9.4, pcv: 28, wc: 12200, rc: 3.7,
    htn: "yes", dm: "yes", cad: "no", appet: "poor", pe: "yes", ane: "yes"
  },
  healthy: {
    age: 30, bp: 70, sg: "1.025", al: "0", su: "0",
    rbc: "normal", pc: "normal", pcc: "notpresent", ba: "notpresent",
    bgr: 100, bu: 18, sc: 0.9, sod: 140, pot: 4.5,
    hemo: 15.0, pcv: 44, wc: 7500, rc: 5.0,
    htn: "no", dm: "no", cad: "no", appet: "good", pe: "no", ane: "no"
  }
};

function fillDemoAndSubmit(type) {
  const data = DEMO_DATA[type];
  currentMode = "doctor";
  console.log(`[CKD] Demo: filling ${type} data in doctor mode`);

  showSection("prediction");

  // Fill numeric and select fields
  for (const [key, val] of Object.entries(data)) {
    const f = FIELDS[key];
    if (!f) continue;
    if (f.type === "toggle") {
      const group = document.querySelector(`.toggle-group[data-field="${key}"]`);
      if (group) {
        group.querySelectorAll(".toggle-btn").forEach(b => {
          b.classList.toggle("active", b.dataset.value === String(val));
        });
      }
    } else {
      const el = document.getElementById(key);
      if (el) el.value = val;
    }
  }

  // Build submittedData
  submittedData = {};
  for (const key of Object.keys(FIELDS)) {
    submittedData[key] = String(data[key]);
  }

  showSection("loading");

  fetch("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
    .then(r => r.json())
    .then(result => {
      console.log("[CKD] Demo result:", result);
      if (result.success) {
        setTimeout(() => {
          try {
            renderResults(result);
          } catch (err) {
            console.error("[CKD] Error rendering demo results:", err);
            alert("Error displaying results: " + err.message);
            showSection("homepage");
          }
        }, 1200);
      } else {
        alert("Error: " + result.error);
        showSection("homepage");
      }
    })
    .catch(err => {
      console.error("[CKD] Demo fetch error:", err);
      alert("Connection error. Is the server running?");
      showSection("homepage");
    });
}

/* ─────────────────────────────────────────────
   10. RESULTS RENDERING
   ───────────────────────────────────────────── */
function renderResults(data) {
  showSection("results");

  const resultsEl = document.getElementById("results");
  const isPatient = currentMode === "patient";
  resultsEl.classList.toggle("patient-mode", isPatient);

  const isCKD = data.prediction === "CKD";
  const prob = data.probability || {};
  const ckdProb = prob["CKD"] || 0;
  const okProb = prob["Not CKD"] || 0;
  const ckdPct = Math.round(ckdProb * 100);

  console.log(`[CKD] Rendering results: prediction=${data.prediction}, CKD%=${ckdPct}, mode=${currentMode}`);

  // Main result card
  const hero = document.getElementById("result-hero");
  hero.className = "result-hero " + (isCKD ? "ckd" : "not-ckd");
  document.getElementById("result-label").textContent = isCKD ? "CKD Detected" : "No CKD Detected";
  document.getElementById("result-message").textContent = isCKD
    ? "The model indicates a high probability of Chronic Kidney Disease. Please consult a healthcare professional."
    : "The model indicates low risk of Chronic Kidney Disease. Maintain regular health checkups.";

  // Gauge
  setTimeout(() => {
    const angle = (ckdProb * 180) - 90;
    document.getElementById("gauge-needle").style.transform = `rotate(${angle}deg)`;
    document.getElementById("gauge-value").textContent = ckdPct + "%";
  }, 100);

  // Probability bars
  setTimeout(() => {
    document.getElementById("prob-ckd-bar").style.width = ckdPct + "%";
    document.getElementById("prob-ok-bar").style.width = Math.round(okProb * 100) + "%";
    document.getElementById("prob-ckd-val").textContent = ckdPct + "%";
    document.getElementById("prob-ok-val").textContent = Math.round(okProb * 100) + "%";
  }, 200);

  // Risk level label
  const riskEl = document.getElementById("risk-level");
  if (ckdPct <= 30) {
    riskEl.textContent = "🟢 Low Risk — Kidney function appears healthy";
    riskEl.className = "risk-level risk-low";
  } else if (ckdPct <= 60) {
    riskEl.textContent = "🟡 Moderate Risk — Some indicators need attention";
    riskEl.className = "risk-level risk-moderate";
  } else {
    riskEl.textContent = "🔴 High Risk — Strong indicators of CKD present";
    riskEl.className = "risk-level risk-high";
  }

  // Health Score (0-100) — higher = healthier
  const healthScore = Math.round((1 - ckdProb) * 100);
  renderHealthScore(healthScore);

  // Patient-friendly explanation (patient mode only)
  const explanationCard = document.getElementById("patient-explanation-card");
  if (isPatient && explanationCard) {
    explanationCard.style.display = "";
    renderPatientExplanation(ckdPct);
  } else if (explanationCard) {
    explanationCard.style.display = "none";
  }

  // Health parameter analysis (doctor mode)
  renderHealthGrid();

  // Feature importance chart (doctor mode)
  if (data.feature_importance) renderImportanceChart(data.feature_importance);

  window.scrollTo({ top: 0, behavior: "smooth" });
}

/* ─────────────────────────────────────────────
   10b. HEALTH SCORE RING
   Circular progress indicator (0–100)
   ───────────────────────────────────────────── */
function renderHealthScore(score) {
  const circumference = 2 * Math.PI * 52;
  const offset = circumference * (1 - score / 100);
  const ring = document.getElementById("score-ring-fill");
  const valEl = document.getElementById("score-value");
  const capEl = document.getElementById("score-caption");

  let color, caption;
  if (score >= 70) { color = "var(--success)"; caption = "Good kidney health indicators"; }
  else if (score >= 40) { color = "var(--warning)"; caption = "Some indicators need attention"; }
  else { color = "var(--danger)"; caption = "Multiple concerning indicators"; }

  setTimeout(() => {
    ring.style.stroke = color;
    ring.style.strokeDashoffset = offset;
    valEl.textContent = score;
    valEl.style.color = color;
    capEl.textContent = caption;
  }, 300);
}

/* ─────────────────────────────────────────────
   10c. PATIENT-FRIENDLY EXPLANATION
   ───────────────────────────────────────────── */
function renderPatientExplanation(ckdPct) {
  const content = document.getElementById("patient-explanation-content");
  if (!content) return;

  let html = "";
  if (ckdPct <= 20) {
    html = `
      <div class="explanation-block good">
        <h4>🟢 Your kidneys appear to be functioning well</h4>
        <p>Based on the information you provided, your kidney health indicators are within normal ranges.</p>
        <h4>💡 Recommendations:</h4>
        <ul>
          <li>Continue maintaining a healthy lifestyle</li>
          <li>Stay hydrated and eat a balanced diet</li>
          <li>Get regular health checkups annually</li>
          <li>Monitor your blood pressure regularly</li>
        </ul>
      </div>`;
  } else if (ckdPct <= 50) {
    html = `
      <div class="explanation-block moderate">
        <h4>🟡 Some indicators need attention</h4>
        <p>Your results show some values that may need medical attention. This doesn't necessarily mean you have kidney disease, but it's worth discussing with a doctor.</p>
        <h4>💡 Recommendations:</h4>
        <ul>
          <li>Schedule an appointment with your doctor</li>
          <li>Request a comprehensive kidney function test</li>
          <li>Monitor your blood pressure and blood sugar</li>
          <li>Reduce salt intake and stay well hydrated</li>
          <li>Avoid over-the-counter painkillers (NSAIDs)</li>
        </ul>
      </div>`;
  } else {
    html = `
      <div class="explanation-block high">
        <h4>🔴 Please consult a healthcare professional</h4>
        <p>Your results suggest elevated risk indicators that warrant professional medical evaluation. Early detection and treatment can significantly improve outcomes.</p>
        <h4>💡 Important Steps:</h4>
        <ul>
          <li><strong>See a doctor as soon as possible</strong></li>
          <li>Request blood tests: BUN, Creatinine, GFR</li>
          <li>Get a urine test (urinalysis)</li>
          <li>Discuss kidney function with a nephrologist if recommended</li>
          <li>Manage diabetes and blood pressure if applicable</li>
        </ul>
      </div>`;
  }

  html += `<p class="explanation-note">⚠️ This is an AI screening tool for educational purposes only. It is NOT a medical diagnosis. Always consult a qualified healthcare professional.</p>`;
  content.innerHTML = html;
}

/* ─────────────────────────────────────────────
   11. HEALTH PARAMETER ANALYSIS
   Shows submitted values vs healthy ranges
   ───────────────────────────────────────────── */
function renderHealthGrid() {
  const grid = document.getElementById("health-grid");
  grid.innerHTML = "";

  const numericFields = Object.entries(FIELDS).filter(([_, f]) => f.ranges && f.normalRange);

  numericFields.forEach(([key, f]) => {
    const val = parseFloat(submittedData[key]);
    if (isNaN(val)) return;

    let status = "Good", cls = "good", icon = "✓";
    for (const r of f.ranges) {
      if (val <= r.max) {
        if (r.cls === "success") { status = "Good"; cls = "good"; icon = "✓"; }
        else if (r.cls === "warning") { status = "Moderate"; cls = "moderate"; icon = "!"; }
        else { status = "Poor"; cls = "poor"; icon = "✗"; }
        break;
      }
    }

    const item = document.createElement("div");
    item.className = "health-item";
    item.innerHTML = `
      <div class="health-item-icon hi-${cls}">${icon}</div>
      <div class="health-item-info">
        <div class="health-item-name">${f.label}</div>
        <div class="health-item-val">Value: ${val} · Range: ${f.normalRange}</div>
      </div>
      <span class="health-item-status hs-${cls}">${status}</span>`;
    grid.appendChild(item);
  });
}

/* ─────────────────────────────────────────────
   12. FEATURE IMPORTANCE CHART
   Horizontal bars showing top influencing features
   ───────────────────────────────────────────── */
function renderImportanceChart(importances) {
  const chart = document.getElementById("importance-chart");
  chart.innerHTML = "";

  const sorted = Object.entries(importances)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  const maxVal = sorted[0][1];

  sorted.forEach(([key, val], i) => {
    const row = document.createElement("div");
    row.className = "imp-row";
    const pct = Math.round((val / maxVal) * 100);
    row.innerHTML = `
      <div class="imp-label">${FEATURE_NAMES[key] || key}</div>
      <div class="imp-track"><div class="imp-bar" id="imp-bar-${i}"></div></div>
      <div class="imp-value">${(val * 100).toFixed(1)}%</div>`;
    chart.appendChild(row);

    setTimeout(() => {
      const bar = document.getElementById(`imp-bar-${i}`);
      if (bar) bar.style.width = pct + "%";
    }, 300 + i * 80);
  });
}

/* ─────────────────────────────────────────────
   13. DEVELOPER EASTER EGG
   Access: Ctrl+Shift+K or triple-click footer version
   ───────────────────────────────────────────── */
function initEasterEgg() {
  const overlay = document.getElementById("dev-overlay");
  const closeBtn = document.getElementById("modal-close-btn");
  const version = document.getElementById("footer-version");

  function openModal() { overlay.style.display = "flex"; }
  function closeModal() { overlay.style.display = "none"; }

  document.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.shiftKey && e.key === "K") { e.preventDefault(); openModal(); }
  });

  let clicks = 0, clickTimer;
  version.addEventListener("click", () => {
    clicks++;
    clearTimeout(clickTimer);
    if (clicks >= 3) { clicks = 0; openModal(); }
    clickTimer = setTimeout(() => { clicks = 0; }, 600);
  });

  closeBtn.addEventListener("click", closeModal);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) closeModal(); });
}

/* ─────────────────────────────────────────────
   14. INITIALIZATION
   ───────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  console.log("[CKD] Initializing CKD Prediction System...");

  initTheme();
  buildProgress();
  buildForm();
  buildPatientForm();
  initNavigation();
  showStep(1);
  initEasterEgg();

  // Hero "Start Assessment" → scroll to mode selection
  document.getElementById("start-btn").addEventListener("click", () => {
    const modeSection = document.getElementById("mode-select");
    if (modeSection) {
      modeSection.scrollIntoView({ behavior: "smooth" });
    } else {
      // Fallback: go directly to doctor mode
      currentMode = "doctor";
      showSection("prediction");
    }
  });

  // Mode Selection — Patient Self-Check
  const startPatientBtn = document.getElementById("start-patient-btn");
  if (startPatientBtn) {
    startPatientBtn.addEventListener("click", () => {
      currentMode = "patient";
      console.log("[CKD] Mode selected: Patient Self-Check");
      showSection("patient-prediction");
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // Mode Selection — Doctor Clinical Mode
  const startDoctorBtn = document.getElementById("start-doctor-btn");
  if (startDoctorBtn) {
    startDoctorBtn.addEventListener("click", () => {
      currentMode = "doctor";
      console.log("[CKD] Mode selected: Doctor Clinical Mode");
      showSection("prediction");
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // Patient form: back button
  const patientBackBtn = document.getElementById("patient-back-btn");
  if (patientBackBtn) {
    patientBackBtn.addEventListener("click", () => goHome());
  }

  // Patient form: submit button
  const patientSubmitBtn = document.getElementById("patient-submit-btn");
  if (patientSubmitBtn) {
    patientSubmitBtn.addEventListener("click", () => submitPatientForm());
  }

  // Demo buttons
  document.getElementById("demo-ckd-btn").addEventListener("click", () => fillDemoAndSubmit("ckd"));
  document.getElementById("demo-healthy-btn").addEventListener("click", () => fillDemoAndSubmit("healthy"));

  // Predict again → go back to homepage
  document.getElementById("predict-again-btn").addEventListener("click", () => goHome());

  console.log("[CKD] Initialization complete.");
});
