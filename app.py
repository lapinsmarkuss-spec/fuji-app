import streamlit as st
from PIL import Image, ImageStat, ImageFilter
import numpy as np
import math

# Konfigurācija
st.set_page_config(page_title="Fuji Recipe Pro", layout="wide")

st.title("Fujifilm Receptes Ģenerators PRO 📷")
st.write("Augšupielādē foto, lai saņemtu ieteicamos Fujifilm receptes iestatījumus.")

# 1. Mūsu reālo recepšu datubāze (kalibrēta)
RECIPE_DB = {
    "Kodachrome 64": {
        "profile": {"C": 65, "S": 85, "W": 20},
        "film": "Classic Chrome", "dr": "DR200",
        "shadow": "+2", "highlight": "+1", "color": "+2",
        "wb_base": "Daylight", "wb_r": "+2", "wb_b": "-4"
    },
    "Portra 400": {
        "profile": {"C": 45, "S": 75, "W": 30},
        "film": "Classic Negative", "dr": "DR400",
        "shadow": "-1", "highlight": "-2", "color": "+1",
        "wb_base": "Auto", "wb_r": "+3", "wb_b": "-5"
    },
    "Cinematic Eterna": {
        "profile": {"C": 30, "S": 40, "W": -10},
        "film": "Eterna", "dr": "DR400",
        "shadow": "+1", "highlight": "-1", "color": "-3",
        "wb_base": "Auto", "wb_r": "-1", "wb_b": "+2"
    },
    "Velvia Summer": {
        "profile": {"C": 70, "S": 130, "W": 10},
        "film": "Velvia", "dr": "DR100",
        "shadow": "+2", "highlight": "+1", "color": "+3",
        "wb_base": "Auto", "wb_r": "+1", "wb_b": "-2"
    },
    "Ilford HP5 (B&W)": {
        "profile": {"C": 75, "S": 0, "W": 0},
        "film": "Acros", "dr": "DR200",
        "shadow": "+3", "highlight": "+2", "color": "N/A",
        "wb_base": "Auto", "wb_r": "0", "wb_b": "0"
    }
}

# Analīzes funkcija
def analyze_image_pro(img):
    # Centrēšana galvenajam objektam
    width, height = img.size
    crop_amount = 0.6
    left, top = (width * (1-crop_amount))/2, (height * (1-crop_amount))/2
    right, bottom = width - left, height - top
    cropped_img = img.crop((left, top, right, bottom))

    # Bāzes analīze
    stat_gray = ImageStat.Stat(cropped_img.convert("L"))
    contrast = stat_gray.stddev[0]

    stat_hsv = ImageStat.Stat(cropped_img.convert("HSV"))
    saturation = stat_hsv.mean[1]

    stat_rgb = ImageStat.Stat(cropped_img)
    r, g, b = stat_rgb.mean
    warmth = r - b

    # Grauda analīze
    edges = cropped_img.convert("L").filter(ImageFilter.FIND_EDGES)
    stat_edges = ImageStat.Stat(edges)
    texture_level = stat_edges.mean[0]

    # Color Chrome
    red_intensity = r - ((g + b) / 2)
    blue_intensity = b - ((r + g) / 2)

    return {
        "C": contrast, "S": saturation, "W": warmth,
        "texture": texture_level, "red_int": red_intensity, "blue_int": blue_intensity
    }

# --- Failu augšupielāde ---
# Mēs norādām 'accept_multiple_files=False', kas datoros atver tikai failu pārlūku.
# Pievienojam aprakstu, kas lūdz izmantot galeriju.
uploaded_file = st.file_uploader("Augšupielādēt atsauces foto (lūdzu izvēlieties no galerijas, nevis kameru):", 
                                 type=["jpg", "jpeg", "png"])

if uploaded_file:
    col_img, col_res = st.columns([1, 2])

    # Rādām bildi
    try:
        image = Image.open(uploaded_file).convert("RGB")
        with col_img:
            st.image(image, caption="Analizētais attēls", use_column_width=True)

        with st.spinner("Analizēju pikseļus..."):
            data = analyze_image_pro(image)

            # Receptes piemeklēšana
            best_match = None
            min_distance = float('inf')

            for name, recipe in RECIPE_DB.items():
                if data["S"] < 20 and name != "Ilford HP5 (B&W)": continue
                p = recipe["profile"]
                dist = math.sqrt((data["C"] - p["C"])**2 + (data["S"] - p["S"])**2 + (data["W"] - p["W"])**2)

                if dist < min_distance:
                    min_distance = dist
                    best_match = name

            rec = RECIPE_DB[best_match]

            # Efektu noteikšana
            grain_effect = "Off"
            if data["texture"] > 35: grain_effect = "Strong, Large"
            elif data["texture"] > 20: grain_effect = "Weak, Small"

            cc_effect = "Off"
            if data["red_int"] > 40: cc_effect = "Strong"
            elif data["red_int"] > 20: cc_effect = "Weak"

            cc_blue = "Off"
            if data["blue_int"] > 40: cc_blue = "Strong"
            elif data["blue_int"] > 20: cc_blue = "Weak"

            fine_tune_r = max(-9, min(9, int(float(rec["wb_r"]) + (data["W"] - rec["profile"]["W"]) / 15))) if rec["wb_r"] != "0" else 0

            # Rezultāti
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
    except Exception as e:
        st.error(f"Kļūda, apstrādājot attēlu: {e}")

st.markdown("---")
st.caption("Fuji Recipe Pro - Dinamiskā analīze.")
