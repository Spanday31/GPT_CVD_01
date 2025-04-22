import streamlit as st
from datetime import datetime
import json
import pandas as pd
import matplotlib.pyplot as plt

# Corrected Imports for Streamlit Cloud (WITH DOTS)
from .calculations import (
    calculate_smart_risk, calculate_ldl_effect, validate_drug_classes,
    calculate_ldl_reduction, generate_recommendations
)
from .constants import LDL_THERAPIES
from .pdf_generator import create_pdf_report
from .utils import load_logo

# ======================
# Streamlit Page Config
# ======================
st.set_page_config(page_title="PRIME CVD Risk Calculator", layout="wide", page_icon="❤️")

# ======================
# HEADER
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
    load_logo()

# ======================
# SIDEBAR: PATIENT INPUTS
# ======================
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

# ======================
# VALIDATION
# ======================
if ldl < hdl:
    st.sidebar.error("LDL-C cannot be lower than HDL-C!")

# ======================
# RISK CALCULATION
# ======================
baseline_risk = calculate_smart_risk(age, sex, sbp, total_chol, hdl, smoker, diabetes, egfr, crp, vasc_count)
if baseline_risk:
    st.success(f"Baseline 10-Year Risk: {baseline_risk}%")
else:
    st.warning("Please complete all patient data to calculate risk.")

# ======================
# TREATMENT OPTIMISATION
# ======================
st.header("Optimise Lipid Therapy")

current_statin = st.selectbox("Current Statin", ["None"] + list(LDL_THERAPIES.keys()), index=0)
current_add_ons = st.multiselect("Current Add-ons", ["Ezetimibe", "PCSK9 inhibitor"])

discharge_statin = st.selectbox("Recommended Statin", ["None"] + list(LDL_THERAPIES.keys()), index=2)
discharge_add_ons = st.multiselect("Recommended Add-ons", ["Ezetimibe", "PCSK9 inhibitor", "Inclisiran"])

conflicts = validate_drug_classes([discharge_statin] + discharge_add_ons)
if conflicts:
    for conflict in conflicts:
        st.error(conflict)

if st.button("Calculate Treatment Impact", disabled=bool(conflicts)):
    projected_ldl, total_reduction = calculate_ldl_reduction(ldl, current_statin, discharge_statin, discharge_add_ons)
    final_risk = calculate_ldl_effect(baseline_risk, ldl, projected_ldl)
    recommendations = generate_recommendations(final_risk)

    st.metric("Projected LDL-C", f"{projected_ldl:.1f} mmol/L", delta=f"{total_reduction:.0f}% reduction")
    st.metric("Post-Treatment Risk", f"{final_risk:.1f}%", delta=f"{baseline_risk - final_risk:.1f}% absolute reduction")

    st.subheader("Clinical Recommendations")
    st.write(recommendations)

    # PDF REPORT GENERATION
    patient_name = st.text_input("Patient Name for Report", placeholder="Enter patient name")
    if st.button("Generate PDF Report") and patient_name:
        ldl_history = {
            'dates': [
                (datetime.now() - pd.Timedelta(days=90)).strftime('%Y-%m-%d'),
                (datetime.now() - pd.Timedelta(days=60)).strftime('%Y-%m-%d'),
                (datetime.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d')
            ],
            'values': [
                ldl * 1.2, ldl * 1.1, ldl, projected_ldl
            ]
        }

        pdf_bytes = create_pdf_report(
            patient_data={'name': patient_name, 'age': age, 'sex': sex},
            risk_data={
                'baseline_risk': baseline_risk,
                'final_risk': final_risk,
                'current_ldl': ldl,
                'ldl_target': 1.4,
                'recommendations': recommendations
            },
            ldl_history=ldl_history
        )

        st.download_button(
            label="⬇️ Download Report",
            data=pdf_bytes,
            file_name=f"{patient_name.replace(' ', '_')}_CVD_Report.pdf",
            mime="application/pdf"
        )

# ======================
# SAVE CASE AS JSON
# ======================
st.markdown("---")
st.header("Save Case")

case_data = {
    'age': age, 'sex': sex, 'diabetes': diabetes, 'smoker': smoker, 'ldl': ldl,
    'hdl': hdl, 'sbp': sbp, 'egfr': egfr, 'crp': crp, 'vasc_count': vasc_count
}
json_data = json.dumps(case_data, indent=2)
st.download_button("Download Case JSON", data=json_data, file_name=f"case_{datetime.now().date()}.json")
