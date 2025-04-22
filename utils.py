
import streamlit as st
from PIL import Image

def load_logo(path: str = "logo.png", width: int = 100):
    try:
        logo = Image.open(path)
        st.image(logo, width=width)
    except Exception:
        st.warning(f"Logo not found at {path}")
