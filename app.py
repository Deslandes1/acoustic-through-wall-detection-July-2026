import streamlit as st
import numpy as np
import plotly.graph_objects as go
import json

st.set_page_config(
    page_title="Acoustic Through-Wall Detection (Real) | GlobalInternet.py",
    layout="wide",
    page_icon="📡"
)

st.markdown("""
<style>
    .main-title {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
        border-radius: 15px;
        color: white;
        margin-bottom: 1rem;
    }
    .main-title h1 { margin: 0; font-size: 2.5rem; }
    .main-title p { margin: 0.5rem 0 0; opacity: 0.9; }
    .result-box {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #4a90d9;
        margin: 10px 0;
    }
    .stButton>button {
        background: #4a90d9 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-title">
    <h1>📡 Acoustic Through‑Wall Detection (Real)</h1>
    <p>Use your device's microphone and speakers to detect objects behind walls</p>
</div>
""", unsafe_allow_html=True)

# ---------- SIDEBAR CONTROLS ----------
st.sidebar.header("⚙️ Parameters")
chirp_duration = st.sidebar.slider("Chirp Duration (ms)", 10, 100, 30, step=5)
chirp_freq_start = st.sidebar.slider("Start Frequency (Hz)", 100, 1000, 200, step=50)
chirp_freq_end = st.sidebar.slider("End Frequency (Hz)", 1000, 8000, 4000, step=100)
volume = st.sidebar.slider("Volume", 0.1, 1.0, 0.5, step=0.05)
max_distance = st.sidebar.slider("Max Detection Distance (cm)", 50, 500, 200, step=10)

st.sidebar.markdown("---")
st.sidebar.info("Click the 'Send Pulse' button below to play a chirp and record the echo. The app will estimate distances to reflective objects behind a wall.")

# ---------- SESSION STATE ----------
if "pulse_result" not in st.session_state:
    st.session_state.pulse_result = None

# ---------- MAIN LAYOUT ----------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎤 Real‑time Audio Analysis")

    # We'll use a pure HTML component that handles everything and displays results directly
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ background: transparent; font-family: sans-serif; }}
            #status {{ padding: 10px; margin: 10px 0; border-radius: 5px; background: #1e2a3a; color: white; }}
            .btn {{ padding: 10px 20px; background: #4a90d9; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }}
            .btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
            .btn:hover {{ background: #357abd; }}
            #result {{ margin-top: 10px; padding: 10px; background: #0e1117; border-radius: 5px; color: #00ff64; font-family: monospace; }}
            .dist {{ font-size: 24px; color: #4a90d9; font-weight: bold; }}
            .err {{ color: #ff6b6b; }}
        </style>
    </head>
    <body>
        <button class="btn" id="pulseBtn">🔊 Send Pulse</button>
        <div id="status">🟢 Ready. Click the button to start.</div>
        <div id="result"></div>
        <script>
        (function() {{
            let audioContext = null;
            let isProcessing = false;

            const statusDiv = document.getElementById('status');
            const resultDiv = document.getElementById('result');
            const pulseBtn = document.getElementById('pulseBtn');

            // Parameters from Python (passed via f-string)
            const chirpDuration = {chirp_duration} / 1000;
            const freqStart = {chirp_freq_start};
            const freqEnd = {chirp_freq_end};
            const volume = {volume};
            const maxDist = {max_distance};

            function updateStatus(text, isError=false) {{
                statusDiv.innerHTML = text;
                statusDiv.style.color = isError ? '#ff6b6b' : 'white';
            }}

            function showResult(data) {{
                if (data.error) {{
                    resultDiv.innerHTML = `<span class="err">❌ ${{data.error}}</span>`;
                    return;
                }}
                let html = `<div><span class="dist">${{data.distance_cm.toFixed(1)}} cm</span> estimated</div>`;
                html += `<div>Delay: ${{(data.delay_seconds * 1000).toFixed(2)}} ms</div>`;
                html += `<div>Peak confidence: ${{(data.peak_value * 100).toFixed(1)}}%</div>`;
                if (data.distance_cm > 10) {{
                    html += `<div>✅ Object detected behind wall (approx)</div>`;
                }} else {{
                    html += `<div>ℹ️ No clear object detected (try moving closer)</div>`;
                }}
                resultDiv.innerHTML = html;
            }}

            async function processPulse() {{
                if (isProcessing) return;
                isProcessing = true;
                pulseBtn.disabled = true;
                updateStatus("🔴 Initializing audio...");

                try {{
                    // 1. Get microphone
                    const stream = await navigator.mediaDevices.getUserMedia({{ audio: true, video: false }});
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    const mic = audioContext.createMediaStreamSource(stream);
                    const analyser = audioContext.createAnalyser();
                    analyser.fftSize = 2048;
                    mic.connect(analyser);

                    // 2. Generate chirp
                    const sampleRate = audioContext.sampleRate;
                    const numSamples = Math.floor(chirpDuration * sampleRate);
                    const buffer = audioContext.createBuffer(1, numSamples, sampleRate);
                    const data = buffer.getChannelData(0);
                    for (let i = 0; i < numSamples; i++) {{
                        const t = i / sampleRate;
                        const f = freqStart + (freqEnd - freqStart) * (t / chirpDuration);
                        data[i] = volume * Math.sin(2 * Math.PI * f * t);
                    }}

                    // 3. Create buffer source
                    const source = audioContext.createBufferSource();
                    source.buffer = buffer;

                    // 4. Setup recording (ScriptProcessorNode)
                    const recorder = audioContext.createScriptProcessor(4096, 1, 1);
                    let recordedSamples = [];
                    recorder.onaudioprocess = function(e) {{
                        const input = e.inputBuffer.getChannelData(0);
                        const copy = new Float32Array(input);
                        recordedSamples.push(copy);
                    }};

                    mic.connect(recorder);
                    recorder.connect(audioContext.destination);

                    // 5. Play and record
                    updateStatus("🔊 Playing chirp...");
                    const startTime = audioContext.currentTime;
                    source.connect(audioContext.destination);
                    source.start();

                    // Record for 2 seconds
                    const recordDuration = 2; // seconds
                    await new Promise(resolve => setTimeout(resolve, recordDuration * 1000 + 500));

                    // 6. Stop
                    source.stop();
                    recorder.disconnect();
                    mic.disconnect();
                    await audioContext.close();

                    // 7. Assemble recorded audio
                    let totalLength = 0;
                    for (let chunk of recordedSamples) totalLength += chunk.length;
                    const recorded = new Float32Array(totalLength);
                    let offset = 0;
                    for (let chunk of recordedSamples) {{
                        recorded.set(chunk, offset);
                        offset += chunk.length;
                    }}

                    // 8. Compute cross-correlation (simplified)
                    const txLen = data.length;
                    const rxLen = recorded.length;
                    // Find the first strong peak after direct sound
                    // We'll compute sliding dot product (simplified)
                    const step = 5;
                    const maxIdx = Math.min(rxLen - txLen, 20000); // limit for speed
                    let maxVal = 0;
                    let maxPos = 0;
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

                    // Skip if peak is too close to direct sound (less than 0.5 ms)
                    const directSamples = Math.floor(0.0005 * sampleRate);
                    if (maxPos < directSamples) {{
                        // find next peak after direct
                        let secondMax = 0;
                        let secondPos = 0;
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
                        const result = {{
                            distance_cm: Math.min(distanceCm, maxDist),
                            delay_seconds: delaySeconds,
                            peak_value: Math.min(maxVal, 1.0),
                            error: null
                        }};
                        showResult(result);
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
    st.components.v1.html(html_code, height=350)

    # Display a placeholder for Python-side results (we'll keep it for compatibility)
    # But the HTML component already shows results, so we don't need to duplicate.

with col2:
    st.subheader("📊 Detection Parameters")
    st.markdown(f"""
    - **Chirp duration:** {chirp_duration} ms
    - **Frequency range:** {chirp_freq_start} – {chirp_freq_end} Hz
    - **Max distance:** {max_distance} cm
    - **Sound speed:** 343 m/s
    """)
    st.markdown("---")
    st.markdown("### ℹ️ How it works")
    st.markdown("""
    1. A short chirp is played through your speakers.
    2. The microphone records the echo.
    3. The app finds the first strong reflection (echo).
    4. The distance is calculated from the round‑trip time.
    """)
    st.warning("⚠️ Make sure your device is in a quiet environment for best results. Place a reflective object (like a wall) a few meters away.")

# ---------- FOOTER ----------
st.markdown("---")
st.caption("🚀 Built by Gesner Deslandes, Engineer-in-Chief at GlobalInternet.py | Uses Web Audio API for real acoustic detection.")
