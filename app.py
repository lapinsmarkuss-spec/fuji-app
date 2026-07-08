import streamlit as st
from PIL import Image, ImageStat, ImageFilter
import numpy as np
import math

st.set_page_config(page_title="Fuji Recipe Pro", layout="wide")

st.title("Fujifilm Receptes Ģenerators PRO 📷")
st.write("Dinamiskā analīze + Grauda noteikšana + Color Chrome efekti")

# 1. Mūsu reālo recepšu datubāze (Profili apmācīti pēc kontrasta(C), piesātinājuma(S) un siltuma(W))
# Vērtības ir kalibrētas aptuvenai salīdzināšanai
RECIPE_DB = {
    "Kodachrome 64": {
        "profile": {"C": 65, "S": 85, "W": 20}, # Augsts kontrasts, vidējs piesātinājums, silts
        "film": "Classic Chrome", "dr": "DR200", 
        "shadow": "+2", "highlight": "+1", "color": "+2", 
        "wb_base": "Daylight", "wb_r": "+2", "wb_b": "-4"
    },
    "Portra 400": {
        "profile": {"C": 45, "S": 75, "W": 30}, # Vidējs kontrasts, silts/zaļgans
        "film": "Classic Negative", "dr": "DR400",
        "shadow": "-1", "highlight": "-2", "color": "+1", 
        "wb_base": "Auto", "wb_r": "+3", "wb_b": "-5"
    },
    "Cinematic Eterna": {
        "profile": {"C": 30, "S": 40, "W": -10}, # Zems kontrasts, blāvs, nedaudz vēss
        "film": "Eterna", "dr": "DR400",
        "shadow": "+1", "highlight": "-1", "color": "-3", 
        "wb_base": "Auto", "wb_r": "-1", "wb_b": "+2"
    },
    "Velvia Summer": {
        "profile": {"C": 70, "S": 130, "W": 10}, # Ļoti kontrastains, ļoti piesātināts
        "film": "Velvia", "dr": "DR100",
        "shadow": "+2", "highlight": "+1", "color": "+3", 
        "wb_base": "Auto", "wb_r": "+1", "wb_b": "-2"
    },
    "Ilford HP5 (B&W)": {
        "profile": {"C": 75, "S": 0, "W": 0}, # Kontrastains, bez krāsām
        "film": "Acros", "dr": "DR200",
        "shadow": "+3", "highlight": "+2", "color": "N/A", 
        "wb_base": "Auto", "wb_r": "0", "wb_b": "0"
    }
}

def analyze_image_pro(img):
    # 1. Centrēšana galvenajam objektam
    width, height = img.size
    crop_amount = 0.6
    left, top = (width * (1-crop_amount))/2, (height * (1-crop_amount))/2
    right, bottom = width - left, height - top
    cropped_img = img.crop((left, top, right, bottom))

    # 2. Bāzes analīze (Kontrasts un Piesātinājums)
    stat_gray = ImageStat.Stat(cropped_img.convert("L"))
    contrast = stat_gray.stddev[0]
    
    stat_hsv = ImageStat.Stat(cropped_img.convert("HSV"))
    saturation = stat_hsv.mean[1]
    
    stat_rgb = ImageStat.Stat(cropped_img)
    r, g, b = stat_rgb.mean
    warmth = r - b # Cik daudz sarkanā ir virs zilā

    # 3. Grauda (Texture/Noise) analīze izmantojot malu detektēšanu
    edges = cropped_img.convert("L").filter(ImageFilter.FIND_EDGES)
    stat_edges = ImageStat.Stat(edges)
    texture_level = stat_edges.mean[0] # Jo augstāks, jo vairāk sīku detaļu/trokšņa

    # 4. Color Chrome (Specifiska sarkano un zilo kanālu intensitāte)
    # Ja kanāls dominē pāri vidējam, attiecīgais efekts ir nepieciešams
    red_intensity = r - ((g + b) / 2)
    blue_intensity = b - ((r + g) / 2)

    return {
        "C": contrast, "S": saturation, "W": warmth, 
        "texture": texture_level, "red_int": red_intensity, "blue_int": blue_intensity
    }

uploaded_file = st.file_uploader("Augšupielādē atsauces foto...", type=["jpg", "jpeg", "png"])

if uploaded_file:
    col_img, col_res = st.columns([1, 2])
    
    image = Image.open(uploaded_file).convert("RGB")
    with col_img:
        st.image(image, caption="Analizētais attēls", use_column_width=True)

    with st.spinner("Skenēju pikseļus un aprēķinu formulu..."):
        data = analyze_image_pro(image)
        
        # Datubāzes salīdzināšana (Eiklīda attālums)
        best_match = None
        min_distance = float('inf')
        
        for name, recipe in RECIPE_DB.items():
            # Ja bilde ir gandrīz melnbalta, uzspiežam B&W recepti
            if data["S"] < 20 and name != "Ilford HP5 (B&W)": continue
            
            p = recipe["profile"]
            # Matemātiskais attālums 3D telpā
            dist = math.sqrt((data["C"] - p["C"])**2 + (data["S"] - p["S"])**2 + (data["W"] - p["W"])**2)
            
            if dist < min_distance:
                min_distance = dist
                best_match = name

        rec = RECIPE_DB[best_match]

        # Efektu dinamiskā piesaiste
        grain_effect = "Off"
        if data["texture"] > 35: grain_effect = "Strong, Large"
        elif data["texture"] > 20: grain_effect = "Weak, Small"

        cc_effect = "Off"
        if data["red_int"] > 40: cc_effect = "Strong"
        elif data["red_int"] > 20: cc_effect = "Weak"

        cc_blue = "Off"
        if data["blue_int"] > 40: cc_blue = "Strong"
        elif data["blue_int"] > 20: cc_blue = "Weak"

        # Fine-tuning: Nedaudz piekoriģējam receptes WB balstoties uz konkrēto bildi
        fine_tune_r = max(-9, min(9, int(float(rec["wb_r"]) + (data["W"] - rec["profile"]["W"]) / 15))) if rec["wb_r"] != "0" else 0

        # --- REZULTĀTU KARTĪTE ---
        with col_res:
            st.success(f"Bāzes recepte atrasta: **{best_match}**")
            
            st.subheader("Iestatījumu Karte (I.Q. Menu)")
            
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Attēla profils**")
                st.info(f"Film Simulation: **{rec['film']}**")
                st.write(f"Dynamic Range: **{rec['dr']}**")
                st.write(f"Highlight Tone: **{rec['highlight']}**")
                st.write(f"Shadow Tone: **{rec['shadow']}**")
                st.write(f"Color: **{rec['color']}**")
            
            with c2:
                st.write("**Efekti & Krāsas**")
                st.write(f"Grain Effect: **{grain_effect}**")
                st.write(f"Color Chrome Effect: **{cc_effect}**")
                st.write(f"Color Chrome FX Blue: **{cc_blue}**")
                st.info(f"White Balance: **{rec['wb_base']}**\n\nR: **{fine_tune_r}** / B: **{rec['wb_b']}**")
                
            st.caption("Matemātiskais profils pabeigts. Lūdzu ņemiet vērā apgaismojumu fotografēšanas brīdī.")