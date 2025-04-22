import streamlit as st
from datetime import datetime
import math
import json
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from PIL import Image
from io import BytesIO

# ======================
# DATA CONSTANTS
# ======================

LDL_THERAPIES = {
    "Atorvastatin 20 mg": {"reduction": 40},
    "Atorvastatin 80 mg": {"reduction": 50},
    "Rosuvastatin 10 mg": {"reduction": 45},
    "Rosuvastatin 20 mg": {"reduction": 55}
}

# ======================
# CALCULATION FUNCTIONS
# ======================

@st.cache_data
def calculate_smart_risk(age, sex, sbp, total_chol, hdl, smoker, diabetes, egfr, crp, vasc_count):
    try:
        sex_val = 1 if sex == "Male" else 0
        smoking_val = 1 if smoker else 0
        diabetes_val = 1 if diabetes else 0
        crp_log = math.log(crp + 1)
        lp = (0.064 * age + 0.34 * sex_val + 0.02 * sbp + 0.25 * total_chol - 0.25 * hdl +
              0.44 * smoking_val + 0.51 * diabetes_val - 0.2 * (egfr / 10) + 0.25 * crp_log + 0.4 * vasc_count)
        risk10 = 1 - 0.900 ** math.exp(lp - 5.8)
        return max(1.0, min(99.0, round(risk10 * 100, 1)))
    except Exception as e:
        st.error(f"Error calculating risk: {str(e)}")
        return None

def calculate_ldl_effect(baseline_risk, baseline_ldl, final_ldl):
    try:
        ldl_reduction = baseline_ldl - final_ldl
        rrr = min(22 * ldl_reduction, 60)
        return baseline_risk * (1 - rrr / 100)
    except Exception as e:
        st.error(f"Error calculating LDL effect: {str(e)}")
        return baseline_risk

def validate_drug_classes(selected_therapies):
    drug_classes = {'statins': ['atorvastatin', 'rosuvastatin'], 'pcsk9': ['pcsk9', 'evolocumab'], 'ezetimibe': ['ezetimibe'], 'inclisiran': ['inclisiran']}
    conflicts = []
    for class_name, drugs in drug_classes.items():
        class_drugs = [d for d in selected_therapies if any(drug in d.lower() for drug in drugs)]
        if len(class_drugs) > 1:
            conflicts.append(f"Multiple {class_name}: {', '.join(class_drugs)}")
    return conflicts

def calculate_ldl_reduction(current_ldl, pre_statin, discharge_statin, discharge_add_ons):
    statin_reduction = LDL_THERAPIES.get(discharge_statin, {}).get("reduction", 0)
    if pre_statin != "None":
        statin_reduction *= 0.5
    total_reduction = statin_reduction
    if "Ezetimibe" in discharge_add_ons:
        total_reduction += 20
    if "PCSK9 inhibitor" in discharge_add_ons:
        total_reduction += 60
    if "Inclisiran" in discharge_add_ons:
        total_reduction += 50
    projected_ldl = current_ldl * (1 - total_reduction / 100)
    return projected_ldl, total_reduction

def generate_recommendations(final_risk):
    if final_risk >= 30:
        return "🔴 Very High Risk: High-intensity statin, PCSK9 inhibitor, SBP <130 mmHg."
    elif final_risk >= 20:
        return "🟠 High Risk: Moderate-intensity statin, SBP <130 mmHg."
    else:
        return "🟢 Moderate Risk: Lifestyle adherence, annual reassessment."

# ======================
# PDF REPORT GENERATION
# ======================

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'PRIME CVD Risk Assessment Report', 0, 1, 'C')

def create_pdf_report(patient_data, risk_data, ldl_history):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'PRIME CVD Risk Assessment', 0, 1, 'C')
    return pdf.output(dest='S').encode('latin1')

# ======================
# STREAMLIT APP CONFIG
# ======================

st.set_page_config(page_title="PRIME CVD Risk Calculator", layout="wide", page_icon="❤️")

# ======================
# UI
# ======================

col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#3b82f6,#2563eb);padding:1rem;border-radius:10px;'>
        <h1 style='color:white;margin:0;'>PRIME CVD Risk Calculator</h1>
        <p style='color:#e0f2fe;margin:0;'>Secondary Prevention After Myocardial Infarction</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    try:
        logo = Image.open("logo.png")
        st.image(logo, width=100)
    except:
        st.warning("Logo not found")

st.sidebar.title("Patient Demographics")
age = st.sidebar.number_input("Age (years)", min_value=30, max_value=100, value=65)
sex = st.sidebar.radio("Sex", ["Male", "Female"], horizontal=True)
diabetes = st.sidebar.checkbox("Diabetes mellitus")
smoker = st.sidebar.checkbox("Current smoker")

st.sidebar.title("Vascular Disease")
cad = st.sidebar.checkbox("Coronary artery disease (CAD)")
stroke = st.sidebar.checkbox("Cerebrovascular disease (Stroke/TIA)")
pad = st.sidebar.checkbox("Peripheral artery disease (PAD)")
vasc_count = sum([cad, stroke, pad])

st.sidebar.title("Biomarkers")
total_chol = st.sidebar.number_input("Total Cholesterol (mmol/L)", 2.0, 10.0, 5.0, 0.1)
hdl = st.sidebar.number_input("HDL-C (mmol/L)", 0.5, 3.0, 1.0, 0.1)
ldl = st.sidebar.number_input("LDL-C (mmol/L)", 0.5, 6.0, 3.5, 0.1)
sbp = st.sidebar.number_input("SBP (mmHg)", 90, 220, 140)
egfr = st.sidebar.slider("eGFR (mL/min/1.73m²)", 15, 120, 80)
crp = st.sidebar.number_input("hs-CRP (mg/L)", 0.1, 20.0, 2.0, 0.1)

if ldl < hdl:
    st.sidebar.error("LDL-C cannot be lower than HDL-C!")

baseline_risk = calculate_smart_risk(age, sex, sbp, total_chol, hdl, smoker, diabetes, egfr, crp, vasc_count)
if baseline_risk:
    st.success(f"Baseline 10-Year Risk: {baseline_risk}%")
else:
    st.warning("Please complete all patient data to calculate risk.")
