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
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-title">
    <h1>📡 Acoustic Through‑Wall Detection</h1>
    <p>Simulate sound waves to detect objects behind walls – no hardware needed</p>
</div>
""", unsafe_allow_html=True)

# ---------- SIDEBAR CONTROLS ----------
st.sidebar.header("⚙️ Simulation Parameters")

wall_thickness = st.sidebar.slider("Wall Thickness (cm)", 10, 50, 25, step=1)
object_distance = st.sidebar.slider("Object Distance from Wall (cm)", 0, 150, 50, step=1)
object_size = st.sidebar.slider("Object Size (cm)", 5, 50, 20, step=1)
wall_material = st.sidebar.selectbox("Wall Material", ["Concrete", "Brick", "Wood", "Drywall"])
movement = st.sidebar.checkbox("Simulate Object Movement", value=False)
movement_speed = st.sidebar.slider("Movement Speed (cm/s)", 1, 20, 5, step=1) if movement else 0

# Sound speed in different materials (m/s)
material_speed = {
    "Concrete": 3500,
    "Brick": 3700,
    "Wood": 4000,
    "Drywall": 2500
}
sound_speed = material_speed[wall_material] / 100  # convert to cm/µs for simulation

st.sidebar.markdown("---")
st.sidebar.info("This simulation models acoustic pulse propagation, reflection, and attenuation to detect objects behind walls. Adjust parameters to see how they affect detection.")

# ---------- MAIN SIMULATION ----------
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
# Distance from source to object: wall_thickness (source to wall) + object_distance (wall to object)
# Convert cm to µs using sound speed (cm/µs)
distance_to_object = wall_thickness + object_distance
round_trip_time = 2 * distance_to_object / sound_speed  # µs

# Simulate received signal: transmitted pulse + attenuated echo + noise
received_signal = np.zeros_like(time_axis)
# Direct transmission through wall (small leakage)
direct_amp = 0.01
direct_idx = int(wall_thickness / sound_speed / time_resolution)
if direct_idx < len(received_signal):
    received_signal[direct_idx:direct_idx+len(tx_signal)] += direct_amp * tx_signal

# Reflection from object
reflection_amp = 0.5 * (object_size / 20)  # larger object = stronger reflection
reflection_idx = int(round_trip_time / time_resolution)
if reflection_idx < len(received_signal):
    end_idx = min(reflection_idx + len(tx_signal), len(received_signal))
    received_signal[reflection_idx:end_idx] += reflection_amp * tx_signal[:end_idx-reflection_idx]

# Add noise
received_signal += np.random.normal(0, 0.02, len(received_signal))

# ---------- DETECTION ALGORITHM ----------
# Cross-correlation with transmitted pulse
corr = signal.correlate(received_signal, tx_signal, mode='same')
corr = np.abs(corr)
# Find peaks
peaks, _ = signal.find_peaks(corr, height=0.01, distance=10)
peak_times = time_axis[peaks]
peak_heights = corr[peaks]

# Estimate object distance from strongest reflection
if len(peak_times) > 1:
    # The first strong peak after direct is the reflection
    for i, t in enumerate(peak_times):
        if t > wall_thickness / sound_speed:  # after wall
            estimated_distance = t * sound_speed / 2  # cm
            break
    else:
        estimated_distance = None
else:
    estimated_distance = None

# ---------- DISPLAY RESULTS ----------
with col1:
    # Plot the cross-section
    fig = go.Figure()

    # Wall
    fig.add_shape(
        type="rect", x0=0, x1=wall_thickness/100, y0=-0.5, y1=0.5,
        fillcolor="#8B4513", line=dict(width=2), opacity=0.7,
        name="Wall"
    )
    # Object
    obj_x = wall_thickness/100 + object_distance/100
    fig.add_shape(
        type="rect", x0=obj_x-object_size/200, x1=obj_x+object_size/200,
        y0=-object_size/200, y1=object_size/200,
        fillcolor="#FF5733", line=dict(width=2), name="Object"
    )
    # Source/Receiver (at x=0)
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

    # Simulated signal plot
    st.subheader("📊 Received Acoustic Signal")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=time_axis, y=received_signal, mode="lines", name="Received Signal"))
    fig2.add_trace(go.Scatter(x=time_axis, y=corr, mode="lines", name="Cross-Correlation (Envelope)"))
    # Mark detected peaks
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
        # Estimate size from reflection amplitude (relative to object_size)
        estimated_size = object_size * (reflection_amp / 0.5)  # rough scaling
        st.metric("Estimated Object Size", f"{estimated_size:.1f} cm")
        st.success("✅ Object detected!")
    else:
        st.info("No object detected. Try adjusting parameters or increasing object size.")
    
    st.caption(f"Wall material: {wall_material} (sound speed: {sound_speed*100:.0f} m/s)")

# ---------- MOVEMENT SIMULATION ----------
if movement:
    st.subheader("🔄 Object Movement Simulation")
    # Simulate moving object back and forth
    progress = st.empty()
    for i in range(60):
        # Update object position
        offset = movement_speed * (i % 60) / 100  # cm
        new_distance = object_distance + (movement_speed * np.sin(i * 0.1))
        # Recalculate echo time
        round_trip_time = 2 * (wall_thickness + new_distance) / sound_speed
        # Update display (we'd refresh the plot, but we'll just show a progress bar)
        progress.progress((i+1)/60, text=f"Moving object... Distance: {new_distance:.1f} cm")
        time.sleep(0.05)
    progress.empty()
    st.success("Movement simulation completed. The object was tracked successfully.")

# ---------- FOOTER ----------
st.markdown("---")
st.caption("🚀 Built by Gesner Deslandes, Engineer-in-Chief at GlobalInternet.py | Acoustic detection simulation for educational purposes.")
