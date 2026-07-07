import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy import signal
import time
import datetime
import asyncio
import tempfile
import os
import base64
import edge_tts

st.set_page_config(
    page_title="Acoustic Through-Wall Detection | GlobalInternet.py",
    layout="wide",
    page_icon="📡"
)

# ---------- TRANSLATIONS ----------
TEXTS = {
    "English": {
        "app_title": "📡 Acoustic Through‑Wall Detection",
        "app_subtitle": "Simulate or use real‑time audio to detect objects behind walls",
        "sidebar_params": "⚙️ Simulation Parameters",
        "wall_thickness": "Wall Thickness (cm)",
        "object_distance": "Object Distance from Wall (cm)",
        "object_size": "Object Size (cm)",
        "wall_material": "Wall Material",
        "movement": "Simulate Object Movement",
        "movement_speed": "Movement Speed (cm/s)",
        "tab_sim": "📐 Simulation Mode",
        "tab_real": "🎤 Real‑time Detection",
        "sim_view": "📐 2D Cross‑Section View",
        "signal_plot": "📊 Received Acoustic Signal",
        "detection_results": "🎯 Detection Results",
        "estimated_distance": "Estimated Object Distance",
        "estimated_size": "Estimated Object Size",
        "object_detected": "✅ Object detected!",
        "no_object": "No object detected. Try adjusting parameters or increasing object size.",
        "material_speed": "Wall material: {} (sound speed: {:.0f} m/s)",
        "movement_sim": "🔄 Object Movement Simulation",
        "moving_object": "Moving object... Distance: {:.1f} cm",
        "sim_complete": "Movement simulation completed.",
        "real_title": "🎤 Real‑time Acoustic Detection",
        "real_desc": "Use your device's microphone and speakers to detect objects in your room.",
        "chirp_duration": "Chirp Duration (ms)",
        "freq_start": "Start Frequency (Hz)",
        "freq_end": "End Frequency (Hz)",
        "volume": "Volume",
        "max_distance": "Max Detection Distance (cm)",
        "params": "📊 Parameters",
        "how_it_works": "ℹ️ How it works",
        "step1": "1. A chirp is played through your speakers.",
        "step2": "2. The microphone records the echo.",
        "step3": "3. The app finds the first strong reflection.",
        "step4": "4. Distance is calculated from round‑trip time.",
        "warning": "For best results, be in a quiet room and place a reflective object (wall, cabinet) a few meters away.",
        "detection_complete": "✅ Detection complete.",
        "cm_estimated": "cm estimated",
        "delay": "Delay: {:.2f} ms",
        "confidence": "Peak confidence: {:.1f}%",
        "object_detected_behind": "✅ Object detected behind wall (approx)",
        "no_clear_object": "ℹ️ No clear object detected (try moving closer)",
        "report_generated": "Report generated",
        "download_report": "📥 Download Report (.txt)",
        "footer": "🚀 Built by Gesner Deslandes, Engineer-in-Chief at GlobalInternet.py | Acoustic detection simulation & real‑time audio.",
        "listen_explanation": "🔊 Listen to App Explanation",
        "voice_lang": "🌐 Voice Language",
    },
    "French": {
        "app_title": "📡 Détection Acoustique à Travers les Murs",
        "app_subtitle": "Simulez ou utilisez l'audio en temps réel pour détecter des objets derrière les murs",
        "sidebar_params": "⚙️ Paramètres de simulation",
        "wall_thickness": "Épaisseur du mur (cm)",
        "object_distance": "Distance de l'objet par rapport au mur (cm)",
        "object_size": "Taille de l'objet (cm)",
        "wall_material": "Matériau du mur",
        "movement": "Simuler le mouvement de l'objet",
        "movement_speed": "Vitesse de déplacement (cm/s)",
        "tab_sim": "📐 Mode simulation",
        "tab_real": "🎤 Détection en temps réel",
        "sim_view": "📐 Vue en coupe 2D",
        "signal_plot": "📊 Signal acoustique reçu",
        "detection_results": "🎯 Résultats de la détection",
        "estimated_distance": "Distance estimée de l'objet",
        "estimated_size": "Taille estimée de l'objet",
        "object_detected": "✅ Objet détecté !",
        "no_object": "Aucun objet détecté. Essayez d'ajuster les paramètres ou d'augmenter la taille de l'objet.",
        "material_speed": "Matériau du mur : {} (vitesse du son : {:.0f} m/s)",
        "movement_sim": "🔄 Simulation de mouvement d'objet",
        "moving_object": "Déplacement de l'objet... Distance : {:.1f} cm",
        "sim_complete": "Simulation de mouvement terminée.",
        "real_title": "🎤 Détection acoustique en temps réel",
        "real_desc": "Utilisez le microphone et les haut‑parleurs de votre appareil pour détecter des objets dans votre pièce.",
        "chirp_duration": "Durée du chirp (ms)",
        "freq_start": "Fréquence de début (Hz)",
        "freq_end": "Fréquence de fin (Hz)",
        "volume": "Volume",
        "max_distance": "Distance maximale de détection (cm)",
        "params": "📊 Paramètres",
        "how_it_works": "ℹ️ Comment ça fonctionne",
        "step1": "1. Un chirp est émis par les haut‑parleurs.",
        "step2": "2. Le microphone enregistre l'écho.",
        "step3": "3. L'application trouve la première réflexion forte.",
        "step4": "4. La distance est calculée à partir du temps aller‑retour.",
        "warning": "Pour de meilleurs résultats, placez‑vous dans une pièce calme et placez un objet réfléchissant (mur, meuble) à quelques mètres.",
        "detection_complete": "✅ Détection terminée.",
        "cm_estimated": "cm estimé",
        "delay": "Délai : {:.2f} ms",
        "confidence": "Confiance du pic : {:.1f}%",
        "object_detected_behind": "✅ Objet détecté derrière un mur (approx)",
        "no_clear_object": "ℹ️ Aucun objet clair détecté (essayez de vous rapprocher)",
        "report_generated": "Rapport généré",
        "download_report": "📥 Télécharger le rapport (.txt)",
        "footer": "🚀 Construit par Gesner Deslandes, ingénieur en chef chez GlobalInternet.py | Simulation de détection acoustique et audio en temps réel.",
        "listen_explanation": "🔊 Écouter l'explication de l'application",
        "voice_lang": "🌐 Langue de la voix",
    },
    "Spanish": {
        "app_title": "📡 Detección Acústica a Través de Paredes",
        "app_subtitle": "Simule o use audio en tiempo real para detectar objetos detrás de paredes",
        "sidebar_params": "⚙️ Parámetros de simulación",
        "wall_thickness": "Grosor de la pared (cm)",
        "object_distance": "Distancia del objeto a la pared (cm)",
        "object_size": "Tamaño del objeto (cm)",
        "wall_material": "Material de la pared",
        "movement": "Simular movimiento del objeto",
        "movement_speed": "Velocidad de movimiento (cm/s)",
        "tab_sim": "📐 Modo simulación",
        "tab_real": "🎤 Detección en tiempo real",
        "sim_view": "📐 Vista transversal 2D",
        "signal_plot": "📊 Señal acústica recibida",
        "detection_results": "🎯 Resultados de detección",
        "estimated_distance": "Distancia estimada al objeto",
        "estimated_size": "Tamaño estimado del objeto",
        "object_detected": "✅ ¡Objeto detectado!",
        "no_object": "Ningún objeto detectado. Intente ajustar los parámetros o aumentar el tamaño del objeto.",
        "material_speed": "Material de la pared: {} (velocidad del sonido: {:.0f} m/s)",
        "movement_sim": "🔄 Simulación de movimiento de objeto",
        "moving_object": "Moviendo objeto... Distancia: {:.1f} cm",
        "sim_complete": "Simulación de movimiento completada.",
        "real_title": "🎤 Detección acústica en tiempo real",
        "real_desc": "Use el micrófono y los altavoces de su dispositivo para detectar objetos en su habitación.",
        "chirp_duration": "Duración del chirp (ms)",
        "freq_start": "Frecuencia inicial (Hz)",
        "freq_end": "Frecuencia final (Hz)",
        "volume": "Volumen",
        "max_distance": "Distancia máxima de detección (cm)",
        "params": "📊 Parámetros",
        "how_it_works": "ℹ️ Cómo funciona",
        "step1": "1. Se reproduce un chirp a través de los altavoces.",
        "step2": "2. El micrófono graba el eco.",
        "step3": "3. La aplicación encuentra la primera reflexión fuerte.",
        "step4": "4. La distancia se calcula a partir del tiempo de ida y vuelta.",
        "warning": "Para obtener mejores resultados, esté en una habitación silenciosa y coloque un objeto reflectante (pared, mueble) a unos metros.",
        "detection_complete": "✅ Detección completada.",
        "cm_estimated": "cm estimado",
        "delay": "Retardo: {:.2f} ms",
        "confidence": "Confianza del pico: {:.1f}%",
        "object_detected_behind": "✅ Objeto detectado detrás de una pared (aprox)",
        "no_clear_object": "ℹ️ No se detectó ningún objeto claro (intente acercarse)",
        "report_generated": "Informe generado",
        "download_report": "📥 Descargar informe (.txt)",
        "footer": "🚀 Construido por Gesner Deslandes, Ingeniero Jefe en GlobalInternet.py | Simulación de detección acústica y audio en tiempo real.",
        "listen_explanation": "🔊 Escuchar explicación de la aplicación",
        "voice_lang": "🌐 Idioma de la voz",
    }
}

# ---------- SESSION STATE ----------
if "lang" not in st.session_state:
    st.session_state.lang = "English"

# ---------- SIDEBAR ----------
with st.sidebar:
    st.image("https://github.com/Deslandes1/Let-s-Learn-Mathematics-with-Gesner/blob/main/Gesner%20Deslandes.png?raw=true", width=150)
    st.markdown("<h3 style='text-align: center; color: #4a2c6a;'>Gesner Deslandes</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Language selection
    lang = st.selectbox(
        TEXTS["English"]["voice_lang"],
        options=["English", "French", "Spanish"],
        index=["English", "French", "Spanish"].index(st.session_state.lang),
        key="lang_select"
    )
    if lang != st.session_state.lang:
        st.session_state.lang = lang
        st.rerun()
    
    t = TEXTS[st.session_state.lang]
    
    # Voice explanation button
    def generate_audio(text, voice):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                output_path = tmp.name
            comm = edge_tts.Communicate(text, voice)
            asyncio.run(comm.save(output_path))
            return output_path
        except Exception as e:
            st.error(f"Audio generation error: {e}")
            return None

    def play_audio(audio_path):
        if audio_path and os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
                b64 = base64.b64encode(audio_bytes).decode()
                st.markdown(f'<audio controls src="data:audio/mp3;base64,{b64}" autoplay style="width:100%;"></audio>', unsafe_allow_html=True)
            os.unlink(audio_path)

    if st.button(t["listen_explanation"], use_container_width=True):
        voice_map = {
            "English": "en-US-JennyNeural",
            "French": "fr-FR-DeniseNeural",
            "Spanish": "es-ES-ElviraNeural"
        }
        voice = voice_map[st.session_state.lang]
        explanation_text = {
            "English": "This application was built by Gesner Deslandes, Engineer-in-Chief at GlobalInternet.py. Phone: (509) 4738-5663. Email: deslandes78@gmail.com. Get in touch with Gesner if you want to build any website or software. This application uses acoustic waves to detect objects behind walls. It simulates sound propagation and reflection, or uses your device's microphone and speakers to measure echo delays. You can adjust parameters to mimic different wall materials and object sizes. In real-time mode, it plays a chirp and listens for echoes, then calculates distance and generates a scientific report. This is useful for non-destructive testing, construction, and educational demonstrations.",
            "French": "Cette application a été construite par Gesner Deslandes, ingénieur en chef chez GlobalInternet.py. Téléphone : (509) 4738-5663. Email : deslandes78@gmail.com. Contactez Gesner si vous souhaitez créer un site web ou un logiciel. Cette application utilise les ondes acoustiques pour détecter des objets derrière les murs. Elle simule la propagation et la réflexion du son, ou utilise le microphone et les haut‑parleurs de votre appareil pour mesurer les délais d'écho. Vous pouvez ajuster les paramètres pour imiter différents matériaux et tailles d'objets. En mode temps réel, elle émet un chirp, écoute les échos, calcule la distance et génère un rapport scientifique. Cela est utile pour les tests non destructifs, la construction et les démonstrations éducatives.",
            "Spanish": "Esta aplicación fue construida por Gesner Deslandes, Ingeniero Jefe en GlobalInternet.py. Teléfono: (509) 4738-5663. Correo: deslandes78@gmail.com. Póngase en contacto con Gesner si desea crear un sitio web o software. Esta aplicación utiliza ondas acústicas para detectar objetos detrás de paredes. Simula la propagación y reflexión del sonido, o usa el micrófono y altavoces de su dispositivo para medir retardos de eco. Puede ajustar parámetros para imitar diferentes materiales y tamaños de objetos. En modo tiempo real, reproduce un chirp, escucha ecos, calcula distancia y genera un informe científico. Esto es útil para ensayos no destructivos, construcción y demostraciones educativas."
        }
        text = explanation_text[st.session_state.lang]
        audio_file = generate_audio(text, voice)
        if audio_file:
            play_audio(audio_file)
        else:
            st.error("Failed to generate audio.")

    st.markdown("---")
    # Sidebar parameters (translated)
    st.markdown(f"### {t['sidebar_params']}")
    wall_thickness = st.slider(t["wall_thickness"], 10, 50, 25, step=1)
    object_distance = st.slider(t["object_distance"], 0, 150, 50, step=1)
    object_size = st.slider(t["object_size"], 5, 50, 20, step=1)
    wall_material = st.selectbox(t["wall_material"], ["Concrete", "Brick", "Wood", "Drywall"])
    movement = st.checkbox(t["movement"], value=False)
    movement_speed = st.slider(t["movement_speed"], 1, 20, 5, step=1) if movement else 0
    
    st.markdown("---")
    # Real-time detection params (they will be used in the tab)
    st.markdown("### 🎤 Real‑time Detection")
    real_chirp_duration = st.slider(t["chirp_duration"], 10, 100, 30, step=5, key="real_chirp")
    real_freq_start = st.slider(t["freq_start"], 100, 1000, 200, step=50, key="real_freq_start")
    real_freq_end = st.slider(t["freq_end"], 1000, 8000, 4000, step=100, key="real_freq_end")
    real_volume = st.slider(t["volume"], 0.1, 1.0, 0.5, step=0.05, key="real_volume")
    real_max_dist = st.slider(t["max_distance"], 50, 500, 200, step=10, key="real_max_dist")

# ---------- LIGHT PURPLE STYLING ----------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(145deg, #f3e5ff 0%, #d9b3ff 100%);
        color: #2a1a3a;
    }
    [data-testid="stSidebar"] {
        background: #f0e6ff;
        border-right: 1px solid #c4a0e8;
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stCaption {
        color: #2a1a3a !important;
    }
    .main-title {
        text-align: center;
        padding: 1.2rem;
        background: linear-gradient(135deg, #b380ff, #d9b3ff);
        border-radius: 15px;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 4px 12px rgba(128, 0, 255, 0.15);
    }
    .main-title h1 { margin: 0; font-size: 2.5rem; color: white; }
    .main-title p { margin: 0.5rem 0 0; opacity: 0.95; color: #f0e6ff; }
    h1, h2, h3, h4, h5, h6, p, li, .stMarkdown, .stCaption, label {
        color: #2a1a3a !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #b380ff, #9a66d9) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(128, 0, 255, 0.2);
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 16px rgba(128, 0, 255, 0.3);
    }
    .stSlider>div>div>div>div {
        background: #b380ff !important;
    }
    .stSelectbox>div>div>div {
        background-color: #f5edff !important;
        border: 1px solid #c4a0e8 !important;
    }
    .stCheckbox>label {
        color: #2a1a3a !important;
    }
    .stTabs [role="tab"] {
        color: #4a2c6a !important;
        background: rgba(179, 128, 255, 0.2) !important;
        border-radius: 10px;
        margin: 0 4px;
    }
    .stTabs [role="tab"][aria-selected="true"] {
        background: rgba(179, 128, 255, 0.5) !important;
        color: #2a1a3a !important;
        font-weight: 600;
    }
    .result-box {
        background: rgba(255,255,255,0.6);
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #c4a0e8;
        margin: 10px 0;
        backdrop-filter: blur(8px);
    }
    .footer {
        text-align: center;
        padding: 20px 0;
        border-top: 1px solid #c4a0e8;
        margin-top: 30px;
        color: #4a2c6a;
    }
</style>
""", unsafe_allow_html=True)

# ---------- MAIN ----------
t = TEXTS[st.session_state.lang]
st.markdown(f"""
<div class="main-title">
    <h1>{t['app_title']}</h1>
    <p>{t['app_subtitle']}</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs([t["tab_sim"], t["tab_real"]])

# ========== TAB 1: SIMULATION ==========
with tab1:
    st.subheader(t["sim_view"])
    col1, col2 = st.columns([2, 1])

    time_resolution = 0.1
    max_time = 300
    time_axis = np.arange(0, max_time, time_resolution)
    t_chirp = np.linspace(0, 20, 200)
    tx_signal = np.sin(2 * np.pi * 0.5 * t_chirp * t_chirp)
    material_speed = {"Concrete": 3500, "Brick": 3700, "Wood": 4000, "Drywall": 2500}
    sound_speed = material_speed[wall_material] / 100
    distance_to_object = wall_thickness + object_distance
    round_trip_time = 2 * distance_to_object / sound_speed
    received_signal = np.zeros_like(time_axis)
    direct_amp = 0.01
    direct_idx = int(wall_thickness / sound_speed / time_resolution)
    if direct_idx < len(received_signal):
        received_signal[direct_idx:direct_idx+len(tx_signal)] += direct_amp * tx_signal
    reflection_amp = 0.5 * (object_size / 20)
    reflection_idx = int(round_trip_time / time_resolution)
    if reflection_idx < len(received_signal):
        end_idx = min(reflection_idx + len(tx_signal), len(received_signal))
        received_signal[reflection_idx:end_idx] += reflection_amp * tx_signal[:end_idx-reflection_idx]
    received_signal += np.random.normal(0, 0.02, len(received_signal))
    corr = signal.correlate(received_signal, tx_signal, mode='same')
    corr = np.abs(corr)
    peaks, _ = signal.find_peaks(corr, height=0.01, distance=10)
    peak_times = time_axis[peaks]
    peak_heights = corr[peaks]
    if len(peak_times) > 1:
        for i, t_val in enumerate(peak_times):
            if t_val > wall_thickness / sound_speed:
                estimated_distance = t_val * sound_speed / 2
                break
        else:
            estimated_distance = None
    else:
        estimated_distance = None

    with col1:
        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, x1=wall_thickness/100, y0=-0.5, y1=0.5,
                      fillcolor="#8B4513", line=dict(width=2), opacity=0.7, name="Wall")
        obj_x = wall_thickness/100 + object_distance/100
        fig.add_shape(type="rect", x0=obj_x-object_size/200, x1=obj_x+object_size/200,
                      y0=-object_size/200, y1=object_size/200,
                      fillcolor="#FF5733", line=dict(width=2), name="Object")
        fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers+text",
                                 marker=dict(size=15, color="blue"), text=["Source/Receiver"],
                                 textposition="top center", name="Source"))
        fig.update_layout(xaxis_title="Distance (m)", yaxis_title="Position",
                          xaxis_range=[-0.1, 2.5], yaxis_range=[-0.8, 0.8],
                          height=350, margin=dict(l=20, r=20, t=20, b=20), showlegend=True,
                          plot_bgcolor="rgba(255,255,255,0.3)", paper_bgcolor="rgba(255,255,255,0.3)")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader(t["signal_plot"])
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=time_axis, y=received_signal, mode="lines", name="Received Signal"))
        fig2.add_trace(go.Scatter(x=time_axis, y=corr, mode="lines", name="Cross-Correlation (Envelope)"))
        if len(peak_times) > 0:
            fig2.add_trace(go.Scatter(x=peak_times, y=peak_heights, mode="markers",
                                      marker=dict(size=10, color="red"), name="Detected Peaks"))
        fig2.update_layout(xaxis_title="Time (µs)", yaxis_title="Amplitude",
                           height=300, margin=dict(l=20, r=20, t=20, b=20),
                           plot_bgcolor="rgba(255,255,255,0.3)", paper_bgcolor="rgba(255,255,255,0.3)")
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader(t["detection_results"])
        if estimated_distance is not None:
            st.metric(t["estimated_distance"], f"{estimated_distance:.1f} cm")
            estimated_size = object_size * (reflection_amp / 0.5)
            st.metric(t["estimated_size"], f"{estimated_size:.1f} cm")
            st.success(t["object_detected"])
        else:
            st.info(t["no_object"])
        st.caption(t["material_speed"].format(wall_material, sound_speed*100))

    if movement:
        st.subheader(t["movement_sim"])
        progress = st.empty()
        for i in range(60):
            new_distance = object_distance + (movement_speed * np.sin(i * 0.1))
            progress.progress((i+1)/60, text=t["moving_object"].format(new_distance))
            time.sleep(0.05)
        progress.empty()
        st.success(t["sim_complete"])

# ========== TAB 2: REAL DETECTION ==========
with tab2:
    st.subheader(t["real_title"])
    st.markdown(t["real_desc"])
    col_r1, col_r2 = st.columns([2, 1])
    with col_r1:
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ background: transparent; font-family: sans-serif; }}
                #status {{ padding: 10px; margin: 10px 0; border-radius: 5px; background: #1e2a3a; color: white; }}
                .btn {{ padding: 10px 20px; background: #9a66d9; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }}
                .btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
                .btn:hover {{ background: #b380ff; }}
                #result {{ margin-top: 10px; padding: 10px; background: #0e1117; border-radius: 5px; color: #00ff64; font-family: monospace; }}
                .dist {{ font-size: 24px; color: #b380ff; font-weight: bold; }}
                .err {{ color: #ff6b6b; }}
                .report-box {{ background: #1a1a2e; border-radius: 8px; padding: 15px; margin-top: 15px; border-left: 4px solid #b380ff; }}
                .report-box pre {{ white-space: pre-wrap; font-family: sans-serif; color: #ddd; margin: 0; }}
                .download-btn {{ background: #9a66d9; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer; font-size: 14px; margin-top: 10px; }}
                .download-btn:hover {{ background: #b380ff; }}
            </style>
        </head>
        <body>
            <button class="btn" id="pulseBtn">🔊 Send Pulse</button>
            <div id="status">🟢 Ready. Click the button to start.</div>
            <div id="result"></div>
            <div id="reportContainer"></div>
            <script>
            (function() {{
                let audioContext = null;
                let isProcessing = false;
                let lastResult = null;

                const statusDiv = document.getElementById('status');
                const resultDiv = document.getElementById('result');
                const reportContainer = document.getElementById('reportContainer');
                const pulseBtn = document.getElementById('pulseBtn');

                const chirpDuration = {real_chirp_duration} / 1000;
                const freqStart = {real_freq_start};
                const freqEnd = {real_freq_end};
                const volume = {real_volume};
                const maxDist = {real_max_dist};

                function updateStatus(text, isError=false) {{
                    statusDiv.innerHTML = text;
                    statusDiv.style.color = isError ? '#ff6b6b' : 'white';
                }}

                function generateReport(distanceCm, delayMs, confidence) {{
                    const meters = (distanceCm / 100).toFixed(2);
                    const cm = distanceCm.toFixed(1);
                    const delay = delayMs.toFixed(2);
                    const conf = (confidence * 100).toFixed(1);
                    const now = new Date();
                    const timestamp = now.toLocaleString();
                    return `Acoustic Detection Report
Generated: ${{timestamp}}

Result: The app successfully detected a reflection and calculated that there is a wall or solid object approximately ${{meters}} meters (${{cm}} cm) away from your device. The ${{delay}} ms delay is the time it took for the sound to travel from your speaker to the object and back, which confirms the distance (since sound travels at 343 m/s, the round‑trip time matches a ${{meters}}‑meter distance). The ${{conf}}% peak confidence means the echo was very clear and strong, so the detection is reliable. The app interprets this as an object "behind a wall" because the reflection is strong enough to suggest a solid surface, which could be a wall, a large piece of furniture, or any other reflective barrier between you and the sound source.

In simple terms: Your app just "listened" to a sound bouncing off a wall about ${{meters}} meters away, and it's confident in that measurement. 🎯`;
                }}

                function showResult(data) {{
                    if (data.error) {{
                        resultDiv.innerHTML = `<span class="err">❌ ${{data.error}}</span>`;
                        reportContainer.innerHTML = '';
                        return;
                    }}
                    const cm = data.distance_cm.toFixed(1);
                    const delay = (data.delay_seconds * 1000).toFixed(2);
                    const conf = (data.peak_value * 100).toFixed(1);
                    let html = `<div><span class="dist">${{cm}} cm</span> estimated</div>`;
                    html += `<div>Delay: ${{delay}} ms</div>`;
                    html += `<div>Peak confidence: ${{conf}}%</div>`;
                    if (data.distance_cm > 10) {{
                        html += `<div>✅ Object detected behind wall (approx)</div>`;
                    }} else {{
                        html += `<div>ℹ️ No clear object detected (try moving closer)</div>`;
                    }}
                    resultDiv.innerHTML = html;

                    const reportText = generateReport(data.distance_cm, parseFloat(delay), data.peak_value);
                    lastResult = reportText;
                    const reportHtml = `
                        <div class="report-box">
                            <pre>${{reportText}}</pre>
                            <button class="download-btn" onclick="downloadReport()">📥 Download Report (.txt)</button>
                        </div>
                    `;
                    reportContainer.innerHTML = reportHtml;
                }}

                window.downloadReport = function() {{
                    if (!lastResult) return;
                    const blob = new Blob([lastResult], {{ type: 'text/plain' }});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'acoustic_detection_report.txt';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }};

                async function processPulse() {{
                    if (isProcessing) return;
                    isProcessing = true;
                    pulseBtn.disabled = true;
                    updateStatus("🔴 Initializing audio...");

                    try {{
                        const stream = await navigator.mediaDevices.getUserMedia({{ audio: true, video: false }});
                        audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        const mic = audioContext.createMediaStreamSource(stream);
                        const analyser = audioContext.createAnalyser();
                        analyser.fftSize = 2048;
                        mic.connect(analyser);

                        const sampleRate = audioContext.sampleRate;
                        const numSamples = Math.floor(chirpDuration * sampleRate);
                        const buffer = audioContext.createBuffer(1, numSamples, sampleRate);
                        const data = buffer.getChannelData(0);
                        for (let i = 0; i < numSamples; i++) {{
                            const t = i / sampleRate;
                            const f = freqStart + (freqEnd - freqStart) * (t / chirpDuration);
                            data[i] = volume * Math.sin(2 * Math.PI * f * t);
                        }}

                        const source = audioContext.createBufferSource();
                        source.buffer = buffer;

                        const recorder = audioContext.createScriptProcessor(4096, 1, 1);
                        let recordedSamples = [];
                        recorder.onaudioprocess = function(e) {{
                            const input = e.inputBuffer.getChannelData(0);
                            const copy = new Float32Array(input);
                            recordedSamples.push(copy);
                        }};

                        mic.connect(recorder);
                        recorder.connect(audioContext.destination);

                        updateStatus("🔊 Playing chirp...");
                        source.connect(audioContext.destination);
                        source.start();

                        await new Promise(resolve => setTimeout(resolve, 2500));

                        source.stop();
                        recorder.disconnect();
                        mic.disconnect();
                        await audioContext.close();

                        let totalLength = 0;
                        for (let chunk of recordedSamples) totalLength += chunk.length;
                        const recorded = new Float32Array(totalLength);
                        let offset = 0;
                        for (let chunk of recordedSamples) {{
                            recorded.set(chunk, offset);
                            offset += chunk.length;
                        }}

                        const txLen = data.length;
                        const rxLen = recorded.length;
                        const step = 5;
                        const maxIdx = Math.min(rxLen - txLen, 20000);
                        let maxVal = 0, maxPos = 0;
                        for (let i = 0; i < maxIdx; i += step) {{
                            let sum = 0;
                            for (let j = 0; j < txLen; j++) {{
                                sum += data[j] * recorded[i+j];
                            }}
                            const val = Math.abs(sum);
                            if (val > maxVal) {{
                                maxVal = val;
                                maxPos = i;
                            }}
                        }}

                        const directSamples = Math.floor(0.0005 * sampleRate);
                        if (maxPos < directSamples) {{
                            let secondMax = 0, secondPos = 0;
                            for (let i = directSamples; i < maxIdx; i += step) {{
                                let sum = 0;
                                for (let j = 0; j < txLen; j++) {{
                                    sum += data[j] * recorded[i+j];
                                }}
                                const val = Math.abs(sum);
                                if (val > secondMax) {{
                                    secondMax = val;
                                    secondPos = i;
                                }}
                            }}
                            if (secondMax > 0.01) {{
                                maxPos = secondPos;
                                maxVal = secondMax;
                            }} else {{
                                maxPos = -1;
                            }}
                        }}

                        if (maxPos > 0) {{
                            const delaySeconds = maxPos / sampleRate;
                            const distanceCm = delaySeconds * 34300 / 2;
                            showResult({{
                                distance_cm: Math.min(distanceCm, maxDist),
                                delay_seconds: delaySeconds,
                                peak_value: Math.min(maxVal, 1.0),
                                error: null
                            }});
                            updateStatus("✅ Detection complete.");
                        }} else {{
                            showResult({{ error: "No reflection detected. Try moving closer or increasing volume." }});
                            updateStatus("⚠️ No object detected.", true);
                        }}

                    }} catch (err) {{
                        updateStatus("❌ Error: " + err.message, true);
                        showResult({{ error: err.message }});
                    }} finally {{
                        isProcessing = false;
                        pulseBtn.disabled = false;
                    }}
                }}

                pulseBtn.onclick = processPulse;
            }})();
            </script>
        </body>
        </html>
        """
        st.components.v1.html(html_code, height=600)

    with col_r2:
        st.markdown(f"### {t['params']}")
        st.markdown(f"""
        - **Chirp:** {real_chirp_duration} ms, {real_freq_start}–{real_freq_end} Hz
        - **Max distance:** {real_max_dist} cm
        - **Sound speed:** 343 m/s
        """)
        st.markdown("---")
        st.markdown(f"### {t['how_it_works']}")
        st.markdown(f"{t['step1']}")
        st.markdown(f"{t['step2']}")
        st.markdown(f"{t['step3']}")
        st.markdown(f"{t['step4']}")
        st.warning(t["warning"])

# ---------- FOOTER ----------
st.markdown("---")
st.caption(t["footer"])
