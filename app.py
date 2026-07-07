import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy import signal
import time

st.set_page_config(
    page_title="Acoustic Through-Wall Detection | GlobalInternet.py",
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
    <h1>📡 Acoustic Through‑Wall Detection</h1>
    <p>Simulate or use real‑time audio to detect objects behind walls</p>
</div>
""", unsafe_allow_html=True)

# ---------- SIDEBAR PARAMETERS ----------
st.sidebar.header("⚙️ Simulation Parameters")
wall_thickness = st.sidebar.slider("Wall Thickness (cm)", 10, 50, 25, step=1)
object_distance = st.sidebar.slider("Object Distance from Wall (cm)", 0, 150, 50, step=1)
object_size = st.sidebar.slider("Object Size (cm)", 5, 50, 20, step=1)
wall_material = st.sidebar.selectbox("Wall Material", ["Concrete", "Brick", "Wood", "Drywall"])
movement = st.sidebar.checkbox("Simulate Object Movement", value=False)
movement_speed = st.sidebar.slider("Movement Speed (cm/s)", 1, 20, 5, step=1) if movement else 0

material_speed = {
    "Concrete": 3500,
    "Brick": 3700,
    "Wood": 4000,
    "Drywall": 2500
}
sound_speed = material_speed[wall_material] / 100  # cm/µs

# ---------- TABS ----------
tab1, tab2 = st.tabs(["📐 Simulation Mode", "🎤 Real‑time Detection"])

# ========== TAB 1: SIMULATION ==========
with tab1:
    st.subheader("📐 2D Cross‑Section View")
    col1, col2 = st.columns([2, 1])

    # Simulation time grid
    time_resolution = 0.1  # microseconds
    max_time = 300  # microseconds
    time_axis = np.arange(0, max_time, time_resolution)

    # Generate transmitted pulse (chirp)
    t_chirp = np.linspace(0, 20, 200)
    tx_signal = np.sin(2 * np.pi * 0.5 * t_chirp * t_chirp)

    # Compute round-trip time to object and back
    distance_to_object = wall_thickness + object_distance
    round_trip_time = 2 * distance_to_object / sound_speed  # µs

    # Simulate received signal: transmitted pulse + attenuated echo + noise
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

    # Detection algorithm
    corr = signal.correlate(received_signal, tx_signal, mode='same')
    corr = np.abs(corr)
    peaks, _ = signal.find_peaks(corr, height=0.01, distance=10)
    peak_times = time_axis[peaks]
    peak_heights = corr[peaks]

    if len(peak_times) > 1:
        for i, t in enumerate(peak_times):
            if t > wall_thickness / sound_speed:
                estimated_distance = t * sound_speed / 2
                break
        else:
            estimated_distance = None
    else:
        estimated_distance = None

    with col1:
        # Cross-section plot
        fig = go.Figure()
        fig.add_shape(
            type="rect", x0=0, x1=wall_thickness/100, y0=-0.5, y1=0.5,
            fillcolor="#8B4513", line=dict(width=2), opacity=0.7,
            name="Wall"
        )
        obj_x = wall_thickness/100 + object_distance/100
        fig.add_shape(
            type="rect", x0=obj_x-object_size/200, x1=obj_x+object_size/200,
            y0=-object_size/200, y1=object_size/200,
            fillcolor="#FF5733", line=dict(width=2), name="Object"
        )
        fig.add_trace(go.Scatter(
            x=[0], y=[0], mode="markers+text",
            marker=dict(size=15, color="blue"), text=["Source/Receiver"], textposition="top center",
            name="Source"
        ))
        fig.update_layout(
            xaxis_title="Distance (m)",
            yaxis_title="Position",
            xaxis_range=[-0.1, 2.5],
            yaxis_range=[-0.8, 0.8],
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)

        # Signal plot
        st.subheader("📊 Received Acoustic Signal")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=time_axis, y=received_signal, mode="lines", name="Received Signal"))
        fig2.add_trace(go.Scatter(x=time_axis, y=corr, mode="lines", name="Cross-Correlation (Envelope)"))
        if len(peak_times) > 0:
            fig2.add_trace(go.Scatter(
                x=peak_times, y=peak_heights, mode="markers",
                marker=dict(size=10, color="red"), name="Detected Peaks"
            ))
        fig2.update_layout(
            xaxis_title="Time (µs)",
            yaxis_title="Amplitude",
            height=300,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("🎯 Detection Results")
        if estimated_distance is not None:
            st.metric("Estimated Object Distance", f"{estimated_distance:.1f} cm")
            estimated_size = object_size * (reflection_amp / 0.5)
            st.metric("Estimated Object Size", f"{estimated_size:.1f} cm")
            st.success("✅ Object detected!")
        else:
            st.info("No object detected. Try adjusting parameters or increasing object size.")
        st.caption(f"Wall material: {wall_material} (sound speed: {sound_speed*100:.0f} m/s)")

    # Movement simulation
    if movement:
        st.subheader("🔄 Object Movement Simulation")
        progress = st.empty()
        for i in range(60):
            new_distance = object_distance + (movement_speed * np.sin(i * 0.1))
            progress.progress((i+1)/60, text=f"Moving object... Distance: {new_distance:.1f} cm")
            time.sleep(0.05)
        progress.empty()
        st.success("Movement simulation completed.")

# ========== TAB 2: REAL DETECTION ==========
with tab2:
    st.subheader("🎤 Real‑time Acoustic Detection")
    st.markdown("Use your device's microphone and speakers to detect objects in your room.")

    col_r1, col_r2 = st.columns([2, 1])

    with col_r1:
        # Parameters for real detection (can share with sidebar)
        real_chirp_duration = st.sidebar.slider("Chirp Duration (ms)", 10, 100, 30, step=5, key="real_chirp")
        real_freq_start = st.sidebar.slider("Start Frequency (Hz)", 100, 1000, 200, step=50, key="real_freq_start")
        real_freq_end = st.sidebar.slider("End Frequency (Hz)", 1000, 8000, 4000, step=100, key="real_freq_end")
        real_volume = st.sidebar.slider("Volume", 0.1, 1.0, 0.5, step=0.05, key="real_volume")
        real_max_dist = st.sidebar.slider("Max Detection Distance (cm)", 50, 500, 200, step=10, key="real_max_dist")

        # HTML component with Web Audio API
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

                const chirpDuration = {real_chirp_duration} / 1000;
                const freqStart = {real_freq_start};
                const freqEnd = {real_freq_end};
                const volume = {real_volume};
                const maxDist = {real_max_dist};

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
        st.components.v1.html(html_code, height=350)

    with col_r2:
        st.markdown("### 📊 Parameters")
        st.markdown(f"""
        - **Chirp:** {real_chirp_duration} ms, {real_freq_start}–{real_freq_end} Hz
        - **Max distance:** {real_max_dist} cm
        - **Sound speed:** 343 m/s
        """)
        st.markdown("---")
        st.markdown("### ℹ️ How it works")
        st.markdown("""
        1. A chirp is played through your speakers.
        2. The microphone records the echo.
        3. The app finds the first strong reflection.
        4. Distance is calculated from round‑trip time.
        """)
        st.warning("For best results, be in a quiet room and place a reflective object (wall, cabinet) a few meters away.")

# ---------- FOOTER ----------
st.markdown("---")
st.caption("🚀 Built by Gesner Deslandes, Engineer-in-Chief at GlobalInternet.py | Acoustic detection simulation & real‑time audio.")
