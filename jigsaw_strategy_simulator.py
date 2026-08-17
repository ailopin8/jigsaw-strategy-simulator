"""Interactive learning model of the Jigsaw strategy from Patterns of Strategy."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from jigsaw_agent_visualization import make_agent_simulation_chart
from jigsaw_strategy_model import PHASES, Params, insight_for, phase_bands, simulate


def make_trajectory_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    series = [
        ("Expertise depth", "#4C78A8"),
        ("Partner recognition", "#F58518"),
        ("Realised synergy", "#54A24B"),
        ("Shaping power", "#B279A2"),
        ("Commoditisation risk", "#E45756"),
    ]
    for name, colour in series:
        fig.add_trace(
            go.Scatter(
                x=df["Month"],
                y=df[name],
                mode="lines",
                name=name,
                line={
                    "width": 3 if name in {"Realised synergy", "Shaping power"} else 2,
                    "color": colour,
                },
                hovertemplate=f"Month %{{x}}<br>{name}: %{{y:.1f}}<extra></extra>",
            )
        )
    fig.update_layout(
        height=430,
        margin={"l": 45, "r": 15, "t": 25, "b": 45},
        xaxis_title="Time (months)",
        yaxis_title="Score (0–100)",
        yaxis={"range": [0, 100]},
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.12, "x": 0},
    )
    return fig


def make_phase_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for start, end, phase in phase_bands(df):
        fig.add_trace(
            go.Bar(
                x=[end - start + 1],
                y=["Jigsaw progression"],
                base=[start],
                orientation="h",
                name=PHASES[phase],
                text=[f"Phase {phase}"],
                textposition="inside",
                hovertemplate=(
                    f"{PHASES[phase]}<br>Months {start}–{end}<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        barmode="stack",
        height=150,
        showlegend=False,
        margin={"l": 10, "r": 15, "t": 5, "b": 35},
        xaxis_title="Time (months)",
        yaxis={"showticklabels": False},
    )
    return fig


def slider(label: str, minimum: int, maximum: int, value: int, help_text: str) -> float:
    return st.slider(label, minimum, maximum, value, help=help_text) / 100.0


st.set_page_config(page_title="Jigsaw Strategy Simulator", layout="wide")
st.title("Jigsaw Strategy Simulator")
st.caption(
    "A learning model of how concentrated specialist capability becomes "
    "collaborative leverage over time."
)

with st.sidebar:
    st.header("Scenario controls")
    preset = st.selectbox(
        "Starting scenario",
        ["Promising specialist", "Hidden gem", "Easy to copy", "Poor fit"],
    )
    presets = {
        "Promising specialist": {
            "focus": 78,
            "expertise": 35,
            "rarity": 82,
            "complementarity": 80,
            "openness": 65,
            "friction": 25,
        },
        "Hidden gem": {
            "focus": 90,
            "expertise": 52,
            "rarity": 91,
            "complementarity": 86,
            "openness": 28,
            "friction": 35,
        },
        "Easy to copy": {
            "focus": 72,
            "expertise": 38,
            "rarity": 48,
            "complementarity": 78,
            "openness": 70,
            "friction": 20,
        },
        "Poor fit": {
            "focus": 70,
            "expertise": 48,
            "rarity": 80,
            "complementarity": 28,
            "openness": 35,
            "friction": 65,
        },
    }
    selected_preset = presets[preset]
    months = st.slider("Simulation length (months)", 24, 120, 72, 12)
    focus = slider(
        "Capability concentration",
        10,
        100,
        selected_preset["focus"],
        "How much effort is focused on one specialism.",
    )
    initial_expertise = slider(
        "Initial expertise depth",
        5,
        95,
        selected_preset["expertise"],
        "Starting mastery of the narrow capability.",
    )
    learning_rate = (
        slider(
            "Learning rate",
            1,
            10,
            5,
            "Speed at which focused practice deepens expertise.",
        )
        * 0.9
    )
    innovation_rate = slider(
        "Renewal / innovation",
        0,
        8,
        3,
        "How quickly the specialist renews the capability to preserve rarity.",
    )
    initial_rarity = slider(
        "Initial scarcity",
        5,
        100,
        selected_preset["rarity"],
        "How difficult the specialist capability is to find or copy.",
    )
    imitation_pressure = slider(
        "Imitation pressure",
        0,
        8,
        2,
        "How quickly alternatives copy or substitute the specialism.",
    )
    complementarity = slider(
        "Partner complementarity",
        0,
        100,
        selected_preset["complementarity"],
        "How strongly the specialist capability complements the partner.",
    )
    partner_reach = slider(
        "Partner reach / platform",
        10,
        100,
        82,
        "Scale of customers, assets, distribution or legitimacy supplied by the partner.",
    )
    partner_openness = slider(
        "Partner openness",
        0,
        100,
        selected_preset["openness"],
        "Willingness to recognise and use outside expertise.",
    )
    initial_trust = slider(
        "Initial trust",
        0,
        80,
        18,
        "Trust present before collaboration begins.",
    )
    reliability = slider(
        "Delivery reliability",
        20,
        100,
        78,
        "Consistency with which the specialist delivers useful work.",
    )
    integration_effort = slider(
        "Integration effort",
        0,
        100,
        48,
        "Effort devoted to aligning interfaces and processes.",
    )
    friction = slider(
        "Coordination friction",
        0,
        100,
        selected_preset["friction"],
        "Cultural, technical and governance difficulty in working together.",
    )
    demand = slider(
        "Market demand",
        10,
        100,
        72,
        "Demand for the combined value proposition.",
    )

params = Params(
    months=months,
    focus=focus,
    initial_expertise=initial_expertise,
    learning_rate=learning_rate,
    innovation_rate=innovation_rate,
    initial_rarity=initial_rarity,
    imitation_pressure=imitation_pressure,
    complementarity=complementarity,
    partner_reach=partner_reach,
    partner_openness=partner_openness,
    initial_trust=initial_trust,
    delivery_reliability=reliability,
    integration_effort=integration_effort,
    coordination_friction=friction,
    market_demand=demand,
)
df = simulate(params)

st.subheader("Animated agent ecosystem")
st.caption(
    "Press Play to watch capability, recognition, imitation and market adoption "
    "develop. Drag the chart timeline to inspect any month."
)
playback_speed = st.segmented_control(
    "Playback speed",
    options=["Slow", "Normal", "Fast"],
    default="Normal",
)
frame_duration = {"Slow": 320, "Normal": 180, "Fast": 90}[playback_speed or "Normal"]
st.plotly_chart(
    make_agent_simulation_chart(df, params, frame_duration=frame_duration),
    use_container_width=True,
    config={"displayModeBar": False},
)
st.caption(
    "Agents move because of the model: trust draws the specialist and partner "
    "together, copying draws imitators inward, and adoption draws market agents "
    "toward the joint offer. Blue arrows carry capability, orange arrows return "
    "resources and recognition, green arrows deliver value, gold arrows return "
    "demand, and red arrows show copying. The red field is effective friction."
)

st.divider()
st.subheader("Inspect the strategy")
selected_month = st.slider("Inspect month", 0, months, months)
current = df.iloc[selected_month]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Current phase", f"{int(current['Phase'])} of 6", current["Status"])
c2.metric("Realised synergy", f"{current['Realised synergy']:.0f}/100")
c3.metric("Local shaping power", f"{current['Shaping power']:.0f}/100")
c4.metric(
    "Commoditisation risk", f"{current['Commoditisation risk']:.0f}/100"
)

st.info(f"**{current['Phase name']}** — {insight_for(current)}")
st.plotly_chart(make_phase_chart(df), use_container_width=True)
st.plotly_chart(make_trajectory_chart(df), use_container_width=True)

left, right = st.columns([1.2, 1])
with left:
    st.subheader("State at inspected month")
    state = pd.DataFrame(
        {
            "Principle": [
                "Concentration",
                "Local strength",
                "Recognition",
                "Co-evolution",
                "Synchronisation",
                "Renewal",
            ],
            "Observable score": [
                focus * 100,
                current["Local strength"],
                current["Partner recognition"],
                current["Trust"],
                current["Integration"],
                current["Rarity"],
            ],
        }
    )
    st.dataframe(
        state.style.format({"Observable score": "{:.1f}"}),
        hide_index=True,
        use_container_width=True,
    )

with right:
    st.subheader("What to experiment with")
    st.markdown(
        "- Lower **scarcity** or raise **imitation pressure** to see commoditisation.\n"
        "- Raise **expertise concentration** while keeping overall size unchanged to see local strength.\n"
        "- Lower **partner complementarity** to see why expertise alone is insufficient.\n"
        "- Raise **coordination friction** to separate potential synergy from realised synergy.\n"
        "- Raise **renewal** to see how the Jigsaw maintains differentiation after success."
    )

with st.expander("Model logic and limitations"):
    st.markdown(
        "This is a deterministic learning model, not a forecast. It represents the "
        "book's logic: focused expertise and rarity create local critical mass; "
        "complementarity and openness create recognition; reliable delivery builds "
        "trust; trust plus integration turns potential synergy into realised value; "
        "and imitation erodes differentiation unless innovation renews it. All scores "
        "are dimensionless 0–100 indices."
    )
