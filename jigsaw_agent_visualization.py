"""Animated ecosystem view for the Jigsaw strategy simulation."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from jigsaw_strategy_model import Params


SPECIALIST = (0.14, 0.50)
PARTNER = (0.50, 0.50)
IMITATORS = ((0.09, 0.80), (0.20, 0.84), (0.28, 0.73))
MARKETS = (
    (0.75, 0.76),
    (0.86, 0.81),
    (0.94, 0.68),
    (0.79, 0.55),
    (0.93, 0.45),
    (0.85, 0.29),
    (0.73, 0.34),
)


@dataclass(frozen=True)
class AgentSnapshot:
    """Visual state derived from a single simulation month."""

    month: int
    phase: int
    status: str
    specialist_size: float
    partner_size: float
    relationship_width: float
    relationship_opacity: float
    imitation_strength: float
    market_activity: float
    value_flow_strength: float


def _bounded(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def snapshot_for(row: pd.Series, params: Params) -> AgentSnapshot:
    """Translate model scores into bounded visual properties."""
    expertise = float(row["Expertise depth"]) / 100
    recognition = float(row["Partner recognition"]) / 100
    trust = float(row["Trust"]) / 100
    integration = float(row["Integration"]) / 100
    rarity_loss = 1.0 - float(row["Rarity"]) / 100
    commoditisation = float(row["Commoditisation risk"]) / 100
    adoption = float(row["Market adoption"]) / 100
    realised_synergy = float(row["Realised synergy"]) / 100

    return AgentSnapshot(
        month=int(row["Month"]),
        phase=int(row["Phase"]),
        status=str(row["Status"]),
        specialist_size=30 + 26 * expertise,
        partner_size=40 + 22 * params.partner_reach,
        relationship_width=1 + 7 * integration,
        relationship_opacity=_bounded(0.18 + 0.42 * recognition + 0.40 * trust),
        imitation_strength=_bounded(
            0.15 * params.imitation_pressure * 12.5
            + 0.45 * rarity_loss
            + 0.40 * commoditisation
        ),
        market_activity=_bounded(adoption),
        value_flow_strength=_bounded(0.35 * recognition + 0.65 * realised_synergy),
    )


def _rgba(hex_colour: str, opacity: float) -> str:
    hex_colour = hex_colour.lstrip("#")
    red, green, blue = (
        int(hex_colour[index : index + 2], 16) for index in (0, 2, 4)
    )
    return f"rgba({red},{green},{blue},{_bounded(opacity):.3f})"


def _segments(origin: tuple[float, float], destinations: tuple[tuple[float, float], ...]):
    x_values: list[float | None] = []
    y_values: list[float | None] = []
    for destination in destinations:
        x_values.extend((origin[0], destination[0], None))
        y_values.extend((origin[1], destination[1], None))
    return x_values, y_values


def _flow_points(
    origin: tuple[float, float],
    destination: tuple[float, float],
    month: int,
    count: int,
    phase_offset: float = 0.0,
) -> tuple[list[float], list[float]]:
    x_values: list[float] = []
    y_values: list[float] = []
    for index in range(count):
        progress = ((month / 7) + phase_offset + index / count) % 1.0
        x_values.append(origin[0] + (destination[0] - origin[0]) * progress)
        y_values.append(origin[1] + (destination[1] - origin[1]) * progress)
    return x_values, y_values


def _market_opacities(activity: float) -> list[float]:
    thresholds = [index / len(MARKETS) for index in range(len(MARKETS))]
    return [
        0.16 + 0.84 * _bounded((activity - threshold) * len(MARKETS))
        for threshold in thresholds
    ]


def _frame_traces(row: pd.Series, params: Params) -> list[go.Scatter]:
    state = snapshot_for(row, params)
    recognition = float(row["Partner recognition"])
    trust = float(row["Trust"])
    integration = float(row["Integration"])
    realised_synergy = float(row["Realised synergy"])
    adoption = float(row["Market adoption"])
    rarity = float(row["Rarity"])
    shaping_power = float(row["Shaping power"])
    local_strength = float(row["Local strength"])
    commoditisation = float(row["Commoditisation risk"])
    phase_label = str(row["Phase name"]).split(" ", 1)[-1]

    market_x, market_y = _segments(PARTNER, MARKETS)
    imitation_x, imitation_y = _segments(SPECIALIST, IMITATORS)

    capability_x, capability_y = _flow_points(
        SPECIALIST, PARTNER, state.month, count=3
    )
    market_flow_x: list[float] = []
    market_flow_y: list[float] = []
    for index, market in enumerate(MARKETS[:4]):
        point_x, point_y = _flow_points(
            PARTNER, market, state.month, count=1, phase_offset=index / 4
        )
        market_flow_x.extend(point_x)
        market_flow_y.extend(point_y)

    relationship_colour = _rgba("#B279A2", state.relationship_opacity)
    market_colour = _rgba("#54A24B", 0.14 + 0.70 * state.market_activity)
    imitation_colour = _rgba("#E45756", 0.10 + 0.72 * state.imitation_strength)

    return [
        go.Scatter(
            x=[SPECIALIST[0], PARTNER[0]],
            y=[SPECIALIST[1], PARTNER[1]],
            mode="lines",
            line={"color": relationship_colour, "width": state.relationship_width},
            hoverinfo="skip",
            showlegend=False,
        ),
        go.Scatter(
            x=market_x,
            y=market_y,
            mode="lines",
            line={
                "color": market_colour,
                "width": 0.8 + 5.2 * state.value_flow_strength,
            },
            hoverinfo="skip",
            showlegend=False,
        ),
        go.Scatter(
            x=imitation_x,
            y=imitation_y,
            mode="lines",
            line={
                "color": imitation_colour,
                "width": 0.7 + 4.0 * state.imitation_strength,
            },
            hoverinfo="skip",
            showlegend=False,
        ),
        go.Scatter(
            x=capability_x,
            y=capability_y,
            mode="markers",
            marker={
                "color": relationship_colour,
                "size": 5 + 10 * state.value_flow_strength,
                "symbol": "diamond",
            },
            hovertemplate="Capability exchange<extra></extra>",
            showlegend=False,
        ),
        go.Scatter(
            x=market_flow_x,
            y=market_flow_y,
            mode="markers",
            marker={
                "color": market_colour,
                "size": 4 + 12 * state.market_activity,
            },
            hovertemplate="Value reaching the market<extra></extra>",
            showlegend=False,
        ),
        go.Scatter(
            x=[SPECIALIST[0]],
            y=[SPECIALIST[1]],
            mode="markers+text",
            text=["Specialist"],
            textposition="bottom center",
            marker={
                "color": "#4C78A8",
                "size": state.specialist_size,
                "symbol": "diamond",
                "line": {"color": "#2D4E72", "width": 2 + 5 * rarity / 100},
            },
            customdata=[[float(row["Expertise depth"]), rarity, local_strength, shaping_power]],
            hovertemplate=(
                "<b>Specialist</b><br>Expertise: %{customdata[0]:.1f}"
                "<br>Rarity: %{customdata[1]:.1f}"
                "<br>Local strength: %{customdata[2]:.1f}"
                "<br>Shaping power: %{customdata[3]:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=[PARTNER[0]],
            y=[PARTNER[1]],
            mode="markers+text",
            text=["Partner"],
            textposition="bottom center",
            marker={
                "color": "#F58518",
                "size": state.partner_size,
                "symbol": "square",
                "line": {"color": "#A65A0A", "width": 2},
            },
            customdata=[[recognition, trust, integration, params.partner_reach * 100]],
            hovertemplate=(
                "<b>Partner</b><br>Recognition: %{customdata[0]:.1f}"
                "<br>Trust: %{customdata[1]:.1f}"
                "<br>Integration: %{customdata[2]:.1f}"
                "<br>Reach: %{customdata[3]:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=[point[0] for point in IMITATORS],
            y=[point[1] for point in IMITATORS],
            mode="markers+text",
            text=["Imitators", "", ""],
            textposition="top center",
            marker={
                "color": imitation_colour,
                "size": [14 + state.imitation_strength * (8 + 3 * index) for index in range(3)],
                "symbol": "triangle-down",
                "line": {"color": "#A23B3A", "width": 1},
            },
            customdata=[
                [commoditisation, 100 - rarity, params.imitation_pressure * 100]
                for _ in IMITATORS
            ],
            hovertemplate=(
                "<b>Imitator</b><br>Commoditisation risk: %{customdata[0]:.1f}"
                "<br>Rarity lost: %{customdata[1]:.1f}"
                "<br>Imitation pressure: %{customdata[2]:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=[point[0] for point in MARKETS],
            y=[point[1] for point in MARKETS],
            mode="markers+text",
            text=["Market agents", "", "", "", "", "", ""],
            textposition="top center",
            marker={
                "color": [
                    _rgba("#54A24B", opacity)
                    for opacity in _market_opacities(state.market_activity)
                ],
                "size": [17 + 5 * opacity for opacity in _market_opacities(state.market_activity)],
                "line": {"color": "#327333", "width": 1},
            },
            customdata=[
                [adoption, realised_synergy, params.market_demand * 100]
                for _ in MARKETS
            ],
            hovertemplate=(
                "<b>Market agent</b><br>Adoption: %{customdata[0]:.1f}"
                "<br>Realised synergy: %{customdata[1]:.1f}"
                "<br>Market demand: %{customdata[2]:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=[0.5],
            y=[0.96],
            mode="text",
            text=[
                f"<b>Month {state.month} · Phase {state.phase}</b> — "
                f"{phase_label}<br>{state.status}"
            ],
            textposition="middle center",
            hoverinfo="skip",
            showlegend=False,
        ),
    ]


def make_agent_simulation_chart(
    df: pd.DataFrame, params: Params, frame_duration: int = 180
) -> go.Figure:
    """Build a playable Plotly animation from simulation output."""
    frames = [
        go.Frame(
            data=_frame_traces(row, params),
            name=str(int(row["Month"])),
        )
        for _, row in df.iterrows()
    ]
    figure = go.Figure(data=frames[0].data, frames=frames)

    slider_steps = []
    last_month = int(df.iloc[-1]["Month"])
    for month in df["Month"].astype(int):
        slider_steps.append(
            {
                "args": [
                    [str(month)],
                    {
                        "frame": {"duration": 0, "redraw": True},
                        "mode": "immediate",
                        "transition": {"duration": 0},
                    },
                ],
                "label": str(month) if month % 12 == 0 or month == last_month else "",
                "method": "animate",
            }
        )

    figure.update_layout(
        height=590,
        margin={"l": 10, "r": 10, "t": 20, "b": 110},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel={"namelength": -1},
        xaxis={"range": [0, 1.02], "visible": False, "fixedrange": True},
        yaxis={"range": [0.08, 1.02], "visible": False, "fixedrange": True},
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "showactive": False,
                "x": 0,
                "y": -0.09,
                "xanchor": "left",
                "yanchor": "top",
                "buttons": [
                    {
                        "label": "▶ Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {
                                    "duration": frame_duration,
                                    "redraw": True,
                                },
                                "fromcurrent": True,
                                "mode": "immediate",
                                "transition": {
                                    "duration": min(80, frame_duration // 2)
                                },
                            },
                        ],
                    },
                    {
                        "label": "Ⅱ Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": 0,
                "currentvalue": {"visible": False},
                "pad": {"t": 35},
                "x": 0.22,
                "len": 0.77,
                "steps": slider_steps,
            }
        ],
    )
    return figure
