import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Humanitarian Aid Targeting Simulation Dashboard")

st.markdown("Simulating IPC Food Security Dynamics and Aid Targeting Strategies")

# -----------------------------
# SIDEBAR CONTROLS
# -----------------------------

st.sidebar.header("Simulation Parameters")

NUM_HOUSEHOLDS = st.sidebar.slider("Number of Households", 1000, 10000, 5000)
AID_PERCENT = st.sidebar.slider("Aid Capacity (% of population)", 5, 50, 20)
SHOCK_2_TO_3 = st.sidebar.slider("Shock: Phase 2 → 3 Probability", 0.0, 1.0, 0.3)
SHOCK_3_TO_4 = st.sidebar.slider("Shock: Phase 3 → 4 Probability", 0.0, 1.0, 0.2)

STEPS = st.sidebar.slider("Simulation Steps", 5, 50, 20)

strategy = st.sidebar.selectbox(
    "Select Aid Strategy",
    ["Equal Distribution", "Target Phase 4", "Early Intervention (Phase 2)"]
)

# -----------------------------
# INITIALIZE HOUSEHOLDS
# -----------------------------

phases = [1, 2, 3, 4]
probs = [0.25, 0.30, 0.30, 0.15]  # default baseline distribution

households = pd.DataFrame({
    "id": range(NUM_HOUSEHOLDS),
    "phase": np.random.choice(phases, size=NUM_HOUSEHOLDS, p=probs)
})

AID_CAPACITY = int((AID_PERCENT / 100) * NUM_HOUSEHOLDS)

# -----------------------------
# DYNAMICS FUNCTIONS
# -----------------------------

def apply_shock(df):
    for i in df.index:
        phase = df.loc[i, "phase"]

        if phase == 2 and np.random.rand() < SHOCK_2_TO_3:
            df.loc[i, "phase"] = 3
        elif phase == 3 and np.random.rand() < SHOCK_3_TO_4:
            df.loc[i, "phase"] = 4
    return df


def apply_recovery(df):
    for i in df.index:
        if df.loc[i, "received_aid"]:
            phase = df.loc[i, "phase"]

            if phase == 4 and np.random.rand() < 0.6:
                df.loc[i, "phase"] = 3
            elif phase == 3 and np.random.rand() < 0.5:
                df.loc[i, "phase"] = 2
            elif phase == 2 and np.random.rand() < 0.4:
                df.loc[i, "phase"] = 1
    return df


def distribute_aid(df):
    df["received_aid"] = False

    if strategy == "Equal Distribution":
        selected = df.sample(AID_CAPACITY).index

    elif strategy == "Target Phase 4":
        phase4 = df[df["phase"] == 4]
        if len(phase4) >= AID_CAPACITY:
            selected = phase4.sample(AID_CAPACITY).index
        else:
            remaining = AID_CAPACITY - len(phase4)
            others = df.drop(phase4.index)
            selected = list(phase4.index) + list(others.sample(remaining).index)

    elif strategy == "Early Intervention (Phase 2)":
        phase2 = df[df["phase"] == 2]
        if len(phase2) >= AID_CAPACITY:
            selected = phase2.sample(AID_CAPACITY).index
        else:
            remaining = AID_CAPACITY - len(phase2)
            others = df.drop(phase2.index)
            selected = list(phase2.index) + list(others.sample(remaining).index)

    df.loc[selected, "received_aid"] = True
    return df


# -----------------------------
# RUN SIMULATION BUTTON
# -----------------------------

if st.button("Run Simulation"):

    sim_df = households.copy()
    phase3plus_history = []

    for step in range(STEPS):
        sim_df = apply_shock(sim_df)
        sim_df = distribute_aid(sim_df)
        sim_df = apply_recovery(sim_df)

        phase3plus = len(sim_df[sim_df["phase"] >= 3])
        phase3plus_history.append(phase3plus / NUM_HOUSEHOLDS)

    # -----------------------------
    # DISPLAY RESULTS
    # -----------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Phase Distribution (Final Step)")
        final_counts = sim_df["phase"].value_counts().sort_index()
        st.bar_chart(final_counts)

    with col2:
        st.subheader("Phase 3+ Trend Over Time")
        st.line_chart(phase3plus_history)

    st.metric(
        "Final Percentage in Phase 3+",
        f"{round(phase3plus_history[-1] * 100, 2)}%"
    )
