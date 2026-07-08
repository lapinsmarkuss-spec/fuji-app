import streamlit as st
from PIL import Image, ImageFilter, ImageDraw
import numpy as np
import math
import io

# --- 1. SASKARNES KONFIGURĀCIJA ---
st.set_page_config(page_title="Fuji Recipe PRO: X-M5 & X-T3", layout="wide")

st.markdown("""
    <style>
    .recipe-box { padding: 20px; border-radius: 10px; background-color: #161a22; border-left: 5px solid #00f0ff; }
    </style>
""", unsafe_allow_html=True)

st.title("Fujifilm Receptes Ģenerators PRO 📷")

# --- 2. DATUBĀZE ---
RECIPE_DB = {
    "X-M5 Reala Everyday": {"profile": {"C": 50, "S": 65, "W": 5, "T": -2}, "film": "REALA ACE", "dr": "DR200", "shadow": "-1", "highlight": "-1", "color": "+1", "wb_base": "Auto", "wb_r": "+2", "wb_b": "-2", "cameras": ["Fujifilm X-M5"], "safe_for_skin": True},
    "Portra 400 (Adapted)": {"profile": {"C": 45, "S": 65, "W": 25, "T": -8}, "film": "Classic Chrome", "dr": "DR400", "shadow": "-1", "highlight": "-1", "color": "+2", "wb_base": "Auto", "wb_r": "+4", "wb_b": "-5", "cameras": ["Fujifilm X-M5", "Fujifilm X-T3"], "safe_for_skin": True},
    "Velvia Punch (Landscape)": {"profile": {"C": 72, "S": 125, "W": 12, "T": -2}, "film": "Velvia / Vivid", "dr": "DR100", "shadow": "+2", "highlight": "+1", "color": "+3", "wb_base": "Auto", "wb_r": "+1", "wb_b": "-2", "cameras": ["Fujifilm X-M5", "Fujifilm X-T3"], "safe_for_skin": False},
    "Ilford HP5 Plus (B&W)": {"profile": {"C": 78, "S": 0, "W": 0, "T": 0}, "film": "Acros", "dr": "DR200", "shadow": "+3", "highlight": "+2", "color": "0", "wb_base": "Auto", "wb_r": "0", "wb_b": "0", "cameras": ["Fujifilm X-M5", "Fujifilm X-T3"], "safe_for_skin": True}
}

# --- 3. SĀNJOSLA ---
st.sidebar.header("Kontroles")
selected_camera = st.sidebar.radio("Kamera:", ["Fujifilm X-M5", "Fujifilm X-T3"])
# MANUĀLAIS SLĒDZIS
use_skin_protection = st.sidebar.checkbox("Ieslēgt ādas toņu aizsardzību (Safe for skin)", value=True)

# --- 4. ATTĒLA ANALĪZE ---
def analyze_image(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img.thumbnail((400, 400))
    arr = np.array(img).astype(np.float32)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    
    gray = 0.299*r + 0.587*g + 0.114*b
    return {
        "C": np.std(gray),
        "S": np.mean(np.max(arr, axis=2) - np.min(arr, axis=2)),
        "W": np.mean(r) - np.mean(b),
        "T": np.mean(g) - ((np.mean(r) + np.mean(b)) / 2)
    }

# --- 5. LOGIKA ---
img_file = st.file_uploader("Augšupielādē foto:", type=["jpg", "png"])
if img_file:
    data = analyze_image(img_file.getvalue())
    best_match = None
    min_dist = float('inf')
    
    for name, rec in RECIPE_DB.items():
        if selected_camera not in rec["cameras"]: continue
        
        # Filtra loģika: Ja ieslēgta aizsardzība un recepte nav safe, uzliek sodu
        penalty = 100 if (use_skin_protection and not rec["safe_for_skin"]) else 0
        dist = abs(data["C"] - rec["profile"]["C"]) + abs(data["S"] - rec["profile"]["S"]) + penalty
        
        if dist < min_dist:
            min_dist = dist
            best_match = name
            
    rec = RECIPE_DB[best_match]
    
    st.markdown(f"<div class='recipe-box'><h3>Ieteikums: {best_match}</h3></div>", unsafe_allow_html=True)
    st.info(f"Film Simulation: {rec['film']} | Dynamic Range: {rec['dr']}")
