import streamlit as st
import PIL.Image
import PIL.ImageDraw
import time
import json
from google import genai  # <-- ZMĚNĚNO: Nová oficiální knihovna
from inference_sdk import InferenceHTTPClient

# GLOBÁLNÍ PŘEKLADOVÝ SLOVNÍK (v3.0)
PREKLAD_DENTAL = {
    "Fillings": "Výplň", "Filling": "Výplň",
    "Cavity": "Kaz", "Caries": "Kaz",
    "Implant": "Implantát", "Crown": "Korunka",
    "Periapical lesion": "Absces / Váček",
    "Root Canal Treatment": "Endodontické ošetření",
    "Impacted tooth": "Retinovaný zub",
    "Missing teeth": "Chybějící zub",
    "Root Piece": "Zbytek kořene"
}




st.markdown("""
    <style>
    /* 1. Hlavní pozadí */
    .stApp {
        background-color: #9DA8A7; 
        color: #1A1D1D;
    }

    /* --- KOMPAKTNÍ REŽIM --- */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
        max-width: 95% !important; 
    }

    /* OMEZENÍ VÝŠKY RENTGENU */
    img {
        max-height: 400px !important; 
        object-fit: contain !important;
    }

    /* 2. SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #3E4747;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* 3. HLAVNÍ NADPIS */
    .main-header {
        font-size: 3rem; 
        font-weight: 200;
        letter-spacing: -2px;
        color: #FFFFFF;
        text-align: center;
        margin-top: 0;
        margin-bottom: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .sub-header {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 5px;
        color: #FFFFFF;
        text-align: center;
        opacity: 0.8;
        margin-bottom: 1.5rem; 
    }

    /* 4. NAHRÁVAČ SOUBORŮ */
    [data-testid="stFileUploader"] {
        background-color: #3E4747;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem !important; 
        margin-bottom: 1rem !important;
    }
    
    [data-testid="stFileUploaderDropzone"] {
        background-color: #3E4747 !important;
        border: 1px dashed rgba(255,255,255,0.3) !important;
    }

    [data-testid="stFileUploader"] label, 
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span {
        color: #FFFFFF !important;
    }

    /* 5. NADPISY SEKCI */
    h3 {
        color: #1A1D1D !important;
        font-weight: 400 !important;
        background-color: transparent !important;
        padding: 0 !important;
        margin-bottom: 0.2rem !important; 
    }

    /* 6. ČEKACÍ TEXT */
    .waiting-text {
        color: #FFFFFF !important;
        font-style: italic;
        font-size: 0.9rem;
    }

    /* 7. OBLÁ EUKALYPTOVÁ TLAČÍTKA */
    .stButton>button {
        border-radius: 25px !important; 
        border: 1px solid #3E4747 !important;
        padding: 8px 15px !important; 
        background-color: #3E4747 !important;
        color: white !important;
        transition: 0.3s;
        margin-bottom: 15px !important;
    }

    .stButton>button:disabled {
        background-color: #BDC3C7 !important; 
        border-color: #BDC3C7 !important;
        color: #7F8C8D !important;
        opacity: 0.6 !important;
        cursor: not-allowed !important;
    }

    /* 8. REPORT BOX */
    .report-box {
        background-color: #3E4747;
        color: white;
        padding: 12px 20px !important; 
        border-radius: 12px; 
        font-size: 0.85rem; 
        border-left: 5px solid #A3AFB0;
        margin-top: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* 9. AI FINAL REPORT BOX (Nový blok pro Chatbota) */
    .ai-box {
        background-color: #F8F9FA;
        color: #1A1D1D;
        padding: 20px !important; 
        border-radius: 12px; 
        font-size: 0.9rem; 
        border-top: 5px solid #3E4747;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    /* Vlastní stylové boxíky pro hlášky */
    .custom-info {
        background-color: #3E4747; /* Tmavá eukalyptová */
        color: #FFFFFF !important;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #A3AFB0;
        margin-bottom: 15px;
        font-size: 0.9rem;
    }

    .custom-success {
        background-color: #4A5D5D; /* Trochu jiný odstín šedé */
        color: #FFFFFF !important;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2ECC71; /* Zelený proužek pro detekci */
        margin-bottom: 15px;
        font-size: 0.9rem;
    }
    /* 10. Chat input */
    [data-testid="stChatInput"] {
        padding-bottom: 0 !important;
            
    }
    /* 1. Barva té části slideru, která se 'naplňuje' (TA ČERVENÁ) */
    div[data-baseweb="slider"] > div > div > div:first-child {
        background-color: rgba(61, 90, 66, 0.2) !important;
    }
    /* Cílíme na track, který je aktivní */
    div[data-baseweb="slider"] > div > div > div:nth-child(2) {
        background-color: #3D5A42 !important;
    }

    /* Pojistka pro moderní Streamlit verze */
    span[data-baseweb="slider"] > div > div > div:nth-child(2) {
        background-color: #3D5A42 !important;
    }

    /* A ještě jedna vrstva pro jistotu, kdyby se to jmenovalo jinak */
    div[data-testid="stSlider"] [data-baseweb="slider"] div {
        background-image: none !important; /* Zruší případné defaultní přechody */
    }

    /* 2. Barva samotného posuvného puntíku */
    div[data-baseweb="slider"] [role="slider"] {
        background-color: #3D5A42 !important;
        border: 2px solid #FFFFFF !important;
        box-shadow: none !important;
    }

    /* 3. Skrytí ošklivých čísel 1 a 100 na koncích (min/max popisky) */
    div[data-testid="stSliderTickBar"] {
        display: none !important;
    }
    
    /* 4. Barva čísla, které se ukazuje nad sliderem */
    div[data-testid="stWidgetLabel"] p {
        color: #1A1D1D !important;
    }
    
    /* 5. Barva hodnoty (toho malého čísla úplně nahoře u labelu) */
    .stSlider [data-testid="stMarkdownContainer"] p {
        color: #3D5A42 !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)


# --- 2. POSTRANNÍ LIŠTA ---
with st.sidebar:
    st.markdown("## ✧")
    st.write("---")
    st.markdown("### O projektu")
    st.write("Tato aplikace využívá umělou inteligenci YOLOv11 pro asistovanou diagnostiku v zubním lékařství.")
    st.info("💡 **Status:** Model se právě trénuje v cloudu. Nyní běží simulace rozhraní.")
    st.write("---")
    st.caption("👩‍💻 Vyvinula studentka IT (2. ročník)")
    st.caption("📍 Projekt 2026")

# --- 3. HLAVNÍ OBSAH ---
st.markdown("<h1 class='main-header'>Dental Vision</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>ASISTENT PŘI VYHODNOCOVÁNÍ RENTGENU</p>", unsafe_allow_html=True)

st.divider()

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### NAHRÁNÍ SNÍMKU")
    uploaded_file = st.file_uploader("Vyberte RTG snímek...", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    
    # --- 1. ČISTIČ PAMĚTI PŘI NOVÉM SOUBORU ---
    if uploaded_file:
        if "last_filename" not in st.session_state or st.session_state.last_filename != uploaded_file.name:
            st.session_state.last_filename = uploaded_file.name
            st.session_state.last_result = None
            st.session_state.current_threshold = 0.5
            st.session_state.selected_idx = None # Pro listování
            st.session_state.detected_items = []
            st.session_state.final_report = []
            st.session_state.clicked_buttons = set()
            st.session_state.ai_response = ""
            st.session_state.ai_consultant_active = False

    if uploaded_file:
        # Načtení čistého originálu pro dynamické kreslení
        clean_image = PIL.Image.open(uploaded_file).convert("RGB")
        
        # --- A. VOLÁNÍ AI (ROBOFLOW API PŘES BASE64) ---
        if st.session_state.last_result is None:
            with st.spinner("Hloubkové skenování (citlivost 1 %)..."):
                try:
                    import requests
                    import base64
                    import io

                    # 1. Převedeme obrázek na Base64 řetězec
                    buffered = io.BytesIO()
                    clean_image.save(buffered, format="JPEG")
                    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

                    # 2. Nastavení API - TADY JE TO 1 % (confidence=0.01)
                    ROBOFLOW_API_KEY = "HGRLUzxYU0GQQEfIP9UF"
                    model_id = "dental-xray-analysis-zfuqf-3m4fe/1"
                    
                    # URL s parametry
                    url = f"https://detect.roboflow.com/{model_id}?api_key={ROBOFLOW_API_KEY}&confidence=0.01"

                    # 3. POST požadavek (posíláme to jako prostý text)
                    response = requests.post(url, data=img_base64, headers={"Content-Type": "application/x-www-form-urlencoded"})
                    
                    if response.status_code == 200:
                        st.session_state.last_result = response.json()
                        st.toast("Detekce dokončena! (Zobrazeno vše od 1 %)")
                    else:
                        st.error(f"Roboflow Error {response.status_code}: {response.text}")

                except Exception as e:
                    st.error(f"Chyba při komunikaci: {e}")

        # --- B. DYNAMICKÉ KRESLENÍ (Reaguje na slider i listování) ---
        if st.session_state.last_result:
            thr = st.session_state.get("current_threshold", 0.5)
            selected_idx = st.session_state.get("selected_idx", None)
            
            # Pracovní kopie obrázku
            draw_img = clean_image.copy()
            draw = PIL.ImageDraw.Draw(draw_img)
            
            barvy_trid = {
                "Caries": "#FF4B4B", "Cavity": "#FF4B4B", "Periapical lesion": "#9B59B6", 
                "Filling": "#3498DB", "Fillings": "#3498DB", "Implant": "#2ECC71", 
                "Crown": "#F1C40F", "Root Canal Treatment": "#E67E22", 
                "Impacted tooth": "#E74C3C", "Missing teeth": "#95A5A6", "Root Piece": "#34495E"
            }

            # Filtrujeme predikce podle aktuálního slideru
            raw_preds = st.session_state.last_result['predictions']
            filtered_preds = [p for p in raw_preds if p['confidence'] >= thr]
            
            # Kreslíme obdélníčky
            for i, pred in enumerate(filtered_preds):
                cls_name = pred['class']
                conf_val = pred['confidence'] # Reálná jistota z modelu
                color = barvy_trid.get(cls_name, "#FFFFFF")
                
                x, y, w, h = pred['x'], pred['y'], pred['width'], pred['height']
                x0, y0, x1, y1 = x - w/2, y - h/2, x + w/2, y + h/2
                
                is_selected = (selected_idx is not None and i == selected_idx)
                line_w = 12 if is_selected else 4
                
                if is_selected:
                    draw.rectangle([x0-2, y0-2, x1+2, y1+2], outline="white", width=2)
                
                draw.rectangle([x0, y0, x1, y1], outline=color, width=line_w)
                
                # OPRAVA POPISKU: Název ze slovníku + procenta
                if selected_idx is None or is_selected:
                    nazev_cz = PREKLAD_DENTAL.get(cls_name, cls_name)
                    procenta = int(conf_val * 100)
                    label_text = f"{nazev_cz} {procenta}%"
                    draw.text((x0, y0 - 20), label_text, fill=color)

            # Aktualizace detekcí pro pravý sloupec (Gemini)
            st.session_state.detected_items = [p['class'] for p in filtered_preds]
            
            # Zobrazení obrázku
            st.image(draw_img, caption="Analyzovaný snímek s barvami", width='stretch')

        # --- C. EXPERTNÍ DIAGNOSTICKÝ PANEL ---
        with st.expander("🛠️ Expertní režim (Citlivost & Listování)"):
            st.markdown("""<div class='custom-info'>✨ <b>Expertní režim</b></div>""", unsafe_allow_html=True)
            
            if st.session_state.last_result:
                # 1. Slider (Okamžité překreslení)
                val = int(st.session_state.get("current_threshold", 0.5) * 100)
                new_thr = st.slider("Minimální jistota AI (%)", 1, 100, val) / 100
                
                if new_thr != st.session_state.current_threshold:
                    st.session_state.current_threshold = new_thr
                    st.session_state.selected_idx = None # Reset listování při pohybu sliderem
                    st.rerun()

                # 2. Listování
                filtered = [p for p in st.session_state.last_result['predictions'] if p['confidence'] >= new_thr]
                if filtered:
                    # --- TADY JE TA ZMĚNA POPISKŮ ---
                    options = ["--- Zobrazit vše ---"] + [
                        f"{PREKLAD_DENTAL.get(p['class'], p['class'])} ({int(p['confidence']*100)}%)" 
                        for p in filtered
                    ]
                    
                    # Zjistíme, co je aktuálně vybráno (index)
                    current_sel_idx = 0 if st.session_state.selected_idx is None else st.session_state.selected_idx + 1
                    
                    # Selectbox teď ukazuje přímo ty hezké texty z 'options'
                    choice_label = st.selectbox("Zaměřit na konkrétní nález:", options, index=current_sel_idx)
                    
                    # Přepočet zpátky na index nebo None
                    new_idx = None if choice_label == "--- Zobrazit vše ---" else options.index(choice_label) - 1
                    
                    if new_idx != st.session_state.selected_idx:
                        st.session_state.selected_idx = new_idx
                        st.rerun()

                    # --- TADY JE TO TLAČÍTKO PRO RYCHLÝ RESET ---
                    if st.session_state.selected_idx is not None:
                        if st.button("👁️ Zrušit zaměření (Zobrazit vše)", use_container_width=True):
                            st.session_state.selected_idx = None
                            st.rerun()
                        
                        # Detailní info o vybraném kousku
                        p = filtered[st.session_state.selected_idx]
                        st.markdown(f"""
                            <div style='background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; font-size: 0.8rem;'>
                                <b>Detail:</b> {PREKLAD_DENTAL.get(p['class'], p['class'])} | 
                                <b>Jistota:</b> {int(p['confidence']*100)}% | 
                                <b>Pozice:</b> x:{int(p['x'])}, y:{int(p['y'])}
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("Při této citlivosti nebylo nic nalezeno.")

            st.markdown("---")
            st.caption("🔍 **Legenda nálezů:**")
            
            # Tvoje krásná legenda
            legenda_html = """
            <div style="display: flex; flex-wrap: wrap; gap: 12px; font-size: 0.85rem; color: white; padding: 10px; background-color: rgba(255,255,255,0.05); border-radius: 10px;">
                <div style="display: flex; align-items: center;"><span style="height: 12px; width: 12px; background-color: #FF4B4B; border-radius: 50%; display: inline-block; margin-right: 6px;"></span> Kaz</div>
                <div style="display: flex; align-items: center;"><span style="height: 12px; width: 12px; background-color: #9B59B6; border-radius: 50%; display: inline-block; margin-right: 6px;"></span> Absces / Váček</div>
                <div style="display: flex; align-items: center;"><span style="height: 12px; width: 12px; background-color: #3498DB; border-radius: 50%; display: inline-block; margin-right: 6px;"></span> Výplň</div>
                <div style="display: flex; align-items: center;"><span style="height: 12px; width: 12px; background-color: #2ECC71; border-radius: 50%; display: inline-block; margin-right: 6px;"></span> Implantát</div>
                <div style="display: flex; align-items: center;"><span style="height: 12px; width: 12px; background-color: #F1C40F; border-radius: 50%; display: inline-block; margin-right: 6px;"></span> Korunka</div>
                <div style="display: flex; align-items: center;"><span style="height: 12px; width: 12px; background-color: #E67E22; border-radius: 50%; display: inline-block; margin-right: 6px;"></span> Endodoncie</div>
                <div style="display: flex; align-items: center;"><span style="height: 12px; width: 12px; background-color: #E74C3C; border-radius: 50%; display: inline-block; margin-right: 6px;"></span> Retinovaný zub</div>
                <div style="display: flex; align-items: center;"><span style="height: 12px; width: 12px; background-color: #95A5A6; border-radius: 50%; display: inline-block; margin-right: 6px;"></span> Chybějící zub</div>
                <div style="display: flex; align-items: center;"><span style="height: 12px; width: 12px; background-color: #34495E; border-radius: 50%; display: inline-block; margin-right: 6px;"></span> Zbytek kořene</div>
            </div>
            """
            st.markdown(legenda_html, unsafe_allow_html=True)
with col2:
    st.markdown("### ANALÝZA & KONZULTANT")
    
    if uploaded_file:
        st.divider()

        # --- 1. SHRNUTÍ NÁLEZU Z YOLOv11 ---
        # Používáme .get s prázdným listem jako default, abychom předešli chybám
        nalezy = st.session_state.get("detected_items", [])
        
        if nalezy:
            from collections import Counter
            pocty = Counter(nalezy)
            # Překlad a formátování detekovaných objektů
            casti = [f"<b>{pocet}x</b> {PREKLAD_DENTAL.get(nazev, nazev)}" for nazev, pocet in pocty.items()]
            text_shrnuti = " &nbsp;|&nbsp; ".join(casti)
            st.markdown(f"<div class='custom-success'>📊 <b>YOLOv11 Detekce:</b> {text_shrnuti}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='custom-success'>📊 <b>YOLOv11 Detekce:</b> Nebyl nalezen žádný zjevný objekt.</div>", unsafe_allow_html=True)

        st.write("") 

        # --- 2. INICIALIZACE SESSION STATE ---
        if "ai_consultant_active" not in st.session_state: st.session_state.ai_consultant_active = False
        if "final_report" not in st.session_state: st.session_state.final_report = []
        if "clicked_buttons" not in st.session_state: st.session_state.clicked_buttons = set()
        if "ai_response" not in st.session_state: st.session_state.ai_response = ""

        # --- 3. AKTIVACE ASISTENTA ---
        if not st.session_state.ai_consultant_active:
            if st.button("✨ Generovat návrhy zprávy (Gemini)", use_container_width=True):
                st.session_state.ai_consultant_active = True
                st.rerun()

        # --- 4. LOGIKA ASISTENTA (Běží jen když je aktivní) ---
        if st.session_state.ai_consultant_active:
            # Generování dynamických tlačítek (jen pokud ještě nejsou v paměti)
            if "dynamic_buttons" not in st.session_state:
                with st.spinner("AI analyzuje nález a připravuje možnosti..."):
                    try:
                        # 1. API Klíč a Klient (Nezapomeň tam dát svůj platný klíč!)
                        # Místo: GOOGLE_API_KEY = "tvuj_klic"
                        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
                        client = genai.Client(api_key=GOOGLE_API_KEY)
                        
                        # 2. Příprava dat pro prompt
                        nalezy = st.session_state.get("detected_items", [])
                        info_pro_ai = f"Nálezy: {', '.join(nalezy)}." if nalezy else "Snímek bez patologického nálezu."
                        
                        prompt_buttons = f"""
                        Jsi špičkový stomatolog. Z rentgenu máš tuto informaci: {info_pro_ai}
                        Navrhni 2 až 8 stručných popisků na tlačítka pro lékaře. 
                        Každý popisek musí začínat tematickým emoji (např. 🦷, 🩸, 🛡️, 💉).
                        Ke každému tlačítku vytvoř odpovídající, vysoce odbornou větu do dekurzu (např. 'Zjištěna kazivá léze v distální části...').
                        Pravidla: Překládej z angličtiny do češtiny. U kazu navrhni sanaci.
                        Vrať POUZE validní JSON pole. Vzor: [{{"id": "b1", "label": "🦷 Kaz", "text": "Nález kazu."}}]
                        """
                        
                        # 3. Volání API s nastavením bezpečnosti
                        response = client.models.generate_content(
                            model='gemini-2.5-flash', # Zkus případně 'models/gemini-2.0-flash'
                            contents=prompt_buttons,
                            config=genai.types.GenerateContentConfig(
                                response_mime_type="application/json",
                                safety_settings=[
                                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                                ]
                            )
                        )
                        
                        # 4. Zpracování a uložení odpovědi
                        st.session_state.dynamic_buttons = json.loads(response.text)
                        
                    except Exception as e:
                        # 5. Odchycení chyb (limity, špatný model, výpadek internetu...)
                        st.error(f"Detail chyby pro tvou analýzu: {e}")
                        st.warning("⚠️ Nouzový režim (Gemini API momentálně nedostupné).")
                        
                        # Fallback mechanismus pro záchranu situace
                        nalezy_fallback = st.session_state.get("detected_items", [])
                        if any(x in ["Caries", "Cavity"] for x in nalezy_fallback):
                            st.session_state.dynamic_buttons = [
                                {"id": "m1", "label": "🦷 Sanace kazu", "text": "Indikována sanace kazu."},
                                {"id": "m2", "label": "🔍 Detailní vyšetření", "text": "Doporučeno klinické došetření sondáží."}
                            ]
                        else:
                            st.session_state.dynamic_buttons = [
                                {"id": "m3", "label": "✅ Status quo", "text": "Nález v mezích fyziologické normy."},
                                {"id": "m4", "label": "🛡️ Profylaxe", "text": "Doporučena pravidelná hygiena a sledování."}
                            ]

            # Zobrazení tlačítek
            if "dynamic_buttons" in st.session_state:
                st.markdown("<div class='custom-info'>✨ <b>AI Asistent:</b> Vyberte body do zprávy:</div>", unsafe_allow_html=True)
                
                # Dynamické mřížky pro tlačítka
                cols = st.columns(2)
                for idx, btn_data in enumerate(st.session_state.dynamic_buttons):
                    btn_id = btn_data["id"]
                    is_clicked = btn_id in st.session_state.clicked_buttons
                    
                    if cols[idx % 2].button(btn_data["label"], key=btn_id, disabled=is_clicked, use_container_width=True):
                        st.session_state.clicked_buttons.add(btn_id)
                        st.session_state.final_report.append(btn_data["text"])
                        st.session_state.ai_response = "" # Resetujeme finální zprávu pro novou generaci
                        st.rerun()

            # --- 5. KONCEPT ZPRÁVY ---
            st.markdown("---")
            st.subheader("Koncept lékařské zprávy")
            
            if st.session_state.final_report:
                report_full_text = "\n".join([f"• {item}" for item in st.session_state.final_report])
                st.markdown(f"<div class='report-box'>{report_full_text}</div>", unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✨ FINALIZOVAT ZPRÁVU", use_container_width=True, type="primary"):
                        with st.spinner("Gemini AI stylizuje zápis..."):
                            try:
                                client = genai.Client(api_key=GOOGLE_API_KEY)
                                prompt_final = f"Zformátuj tyto body do profesionálního zápisu v dekurzu (RTG NÁLEZ, DIAGNÓZA, DOPORUČENÍ). Piš odborně, česky, bez oslovení: {report_full_text}"
                                response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt_final)
                                st.session_state.ai_response = response.text
                                st.rerun()
                            except:
                                st.error("Chyba při finalizaci.")
                
                with c2:
                    if st.button("Smazat vše", use_container_width=True):
                        st.session_state.final_report = []
                        st.session_state.clicked_buttons = set()
                        st.session_state.ai_response = ""
                        st.rerun()
                
                # Zobrazení finálního výstupu
                if st.session_state.ai_response:
                    st.success("Finální text dekurzu:")
                    st.text_area("Kopírovatelný text:", value=st.session_state.ai_response, height=200)
            else:
                st.info("Zatím jste nevybrali žádné body pro zápis.")

            # Chat pro ruční doplnění
            user_input = st.chat_input("Doplnit vlastní poznámku k nálezu...")
            if user_input:
                st.session_state.final_report.append(user_input)
                st.session_state.ai_response = ""
                st.rerun()
                
    else:
        # Reset stavů při odstranění obrázku
        keys_to_reset = ["dynamic_buttons", "final_report", "clicked_buttons", "ai_response", "ai_consultant_active"]
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        
        st.markdown('<p class="waiting-text">Pro spuštění analýzy nahrajte RTG snímek vlevo.</p>', unsafe_allow_html=True)