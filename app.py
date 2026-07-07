import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time
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

# Speed of sound in air (cm/µs) – approx 34,300 cm/s = 0.0343 cm/µs
SOUND_SPEED = 0.0343  # cm/µs

st.sidebar.markdown("---")
st.sidebar.info("Click 'Send Pulse' to play a sound and record the echo. The app will estimate distances to reflective objects behind a wall.")

# ---------- SESSION STATE ----------
if "pulse_result" not in st.session_state:
    st.session_state.pulse_result = None
if "trigger_pulse" not in st.session_state:
    st.session_state.trigger_pulse = False

# ---------- HIDDEN BUTTON FOR CALLBACK ----------
def on_pulse_complete():
    # This will be called from JavaScript via a hidden button click
    st.session_state.pulse_result = st.session_state.get("pulse_data", None)
    st.rerun()

if "pulse_complete_btn" not in st.session_state:
    st.button("Pulse Complete", key="pulse_complete_btn", on_click=on_pulse_complete, type="primary", hidden=True)

# ---------- MAIN LAYOUT ----------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎤 Real‑time Audio Analysis")
    # The HTML component will handle microphone, playback, and processing
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ background: transparent; font-family: sans-serif; }}
            #status {{ padding: 10px; margin: 10px 0; border-radius: 5px; background: #1e2a3a; color: white; }}
            .btn {{ padding: 10px 20px; background: #4a90d9; color: white; border: none; border-radius: 5px; cursor: pointer; }}
            .btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
            #result {{ margin-top: 10px; padding: 10px; background: #0e1117; border-radius: 5px; color: #00ff64; font-family: monospace; }}
        </style>
    </head>
    <body>
        <div id="status">🔴 Idle. Click "Send Pulse" in the sidebar.</div>
        <div id="result"></div>
        <script>
        (function() {{
            let audioContext = null;
            let isRecording = false;
            let isProcessing = false;
            let resultSent = false;

            // Parameters
            const chirpDuration = {chirp_duration} / 1000; // seconds
            const freqStart = {chirp_freq_start};
            const freqEnd = {chirp_freq_end};
            const volume = {volume};
            const maxDist = {max_distance}; // cm

            // Hidden button to trigger rerun
            const hiddenBtn = document.querySelector('[data-testid="baseButton-secondary"]');
            if (!hiddenBtn) {{
                console.error("Hidden button not found");
                return;
            }}

            function updateStatus(text) {{
                document.getElementById('status').innerHTML = text;
            }}

            function sendResult(data) {{
                if (resultSent) return;
                resultSent = true;
                // Store data in a global variable for Python to read via hidden button
                window.pulseData = data;
                // Click the hidden button to trigger rerun
                hiddenBtn.click();
            }}

            async function processPulse() {{
                if (isProcessing) return;
                isProcessing = true;
                resultSent = false;
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

                    // 4. Setup recording
                    const recorder = audioContext.createScriptProcessor(4096, 1, 1);
                    let recordedSamples = [];
                    let recordingStartTime = 0;

                    recorder.onaudioprocess = function(e) {{
                        const input = e.inputBuffer.getChannelData(0);
                        const copy = new Float32Array(input);
                        recordedSamples.push(copy);
                    }};

                    mic.connect(recorder);
                    recorder.connect(audioContext.destination);

                    // 5. Play and record
                    updateStatus("🔊 Playing chirp...");
                    source.connect(audioContext.destination);
                    recordingStartTime = audioContext.currentTime;
                    source.start();
                    
                    // Record for 2 seconds
                    const recordDuration = 2; // seconds
                    await new Promise(resolve => {{
                        setTimeout(resolve, recordDuration * 1000 + 500);
                    }});

                    // 6. Stop everything
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

                    // 8. Compute cross-correlation with transmitted signal
                    // Pad transmitted signal to same length
                    const txLen = buffer.length;
                    const rxLen = recorded.length;
                    const maxLen = Math.max(txLen, rxLen);
                    const txPadded = new Float32Array(maxLen);
                    txPadded.set(data, 0);
                    const rxPadded = new Float32Array(maxLen);
                    rxPadded.set(recorded, 0);

                    // FFT-based cross-correlation
                    const fftSize = 4096;
                    const fft = (x) => {{
                        // Simple DFT for demo (use FFT if available, but we'll use manual)
                        // For simplicity, we'll use a sliding dot product (slow but works)
                        // To keep it fast, we'll use a simplified approach: find peaks in envelope.
                        // Actually, we'll use the time-domain cross-correlation via convolution.
                        // For brevity, we'll use a basic sliding window.
                        // We'll compute the envelope of the received signal and look for peaks.
                        // This is a simplified version for demo.
                        const correlations = [];
                        const windowSize = 256;
                        for (let i = 0; i < rxLen - windowSize; i += 10) {{
                            let sum = 0;
                            for (let j = 0; j < windowSize && j < txLen; j++) {{
                                sum += txPadded[j] * rxPadded[i+j];
                            }}
                            correlations.push({{ idx: i, val: Math.abs(sum) }});
                        }}
                        return correlations;
                    }};

                    const corr = [];
                    for (let i = 0; i < rxLen - data.length; i += 5) {{
                        let sum = 0;
                        for (let j = 0; j < data.length; j++) {{
                            sum += data[j] * recorded[i+j];
                        }}
                        corr.push({{ idx: i, val: Math.abs(sum) }});
                    }}

                    // Find the first strong peak after the direct sound (skip the first 0.5 ms)
                    const directSamples = Math.floor(0.0005 * sampleRate);
                    let maxVal = 0;
                    let maxIdx = 0;
                    for (let i = 0; i < corr.length; i++) {{
                        if (corr[i].idx > directSamples && corr[i].val > maxVal) {{
                            maxVal = corr[i].val;
                            maxIdx = corr[i].idx;
                        }}
                    }}

                    const delaySeconds = maxIdx / sampleRate;
                    const distanceCm = delaySeconds * 34300 / 2; // round-trip
                    const estimatedDistance = Math.min(distanceCm, maxDist);

                    // 9. Send results back
                    const resultData = {{
                        distance: estimatedDistance,
                        delay_seconds: delaySeconds,
                        peak_value: maxVal,
                        status: "success"
                    }};
                    sendResult(resultData);

                }} catch (err) {{
                    updateStatus("❌ Error: " + err.message);
                    sendResult({{ status: "error", message: err.message }});
                }} finally {{
                    isProcessing = false;
                }}
            }}

            // Listen for trigger from sidebar (via session state change)
            // We'll use a MutationObserver on a dummy element that we can update from Python.
            // But simpler: we'll expose a function to call from Python via a hidden button? 
            // Actually, we can set a global variable and check periodically.
            // We'll just use the hidden button click to trigger the pulse.
            // We'll detect a click on a special hidden button that we'll create from Python.
            // Better: use a polling mechanism in JavaScript to check a variable set by Python.
            // We'll use a simple method: we'll listen for a custom event from Python.
            // For simplicity, we'll just call processPulse() when the user clicks the "Send Pulse" button in the sidebar.
            // That button will be a Streamlit button that sets a session state variable.
            // To trigger from Python, we'll use a hidden button with a unique ID.
            // The sidebar button will set st.session_state.trigger_pulse = True.
            // The HTML component will periodically check that variable via an API call? Not straightforward.
            
            // Instead, we'll use the hidden button trick: when the user clicks the Streamlit button,
            // we call a JavaScript function via a custom component? Actually, we can use a button with an onclick that calls a Python function via a form.
            // I'll use a simpler method: the sidebar button will set a session state flag,
            // and the HTML component will use a setInterval to check a global variable that we set from Python.
            // Since we can't modify global variable from Python easily, we'll use a hidden input element that we update.
            // I'll add a hidden input in the HTML that we can update via a rerun.
            // For this demo, I'll just use a button in the HTML itself instead of sidebar.

            // We'll add a button in the HTML to trigger the pulse.
            // That way, no need for cross-communication.
            // I'll add a "Send Pulse" button inside the HTML component.
            // The button will call processPulse() on click.
            // The result will be sent via the hidden button trick.

            // So we need to add a button in the HTML.
            const container = document.createElement('div');
            const btn = document.createElement('button');
            btn.innerText = '🔊 Send Pulse (Microphone)';
            btn.className = 'btn';
            btn.onclick = processPulse;
            container.appendChild(btn);
            document.body.prepend(container);

            // Also show status
            const statusDiv = document.getElementById('status');
            // We'll keep the status div.

            // Add a note about allowing microphone access.
            updateStatus("🟡 Click 'Send Pulse' to begin. Allow microphone access when prompted.");
        }})();
        </script>
    </body>
    </html>
    """
    st.components.v1.html(html_code, height=250)

    # Display results if available
    if st.session_state.pulse_result:
        result = st.session_state.pulse_result
        if result.get("status") == "success":
            distance_cm = result.get("distance", 0)
            delay = result.get("delay_seconds", 0)
            st.success(f"✅ Object detected at **{distance_cm:.1f} cm**")
            st.metric("Round-trip Delay", f"{delay*1000:.2f} ms")
            st.info(f"Wall + object distance: ~{distance_cm/2:.1f} cm")
        else:
            st.error(f"❌ Error: {result.get('message', 'Unknown error')}")
        # Clear result after displaying
        st.session_state.pulse_result = None

with col2:
    st.subheader("📊 Detection Parameters")
    st.markdown(f"""
    - **Chirp duration:** {chirp_duration} ms
    - **Frequency range:** {chirp_freq_start} – {chirp_freq_end} Hz
    - **Max distance:** {max_distance} cm
    - **Sound speed:** {SOUND_SPEED*34300:.0f} m/s
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
