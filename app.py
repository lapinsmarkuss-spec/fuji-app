import streamlit as st
from PIL import Image, ImageFilter, ImageDraw, ImageFont
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
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    </style>
""", unsafe_allow_html=True)

st.title("Fujifilm Receptes Ģenerators PRO 📷 | X-M5 & X-T3")
st.write("Ekskluzīvi pielāgots tavam arsenālam. AI perceptuālā analīze + precīza aparatūras emulācija.")

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
st.sidebar.header("📷 Izvēlies Tehniku")
selected_camera = st.sidebar.radio("Aktīvā kamera rokās:", ["Fujifilm X-M5", "Fujifilm X-T3"])

# MANUĀLAIS SLĒDZIS
skin_protection_manual = st.sidebar.checkbox("Aktivizēt ādas toņu aizsardzību", value=True)
st.sidebar.caption("Bloķē agresīvas filmas portretiem.")

bias_preference = st.sidebar.selectbox(
    "Analīzes prioritāte:",
    ["Sabalansēts (Standarta)", "Krāsu precizitāte (Piesātinājums)", "Noskaņa un Kontrasts"]
)

if bias_preference == "Krāsu precizitāte (Piesātinājums)":
    W_C, W_S, W_W, W_T = 1.0, 3.0, 1.5, 1.5
elif bias_preference == "Noskaņa un Kontrasts":
    W_C, W_S, W_W, W_T = 3.0, 1.0, 1.5, 1.0
else:
    W_C, W_S, W_W, W_T = 2.0, 1.5, 1.2, 1.2

# --- 4. MAX PRO DZINĒJS ---
@st.cache_data(show_spinner=False)
def analyze_image_ultimate(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img.thumbnail((800, 800))
    width, height = img.size
    
    crop_f = 0.7
    cropped = img.crop(((width*(1-crop_f))/2, (height*(1-crop_f))/2, width-(width*(1-crop_f))/2, height-(height*(1-crop_f))/2))
    img_np = np.array(cropped).astype(np.float32)
    r, g, b = img_np[:,:,0], img_np[:,:,1], img_np[:,:,2]

    skin_mask = (r > 95) & (g > 40) & (b > 20) & ((np.maximum(r, np.maximum(g, b)) - np.minimum(r, np.minimum(g, b))) > 15) & (np.abs(r - g) > 15) & (r > g) & (r > b)
    skin_ratio = np.sum(skin_mask) / skin_mask.size
    has_people = skin_ratio > 0.08 

    perceptual_gray = 0.299 * r + 0.587 * g + 0.114 * b
    contrast = np.std(perceptual_gray)
    overexposed_ratio = np.sum(perceptual_gray > 245) / perceptual_gray.size

    max_rgb, min_rgb = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    sat_mask = max_rgb != 0
    sat_array = np.zeros_like(max_rgb)
    sat_array[sat_mask] = (max_rgb[sat_mask] - min_rgb[sat_mask]) / max_rgb[sat_mask]
    saturation = np.mean(sat_array) * 255

    warmth = np.mean(r) - np.mean(b)
    tint = np.mean(g) - ((np.mean(r) + np.mean(b)) / 2)
    edges = cropped.convert("L").filter(ImageFilter.FIND_EDGES)
    texture_level = np.mean(np.array(edges))
    red_int = np.mean(r) - ((np.mean(g) + np.mean(b)) / 2)
    blue_int = np.mean(b) - ((np.mean(r) + np.mean(g)) / 2)

    return {
        "C": contrast, "S": saturation, "W": warmth, "T": tint,
        "overexposed": overexposed_ratio, "texture": texture_level,
        "red_int": red_int, "blue_int": blue_int, "has_people": has_people
    }

# --- 5. DINAMISKAIS KARTĪTES ĢENERATORS ---
def draw_recipe_card(name, camera, rec_data, grain, cc, ccb, clarity, dr, r_wb, b_wb):
    card = Image.new("RGB", (450, 720), "#11141a")
    d = ImageDraw.Draw(card)
    d.rectangle([(15, 15), (435, 705)], outline="#2d3139", width=2)
    d.line([(30, 85), (420, 85)], fill="#00f0ff", width=3)
    d.text((35, 35), f"FUJIFILM {camera.split(' ')[1]} RECIPE", fill="#888e9b")
    d.text((35, 55), f"Profile: {name.upper()}", fill="#ffffff")
    
    y = 110
    settings = [
        ("Film Simulation", rec_data['film']), ("Dynamic Range", dr),
        ("Highlight Tone", rec_data['highlight']), ("Shadow Tone", rec_data['shadow']),
        ("Color", rec_data['color']), ("Sharpness", "0"), ("Noise Reduction", "-4")
    ]
    
    if camera == "Fujifilm X-M5":
        settings.extend([("Clarity", clarity), ("Grain Effect", grain), ("Color Chrome Effect", cc), ("Color Chrome FX Blue", ccb)])
    else:
        settings.extend([("Grain Effect", grain), ("Color Chrome Effect", cc)])
        
    settings.extend([("White Balance", rec_data['wb_base']), ("WB Shift", f"R: {r_wb} / B: {b_wb}")])
    
    for label, val in settings:
        d.text((35, y), label, fill="#a3a9b6")
        d.text((260, y), str(val), fill="#ffffff")
        d.line([(35, y+22), (415, y+22)], fill="#1c202a", width=1)
        y += 38
        
    d.text((35, 680), "Generated via Fuji Recipe PRO", fill="#4f5564")
    
    buf = io.BytesIO()
    card.save(buf, format="PNG")
    return buf.getvalue()

# --- 6. LIETOTĀJA IEVADE ---
tab1, tab2 = st.tabs(["📁 Augšupielādēt failu", "📸 Skatīties Caur Kameru (Live)"])
img_source = None
with tab1:
    uploaded_file = st.file_uploader("Pievieno atsauces fotoattēlu:", type=["jpg", "jpeg", "png"])
    if uploaded_file: img_source = uploaded_file.getvalue()
with tab2:
    camera_file = st.camera_input("Nofotografē ainu tagad:")
    if camera_file: img_source = camera_file.getvalue()

# --- 7. APSTRĀDE UN SADERĪBAS LOĢIKA ---
if img_source:
    col_img, col_res = st.columns([1, 1.2])
    
    with col_img:
        st.image(img_source, caption=f"Avots analizēts priekš: {selected_camera}", use_column_width=True)
        with st.spinner("Skripts krakšķina datus..."):
            data = analyze_image_ultimate(img_source)
        
        # Loģika ar manuālo slēdzi
        is_protected = skin_protection_manual and data["has_people"]
        
        if is_protected:
            st.warning("👤 Ādas toņu aizsardzība AKTĪVA. Bloķēju agresīvas filmas.")
        else:
            st.info("🔓 Aizsardzība izslēgta - tiek piemēroti visi stila efekti.")

    min_distance = float('inf')
    best_match = None

    for name, recipe in RECIPE_DB.items():
        if selected_camera not in recipe["cameras"]: continue
        if data["S"] < 18 and name != "Ilford HP5 Plus (B&W)": continue
        
        penalty = 150 if is_protected and not recipe["safe_for_skin"] else 0
        p = recipe["profile"]
        dist = math.sqrt(
            W_C * (data["C"] - p["C"])**2 + W_S * (data["S"] - p["S"])**2 + 
            W_W * (data["W"] - p["W"])**2 + W_T * (data["T"] - p["T"])**2
        ) + penalty
        
        if dist < min_distance:
            min_distance = dist
            best_match = name

    if not best_match: 
        best_match = "Ilford HP5 Plus (B&W)" if data["S"] < 18 else ("X-M5 Reala Everyday" if selected_camera == "Fujifilm X-M5" else "Portra 400 (X-T3 Adapted)")
    rec = RECIPE_DB[best_match]

    # Aparatūras specifiskā kalibrācija
    if selected_camera == "Fujifilm X-M5":
        grain_effect = "Strong, Large" if data["texture"] > 38 else ("Weak, Small" if data["texture"] > 22 else "Off")
        clarity_effect = "-2" if data["texture"] < 12 else ("+2" if data["texture"] > 42 else "0")
        cc_blue = "Strong" if data["blue_int"] > 35 else ("Weak" if data["blue_int"] > 15 else "Off")
    else: 
        grain_effect = "Strong" if data["texture"] > 38 else ("Weak" if data["texture"] > 22 else "Off")
        clarity_effect = "N/A"
        cc_blue = "N/A"

    cc_effect = "Strong" if data["red_int"] > 35 else ("Weak" if data["red_int"] > 15 else "Off")
    dynamic_dr = "DR400" if data["overexposed"] > 0.06 else ("DR200" if data["overexposed"] > 0.02 else rec["dr"])

    diff_w, diff_t = data["W"] - rec["profile"]["W"], data["T"] - rec["profile"]["T"]
    base_r, base_b = int(rec["wb_r"]) if rec["wb_r"] not in ["0", "N/A"] else 0, int(rec["wb_r"]) if rec["wb_b"] not in ["0", "N/A"] else 0
    fine_tune_r = max(-9, min(9, base_r + int(diff_w / 10)))
    fine_tune_b = max(-9, min(9, base_b - int(diff_t / 10)))
    if rec["film"] == "Acros": fine_tune_r, fine_tune_b = 0, 0

    # --- 8. FINĀLA IZVADE ---
    with col_res:
        st.markdown(f"""
        <div class='recipe-box'>
            <h3 style='margin:0; color:#ffffff;'>Iestatījumi priekš: <b>{selected_camera}</b></h3>
            <p style='margin:5px 0 0 0; color:#00f0ff;'>Rīks izvēlējās: {best_match}</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")

        res_c1, res_c2 = st.columns(2)
        with res_c1:
            st.markdown("### 🛠️ I.Q. Izvēlne")
            st.info(f"**Film Simulation:** {rec['film']}")
            st.metric(label="Dynamic Range", value=dynamic_dr)
            st.text(f"Highlight Tone: {rec['highlight']}")
            st.text(f"Shadow Tone: {rec['shadow']}")
            st.text(f"Color: {rec['color']}")
            if selected_camera == "Fujifilm X-M5": st.text(f"Clarity: {clarity_effect}")

        with res_c2:
            st.markdown("### 🎨 Efekti")
            st.text(f"Grain Effect: {grain_effect}")
            st.text(f"Color Chrome: {cc_effect}")
            if selected_camera == "Fujifilm X-M5": st.text(f"CC FX Blue: {cc_blue}")
            st.markdown("---")
            st.success(f"**White Balance:** {rec['wb_base']}\n\n**Shift:** R: `{fine_tune_r}` / B: `{fine_tune_b}`")

        st.markdown("---")
        card_bytes = draw_recipe_card(best_match, selected_camera, rec, grain_effect, cc_effect, cc_blue, clarity_effect, dynamic_dr, fine_tune_r, fine_tune_b)
        st.download_button(label="📥 Lejupielādēt Receptes Kartīti", data=card_bytes, file_name=f"fuji_{selected_camera.split()[1]}_{best_match[:5]}.png", mime="image/png")
