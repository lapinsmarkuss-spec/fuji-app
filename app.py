import streamlit as st
from PIL import Image, ImageFilter, ImageDraw
import numpy as np
import math
import io

# --- 1. SASKARNES KONFIGURĀCIJA ---
st.set_page_config(page_title="Fuji Recipe PRO: X-M5 & X-T3 Edition", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .stMetric { background-color: #1e222b; padding: 15px; border-radius: 10px; border: 1px solid #2d3139; }
    .recipe-box { padding: 20px; border-radius: 10px; background-color: #161a22; border-left: 5px solid #00f0ff; }
    </style>
""", unsafe_allow_html=True)

st.title("Fujifilm Receptes Ģenerators PRO 📷 | X-M5 & X-T3")

# --- 2. DATUBĀZE ---
RECIPE_DB = {
    "X-M5 Reala Everyday": {
        "profile": {"C": 50, "S": 65, "W": 5, "T": -2},
        "film": "REALA ACE", "dr": "DR200", "shadow": "-1", "highlight": "-1", "color": "+1", 
        "wb_base": "Auto", "wb_r": "+2", "wb_b": "-2", "cameras": ["Fujifilm X-M5"], "safe_for_skin": True
    },
    "Portra 400 (X-M5 Native)": {
        "profile": {"C": 48, "S": 70, "W": 28, "T": -12},
        "film": "Classic Negative", "dr": "DR400", "shadow": "-1", "highlight": "-2", "color": "+1", 
        "wb_base": "Auto", "wb_r": "+3", "wb_b": "-5", "cameras": ["Fujifilm X-M5"], "safe_for_skin": True
    },
    "Portra 400 (X-T3 Adapted)": {
        "profile": {"C": 45, "S": 65, "W": 25, "T": -8},
        "film": "Classic Chrome", "dr": "DR400", "shadow": "-1", "highlight": "-1", "color": "+2", 
        "wb_base": "Auto", "wb_r": "+4", "wb_b": "-5", "cameras": ["Fujifilm X-M5", "Fujifilm X-T3"], "safe_for_skin": True
    },
    "Velvia Punch (Landscape)": {
        "profile": {"C": 72, "S": 125, "W": 12, "T": -2},
        "film": "Velvia / Vivid", "dr": "DR100", "shadow": "+2", "highlight": "+1", "color": "+3", 
        "wb_base": "Auto", "wb_r": "+1", "wb_b": "-2", "cameras": ["Fujifilm X-M5", "Fujifilm X-T3"], "safe_for_skin": False
    },
    "Ilford HP5 Plus (B&W)": {
        "profile": {"C": 78, "S": 0, "W": 0, "T": 0},
        "film": "Acros", "dr": "DR200", "shadow": "+3", "highlight": "+2", "color": "0", 
        "wb_base": "Auto", "wb_r": "0", "wb_b": "0", "cameras": ["Fujifilm X-M5", "Fujifilm X-T3"], "safe_for_skin": True
    }
}

# --- 3. SĀNJOSLAS KONTROLES ---
st.sidebar.header("📷 Iestatījumi")
selected_camera = st.sidebar.radio("Aktīvā kamera:", ["Fujifilm X-M5", "Fujifilm X-T3"])
use_skin_protection = st.sidebar.checkbox("Ieslēgt ādas toņu aizsardzību", value=True)

# --- 4. ANALĪZES DZINĒJS ---
@st.cache_data(show_spinner=False)
def analyze_image(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img.thumbnail((800, 800))
    arr = np.array(img).astype(np.float32)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    return {
        "C": np.std(gray),
        "S": np.mean(np.max(arr, axis=2) - np.min(arr, axis=2)),
        "W": np.mean(r) - np.mean(b),
        "T": np.mean(g) - ((np.mean(r) + np.mean(b)) / 2),
        "texture": np.mean(np.array(img.convert("L").filter(ImageFilter.FIND_EDGES)))
    }

# --- 5. KARTĪTES ĢENERATORS ---
def draw_recipe_card(name, camera, rec, dr, grain, r_wb, b_wb):
    card = Image.new("RGB", (450, 600), "#11141a")
    d = ImageDraw.Draw(card)
    d.text((35, 35), f"FUJIFILM {camera.split(' ')[1]} RECIPE", fill="#888e9b")
    d.text((35, 60), f"Profile: {name.upper()}", fill="#ffffff")
    y = 120
    settings = [("Film Sim", rec['film']), ("DR", dr), ("Color", rec['color']), ("WB Shift", f"R:{r_wb} B:{b_wb}")]
    for label, val in settings:
        d.text((35, y), f"{label}: {val}", fill="#ffffff")
        y += 40
    buf = io.BytesIO()
    card.save(buf, format="PNG")
    return buf.getvalue()

# --- 6. LOĢIKA ---
img_source = st.file_uploader("Augšupielādēt atsauces foto:", type=["jpg", "png"])

if img_source:
    data = analyze_image(img_source.getvalue())
    best_match = None
    min_dist = float('inf')
    
    for name, rec in RECIPE_DB.items():
        if selected_camera not in rec["cameras"]: continue
        
        # Manuālais sods, ja lietotājs ieslēdzis aizsardzību
        penalty = 150 if (use_skin_protection and not rec["safe_for_skin"]) else 0
        dist = abs(data["C"] - rec["profile"]["C"]) + abs(data["S"] - rec["profile"]["S"]) + penalty
        
        if dist < min_dist:
            min_dist, best_match = dist, name
            
    rec = RECIPE_DB[best_match]
    
    # Kalibrācija
    diff_w, diff_t = data["W"] - rec["profile"]["W"], data["T"] - rec["profile"]["T"]
    r_wb, b_wb = int(diff_w / 10), int(diff_t / 10)
    
    st.markdown(f"<div class='recipe-box'><h3>Ieteikums: {best_match}</h3></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.metric("Film Simulation", rec["film"])
    col2.metric("Dynamic Range", rec["dr"])
    
    card_bytes = draw_recipe_card(best_match, selected_camera, rec, rec["dr"], "Off", r_wb, b_wb)
    st.download_button("📥 Lejupielādēt Receptes Kartīti", data=card_bytes, file_name="recipe.png", mime="image/png")
