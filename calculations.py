
import math
import streamlit as st

@st.cache_data
def calculate_smart_risk(age, sex, sbp, total_chol, hdl, smoker, diabetes, egfr, crp, vasc_count):
    sex_val = 1 if sex == "Male" else 0
    smoking_val = 1 if smoker else 0
    diabetes_val = 1 if diabetes else 0
    crp_log = math.log(crp + 1)
    lp = (0.064 * age + 0.34 * sex_val + 0.02 * sbp + 0.25 * total_chol - 0.25 * hdl + 0.44 * smoking_val + 0.51 * diabetes_val - 0.2 * (egfr / 10) + 0.25 * crp_log + 0.4 * vasc_count)
    risk10 = 1 - 0.900 ** math.exp(lp - 5.8)
    return max(1.0, min(99.0, round(risk10 * 100, 1)))
