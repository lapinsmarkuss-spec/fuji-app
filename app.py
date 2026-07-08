import streamlit as st
from PIL import Image, ImageFilter, ImageDraw
import numpy as np
import math
import io

# --- 1. SASKARNES KONFIGURĀCIJA ---
st.set_page_config(page_title="Fuji Recipe PRO", layout="wide", page_icon="📷")

# Uzlabots CSS stilizējums
st.markdown("""
    <style>
    .main { background-color: #0a0c10; }
    .stApp { background: linear-gradient(180deg, #0e1117 0%, #161b22 100%); }
    .recipe-card { 
        background: #1c222d; padding: 25px; border-radius: 15px; 
        border: 1px solid #30363d; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    h1, h2, h3 { color: #e6edf3 !important; }
    .stMetricValue { font-size: 20px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. KAMERĀM SPECIFISKĀ DATUBĀZE ---
RECIPE_DB = {
    "X-M5 Reala Everyday": {
        "profile": {"C": 50, "S": 65, "W": 5, "T": -2},
        "film": "REALA ACE", "dr": "DR200", "shadow": "-1", "highlight": "-1", "color": "+1", 
        "wb_base": "Auto", "wb_r": "+2", "wb_b": "-2", "cameras": ["X-M5"], "safe_for_skin": True
    },
    "Portra 400 (X-M5 Native)": {
        "profile": {"C": 48, "S": 70, "W": 28, "T": -12},
        "film": "Classic Negative", "dr": "DR400", "shadow": "-1", "highlight": "-2", "color": "+1", 
        "wb_base": "Auto", "wb_r": "+3", "wb_b": "-5", "cameras": ["X-M5"], "safe_for_skin": True
    },
    "Portra 400 (X-T3 Adapted)": {
        "profile": {"C": 45, "S": 65, "W": 25, "T": -8},
        "film": "Classic Chrome", "dr": "DR400", "shadow": "-1", "highlight": "-1", "color": "+2", 
        "wb_base": "Auto", "wb_r": "+4", "wb_b": "-5", "cameras": ["X-M5", "X-T3"], "safe_for_skin": True
    },
    "Kodachrome 64 Classic": {
        "profile": {"C": 65, "S": 82, "W": 18, "T": -5},
        "film": "Classic Chrome", "dr": "DR200", "shadow": "+2", "highlight": "+1", "color": "+2", 
        "wb_base": "Daylight", "wb_r": "+2", "wb_b": "-4", "cameras": ["X-M5", "X-T3"], "safe_for_skin": True
    },
    "Nostalgic Cinema": {
        "profile": {"C": 55, "S": 78, "W": 35, "T": -15},
        "film": "Nostalgic Negative", "dr": "DR400", "shadow": "+1", "highlight": "-1", "color": "+2", 
        "wb_base": "Auto", "wb_r": "+4", "wb_b": "-6", "cameras": ["X-M5"], "safe_for_skin": True
    },
    "Eterna Cinematic": {
        "profile": {"C": 28, "S": 35, "W": -5, "T": 5},
        "film": "Eterna / Cinema", "dr": "DR400", "shadow": "+1", "highlight": "-1", "color": "-3", 
        "wb_base": "Auto", "wb_r": "-1", "wb_b": "+2", "cameras": ["X-M5", "X-T3"], "safe_for_skin": True
    },
    "Velvia Punch (Landscape)": {
        "profile": {"C": 72, "S": 125, "W": 12, "T": -2},
        "film": "Velvia / Vivid", "dr": "DR100", "shadow": "+2", "highlight": "+1", "color": "+3", 
        "wb_base": "Auto", "wb_r": "+1", "wb_b": "-2", "cameras": ["X-M5", "X-T3"], "safe_for_skin": False
    },
    "Ilford HP5 Plus (B&W)": {
        "profile": {"C": 78, "S": 0, "W": 0, "T": 0},
        "film": "Acros", "dr": "DR200", "shadow": "+3", "highlight": "+2", "color": "0", 
        "wb_base": "Auto", "wb_r": "0", "wb_b": "0", "cameras": ["X-M5", "X-T3"], "safe_for_skin": True
    }
}

# --- 3. SĀNJOSLAS KONTROLES ---
with st.sidebar:
    st.header("⚙️ Konfigurācija")
    selected_camera = st.radio("Aktīvā kamera:", ["Fujifilm X-M5", "Fujifilm X-T3"])
    st.divider()
    skin_protection_manual = st.toggle("🛡️ Ādas toņu aizsardzība", value=True)
    bias_preference = st.select_slider("Analīzes prioritāte:", options=["Sabalansēts", "Krāsu precizitāte", "Noskaņa"])
    
    st.divider()
    st.caption("Fuji Recipe PRO v2.1")

# --- 4. ANALĪZES DZINĒJS ---
@st.cache_data
def analyze_image_ultimate(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((400, 400))
    img_np = np.array(img).astype(np.float32)
    r, g, b = img_np[:,:,0], img_np[:,:,1], img_np[:,:,2]
    
    skin_mask = (r > 95) & (g > 40) & (b > 20) & (r > g) & (r > b)
    has_people = (np.sum(skin_mask) / skin_mask.size) > 0.05
    
    contrast = np.std(0.299*r + 0.587*g + 0.114*b)
    saturation = np.mean(np.max(img_np, axis=2) - np.min(img_np, axis=2))
    return {"C": contrast, "S": saturation, "has_people": has_people, "texture": np.mean(np.array(img.filter(ImageFilter.FIND_EDGES)))}

# --- 5. INTERFEISS ---
st.title("📷 Fuji Recipe PRO")
st.subheader("Pārveido savus kadrus par filmu mākslu.")

tab1, tab2 = st.tabs(["📁 Augšupielādēt", "📸 Live Kamera"])
img_source = None
with tab1: img_source = st.file_uploader("Pievieno foto:", type=["jpg", "png"])
with tab2: img_source = st.camera_input("Nofotografē ainu:")

if img_source:
    data = analyze_image_ultimate(img_source.getvalue())
    is_protected = skin_protection_manual and data["has_people"]
    
    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.image(img_source, use_column_width=True)
        if is_protected: st.warning("👤 Portreta režīms: Aizsardzība aktīva")
    
    # Loģika (šeit paliek tava esošā loģika...)
    best_match = "X-M5 Reala Everyday" # Vienkāršots piemērs
    rec = RECIPE_DB[best_match]
    
    with col2:
        st.markdown(f"<div class='recipe-box'><h3>🎯 Ieteiktā recepte: {best_match}</h3></div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Film Sim", rec["film"])
        c2.metric("Dynamic Range", rec["dr"])
        c3.metric("Color", rec["color"])
        
        st.success("✅ Iestatījumi gatavi eksportēšanai")
        if st.button("Ģenerēt kartīti"):
            st.balloons()
