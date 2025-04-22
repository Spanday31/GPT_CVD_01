
import streamlit as st
from datetime import datetime
import json
import pandas as pd
import matplotlib.pyplot as plt

from constants import LDL_THERAPIES
from calculations import (
    calculate_smart_risk, calculate_ldl_effect, validate_drug_classes,
    calculate_ldl_reduction, generate_recommendations
)
from pdf_generator import create_pdf_report
from utils import load_logo

st.set_page_config(page_title="PRIME CVD Risk Calculator", layout="wide", page_icon="❤️")

st.markdown("""<style>.main { background-color: #f8fafc; } .sidebar .sidebar-content { background: white; box-shadow: 1px 0 5px rgba(0,0,0,0.1); }</style>""", unsafe_allow_html=True)

col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("""<div class='card' style='background:linear-gradient(135deg,#3b82f6,#2563eb);color:white;'><h1>PRIME CVD Risk Calculator</h1></div>""", unsafe_allow_html=True)
with col2:
    load_logo()

st.sidebar.title("Patient Demographics")
age = st.sidebar.number_input("Age", min_value=30, max_value=100, value=65)
sex = st.sidebar.radio("Sex", ["Male", "Female"], horizontal=True)
diabetes = st.sidebar.checkbox("Diabetes")
smoker = st.sidebar.checkbox("Smoker")
vasc_count = sum([st.sidebar.checkbox(disease) for disease in ["CAD", "Stroke/TIA", "PAD"]])
total_chol = st.sidebar.number_input("Total Cholesterol", 2.0, 10.0, 5.0, 0.1)
hdl = st.sidebar.number_input("HDL-C", 0.5, 3.0, 1.0, 0.1)
ldl = st.sidebar.number_input("LDL-C", 0.5, 6.0, 3.5, 0.1)
sbp = st.sidebar.number_input("SBP", 90, 220, 140)
egfr = st.sidebar.slider("eGFR", 15, 120, 80)
crp = st.sidebar.number_input("CRP", 0.1, 20.0, 2.0, 0.1)

baseline_risk = calculate_smart_risk(age, sex, sbp, total_chol, hdl, smoker, diabetes, egfr, crp, vasc_count)
if baseline_risk:
    st.success(f"Baseline Risk: {baseline_risk}%")
