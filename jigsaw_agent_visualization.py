"""Animated ecosystem view for the Jigsaw strategy simulation."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from jigsaw_strategy_model import Params


SPECIALIST_BASE = (0.18, 0.50)
PARTNER_BASE = (0.51, 0.50)
IMITATOR_BASES = ((0.07, 0.80), (0.18, 0.86), (0.29, 0.75))
MARKET_BASES = (
    (0.75, 0.76),
    (0.86, 0.82),
    (0.95, 0.68),
    (0.80, 0.55),
    (0.94, 0.44),
    (0.85, 0.27),
    (0.73, 0.33),
)


@dataclass(frozen=True)
class AgentSnapshot:
    """Visual state derived from a single simulation month."""

    month: int
    phase: int
    status: str
    specialist_position: tuple[float, float]
    partner_position: tuple[float, float]
    imitator_positions: tuple[tuple[float, float], ...]
    market_positions: tuple[tuple[float, float], ...]
    specialist_size: float
    partner_size: float
    relationship_width: float
    relationship_opacity: float
    recognition_strength: float
    resource_flow_strength: float
    imitation_strength: float
    market_activity: float
    value_flow_strength: float
    demand_feedback_strength: float
    friction_strength: float
    rarity_strength: float
    fit_alignment: float
    assembly_progress: float
    picture_completion: float


def _bounded(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _towards(
    origin: tuple[float, float], destination: tuple[float, float], amount: float
) -> tuple[float, float]:
    return (
        origin[0] + (destination[0] - origin[0]) * amount,
        origin[1] + (destination[1] - origin[1]) * amount,
    )


def snapshot_for(row: pd.Series, params: Params) -> AgentSnapshot:
    """Translate model scores into bounded visual properties and agent motion."""
    month = int(row["Month"])
    expertise = float(row["Expertise depth"]) / 100
    recognition = float(row["Partner recognition"]) / 100
    trust = float(row["Trust"]) / 100
    integration = float(row["Integration"]) / 100
    rarity = float(row["Rarity"]) / 100
    rarity_loss = 1.0 - rarity
    commoditisation = float(row["Commoditisation risk"]) / 100
    adoption = float(row["Market adoption"]) / 100
    realised_synergy = float(row["Realised synergy"]) / 100

    effective_friction = _bounded(
        params.coordination_friction
        * (1.0 - 0.72 * integration)
        * (1.0 - 0.22 * trust)
    )
    fit_alignment = _bounded(
        params.complementarity * (1.0 - 0.78 * effective_friction)
    )
    assembly_progress = _bounded(
        (0.26 * recognition + 0.32 * trust + 0.42 * integration)
        * 1.45
        * params.complementarity
    )
    picture_completion = _bounded(
        0.34 * integration + 0.36 * realised_synergy + 0.30 * adoption
    )

    vertical_misalignment = 0.065 * (1.0 - fit_alignment)
    specialist_position = (
        SPECIALIST_BASE[0] + 0.025 * recognition,
        SPECIALIST_BASE[1]
        + vertical_misalignment
        + 0.003 * math.sin(month * 0.48),
    )
    separated_partner = (
        PARTNER_BASE[0],
        PARTNER_BASE[1]
        - vertical_misalignment
        - 0.003 * math.sin(month * 0.39),
    )
    interlocked_partner = (
        specialist_position[0] + 0.153,
        specialist_position[1],
    )
    partner_position = (
        _towards(separated_partner, interlocked_partner, assembly_progress)[0],
        _towards(separated_partner, interlocked_partner, assembly_progress)[1],
    )

    imitation_strength = _bounded(
        0.15 * params.imitation_pressure * 12.5
        + 0.45 * rarity_loss
        + 0.40 * commoditisation
    )
    imitator_positions = tuple(
        (
            _towards(base, specialist_position, 0.34 * imitation_strength)[0]
            + 0.009 * math.sin(month * 0.42 + index * 2.1),
            _towards(base, specialist_position, 0.34 * imitation_strength)[1]
            + 0.007 * math.cos(month * 0.38 + index * 1.7),
        )
        for index, base in enumerate(IMITATOR_BASES)
    )

    market_positions: list[tuple[float, float]] = []
    for index, base in enumerate(MARKET_BASES):
        threshold = index / len(MARKET_BASES)
        activation = _bounded((adoption - threshold) * len(MARKET_BASES))
        approach = 0.12 * adoption * (0.35 + 0.65 * activation)
        approached = _towards(base, partner_position, approach)
        market_positions.append(
            (
                approached[0] + 0.005 * math.sin(month * 0.36 + index),
                approached[1] + 0.007 * math.cos(month * 0.31 + index * 1.3),
            )
        )

    return AgentSnapshot(
        month=month,
        phase=int(row["Phase"]),
        status=str(row["Status"]),
        specialist_position=specialist_position,
        partner_position=partner_position,
        imitator_positions=imitator_positions,
        market_positions=tuple(market_positions),
        specialist_size=30 + 26 * expertise,
        partner_size=40 + 22 * params.partner_reach,
        relationship_width=1 + 7 * (0.45 * trust + 0.55 * integration),
        relationship_opacity=_bounded(0.16 + 0.40 * recognition + 0.44 * trust),
        recognition_strength=_bounded(recognition),
        resource_flow_strength=_bounded(recognition * (0.35 + 0.65 * trust)),
        imitation_strength=imitation_strength,
        market_activity=_bounded(adoption),
        value_flow_strength=_bounded(0.25 * recognition + 0.75 * realised_synergy),
        demand_feedback_strength=_bounded(adoption * params.market_demand),
        friction_strength=effective_friction,
        rarity_strength=_bounded(rarity),
        fit_alignment=fit_alignment,
        assembly_progress=assembly_progress,
        picture_completion=picture_completion,
    )


def _rgba(hex_colour: str, opacity: float) -> str:
    hex_colour = hex_colour.lstrip("#")
    red, green, blue = (
        int(hex_colour[index : index + 2], 16) for index in (0, 2, 4)
    )
    return f"rgba({red},{green},{blue},{_bounded(opacity):.3f})"


def _puzzle_piece_points(
    centre: tuple[float, float],
    half_width: float,
    half_height: float,
    joining_edge: str,
    tab_depth: float,
) -> tuple[list[float], list[float]]:
    """Return an angular jigsaw-piece outline with a tab or matching slot."""
    centre_x, centre_y = centre
    left = centre_x - half_width
    right = centre_x + half_width
    top = centre_y + half_height
    bottom = centre_y - half_height

    points: list[tuple[float, float]] = [
        (left, top),
        (centre_x - 0.34 * half_width, top),
        (centre_x - 0.24 * half_width, top + 0.45 * tab_depth),
        (centre_x, top + 0.72 * tab_depth),
        (centre_x + 0.24 * half_width, top + 0.45 * tab_depth),
        (centre_x + 0.34 * half_width, top),
        (right, top),
    ]

    if joining_edge == "tab-right":
        points.extend(
            [
                (right, centre_y + 0.34 * half_height),
                (right + 0.55 * tab_depth, centre_y + 0.25 * half_height),
                (right + tab_depth, centre_y),
                (right + 0.55 * tab_depth, centre_y - 0.25 * half_height),
                (right, centre_y - 0.34 * half_height),
            ]
        )
    else:
        points.extend([(right, bottom)])

    points.extend([(right, bottom), (left, bottom)])

    if joining_edge == "slot-left":
        points.extend(
            [
                (left, centre_y - 0.34 * half_height),
                (left + 0.55 * tab_depth, centre_y - 0.25 * half_height),
                (left + tab_depth, centre_y),
                (left + 0.55 * tab_depth, centre_y + 0.25 * half_height),
                (left, centre_y + 0.34 * half_height),
            ]
        )

    points.append((left, top))
    return [point[0] for point in points], [point[1] for point in points]


def _joined_puzzle_pieces(
    centres: tuple[tuple[float, float], ...],
    half_width: float,
    half_height: float,
    tab_depth: float,
) -> tuple[list[float | None], list[float | None]]:
    x_values: list[float | None] = []
    y_values: list[float | None] = []
    for centre in centres:
        piece_x, piece_y = _puzzle_piece_points(
            centre, half_width, half_height, "tab-right", tab_depth
        )
        x_values.extend([*piece_x, None])
        y_values.extend([*piece_y, None])
    return x_values, y_values


def _segments(
    origin: tuple[float, float], destinations: tuple[tuple[float, float], ...]
) -> tuple[list[float | None], list[float | None]]:
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
        progress = ((month / 5.5) + phase_offset + index / count) % 1.0
        x_values.append(origin[0] + (destination[0] - origin[0]) * progress)
        y_values.append(origin[1] + (destination[1] - origin[1]) * progress)
    return x_values, y_values


def _multi_flow_points(
    origins: tuple[tuple[float, float], ...],
    destinations: tuple[tuple[float, float], ...],
    month: int,
) -> tuple[list[float], list[float]]:
    x_values: list[float] = []
    y_values: list[float] = []
    for index, (origin, destination) in enumerate(zip(origins, destinations)):
        point_x, point_y = _flow_points(
            origin, destination, month, count=1, phase_offset=index / len(origins)
        )
        x_values.extend(point_x)
        y_values.extend(point_y)
    return x_values, y_values


def _market_opacities(activity: float) -> list[float]:
    thresholds = [index / len(MARKET_BASES) for index in range(len(MARKET_BASES))]
    return [
        0.16 + 0.84 * _bounded((activity - threshold) * len(MARKET_BASES))
        for threshold in thresholds
    ]


def _renewal_points(
    centre: tuple[float, float], month: int, count: int = 7
) -> tuple[list[float], list[float]]:
    radius = 0.046 + 0.006 * math.sin(month * 0.55)
    angles = [month * 0.17 + index * math.tau / count for index in range(count)]
    return (
        [centre[0] + radius * math.cos(angle) for angle in angles],
        [centre[1] + radius * math.sin(angle) for angle in angles],
    )


def _friction_field(
    state: AgentSnapshot,
) -> tuple[list[float], list[float], float]:
    midpoint = (state.specialist_position[0] + state.partner_position[0]) / 2
    half_width = 0.004 + 0.022 * state.friction_strength
    half_height = 0.10 + 0.20 * state.friction_strength
    return (
        [midpoint - half_width, midpoint + half_width] * 2,
        [0.50 - half_height, 0.50 - half_height, 0.50 + half_height, 0.50 + half_height],
        midpoint,
    )


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

    specialist = state.specialist_position
    partner = state.partner_position
    imitators = state.imitator_positions
    markets = state.market_positions

    market_x, market_y = _segments(partner, markets)
    imitation_x, imitation_y = _segments(specialist, imitators)
    capability_x, capability_y = _flow_points(
        specialist, partner, state.month, count=4
    )
    resource_x, resource_y = _flow_points(
        partner, specialist, state.month, count=3, phase_offset=0.35
    )
    value_x, value_y = _multi_flow_points(
        tuple(partner for _ in markets), markets, state.month
    )
    demand_x, demand_y = _multi_flow_points(
        markets[:4], tuple(partner for _ in markets[:4]), state.month
    )
    copying_x, copying_y = _multi_flow_points(
        tuple(specialist for _ in imitators), imitators, state.month
    )
    renewal_x, renewal_y = _renewal_points(specialist, state.month)
    friction_x, friction_y, _ = _friction_field(state)
    specialist_piece_x, specialist_piece_y = _puzzle_piece_points(
        specialist,
        half_width=0.048 + 0.00035 * (state.specialist_size - 30),
        half_height=0.064 + 0.00045 * (state.specialist_size - 30),
        joining_edge="tab-right",
        tab_depth=0.021,
    )
    partner_piece_x, partner_piece_y = _puzzle_piece_points(
        partner,
        half_width=0.067 + 0.00025 * (state.partner_size - 40),
        half_height=0.076 + 0.00035 * (state.partner_size - 40),
        joining_edge="slot-left",
        tab_depth=0.021,
    )
    imitator_piece_x, imitator_piece_y = _joined_puzzle_pieces(
        imitators,
        half_width=0.014 + 0.008 * state.imitation_strength,
        half_height=0.021 + 0.008 * state.imitation_strength,
        tab_depth=0.006,
    )
    interlock_midpoint = (
        (specialist[0] + partner[0]) / 2,
        (specialist[1] + partner[1]) / 2,
    )

    relationship_colour = _rgba("#7A5195", state.relationship_opacity)
    capability_colour = _rgba("#4C78A8", 0.25 + 0.75 * state.recognition_strength)
    resource_colour = _rgba("#F58518", 0.18 + 0.78 * state.resource_flow_strength)
    market_colour = _rgba("#54A24B", 0.12 + 0.82 * state.market_activity)
    demand_colour = _rgba("#D49A00", 0.12 + 0.84 * state.demand_feedback_strength)
    imitation_colour = _rgba("#E45756", 0.10 + 0.82 * state.imitation_strength)
    renewal_strength = _bounded(params.innovation_rate * 12.5)

    market_opacities = _market_opacities(state.market_activity)

    return [
        go.Scatter(
            x=friction_x,
            y=friction_y,
            mode="lines",
            fill="toself",
            fillcolor=_rgba("#E45756", 0.04 + 0.22 * state.friction_strength),
            line={"color": _rgba("#E45756", 0.18 + 0.62 * state.friction_strength), "width": 1},
            hovertemplate=(
                f"<b>Coordination barrier</b><br>Effective friction: "
                f"{state.friction_strength * 100:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=[interlock_midpoint[0]],
            y=[interlock_midpoint[1]],
            mode="markers",
            marker={
                "color": _rgba("#7A5195", 0.02 + 0.12 * state.assembly_progress),
                "size": 70 + 95 * state.assembly_progress,
                "symbol": "circle",
                "line": {
                    "color": _rgba("#7A5195", 0.08 + 0.35 * state.assembly_progress),
                    "width": 1 + 2 * state.assembly_progress,
                },
            },
            hovertemplate=(
                f"<b>Jigsaw interlock</b><br>Assembly: "
                f"{state.assembly_progress * 100:.1f}"
                f"<br>Fit alignment: {state.fit_alignment * 100:.1f}"
                "<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=[0.84],
            y=[0.51],
            mode="markers",
            marker={
                "color": _rgba(
                    "#54A24B", 0.02 + 0.04 * params.market_demand + 0.10 * state.picture_completion
                ),
                "size": 150 + 70 * params.market_demand,
                "symbol": "circle",
                "line": {
                    "color": _rgba("#54A24B", 0.16 + 0.44 * state.picture_completion),
                    "width": 1 + 2 * state.picture_completion,
                },
            },
            hovertemplate=(
                f"<b>Market environment</b><br>Demand: "
                f"{params.market_demand * 100:.1f}"
                f"<br>Picture completion: {state.picture_completion * 100:.1f}"
                "<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=[specialist[0]],
            y=[specialist[1]],
            mode="markers",
            marker={
                "color": _rgba("#4C78A8", 0.65),
                "size": state.specialist_size + 24 + 18 * state.rarity_strength,
                "symbol": "circle-open",
                "line": {"color": _rgba("#4C78A8", 0.35 + 0.60 * state.rarity_strength), "width": 2 + 3 * state.rarity_strength},
            },
            hovertemplate=(
                f"<b>Scarcity field</b><br>Rarity: {rarity:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=renewal_x,
            y=renewal_y,
            mode="markers",
            marker={
                "color": _rgba("#4C78A8", 0.12 + 0.82 * renewal_strength),
                "size": 3 + 7 * renewal_strength,
            },
            hovertemplate=(
                f"<b>Capability renewal</b><br>Innovation: "
                f"{params.innovation_rate * 100:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=[partner[0]],
            y=[partner[1]],
            mode="markers",
            marker={
                "color": _rgba("#F58518", 0.45),
                "size": state.partner_size + 20,
                "symbol": "circle-open",
                "line": {"color": _rgba("#F58518", 0.48), "width": 2},
            },
            hovertemplate=(
                f"<b>Partner platform</b><br>Reach: "
                f"{params.partner_reach * 100:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=[specialist[0], partner[0]],
            y=[specialist[1], partner[1]],
            mode="lines",
            line={"color": relationship_colour, "width": state.relationship_width},
            hovertemplate=(
                f"<b>Partnership interface</b><br>Trust: {trust:.1f}"
                f"<br>Integration: {integration:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=market_x,
            y=market_y,
            mode="lines",
            line={
                "color": market_colour,
                "width": 0.7 + 5.8 * state.value_flow_strength,
            },
            hovertemplate=(
                f"<b>Joint offer</b><br>Realised synergy: "
                f"{realised_synergy:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=imitation_x,
            y=imitation_y,
            mode="lines",
            line={
                "color": imitation_colour,
                "width": 0.6 + 4.8 * state.imitation_strength,
            },
            hovertemplate=(
                f"<b>Copying pressure</b><br>Commoditisation risk: "
                f"{commoditisation:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=capability_x,
            y=capability_y,
            mode="markers",
            marker={
                "color": capability_colour,
                "size": 6 + 11 * state.recognition_strength,
                "symbol": "triangle-right",
            },
            hovertemplate="Specialist capability → partner<extra></extra>",
            showlegend=False,
        ),
        go.Scatter(
            x=resource_x,
            y=resource_y,
            mode="markers",
            marker={
                "color": resource_colour,
                "size": 5 + 10 * state.resource_flow_strength,
                "symbol": "triangle-left",
            },
            hovertemplate="Partner resources and recognition → specialist<extra></extra>",
            showlegend=False,
        ),
        go.Scatter(
            x=value_x,
            y=value_y,
            mode="markers",
            marker={
                "color": market_colour,
                "size": 5 + 13 * state.value_flow_strength,
                "symbol": "triangle-right",
            },
            hovertemplate="Joint value → market<extra></extra>",
            showlegend=False,
        ),
        go.Scatter(
            x=demand_x,
            y=demand_y,
            mode="markers",
            marker={
                "color": demand_colour,
                "size": 4 + 11 * state.demand_feedback_strength,
                "symbol": "triangle-left",
            },
            hovertemplate="Market demand feedback → partner<extra></extra>",
            showlegend=False,
        ),
        go.Scatter(
            x=copying_x,
            y=copying_y,
            mode="markers",
            marker={
                "color": imitation_colour,
                "size": 4 + 13 * state.imitation_strength,
                "symbol": "triangle-up",
            },
            hovertemplate="Capability knowledge copied → imitator<extra></extra>",
            showlegend=False,
        ),
        go.Scatter(
            x=specialist_piece_x,
            y=specialist_piece_y,
            mode="lines",
            fill="toself",
            fillcolor=_rgba("#4C78A8", 0.88),
            line={"color": "#2D4E72", "width": 2.5},
            customdata=[
                [float(row["Expertise depth"]), rarity, local_strength, shaping_power]
                for _ in specialist_piece_x
            ],
            hovertemplate=(
                "<b>Specialist jigsaw piece</b><br>Expertise: %{customdata[0]:.1f}"
                "<br>Rarity: %{customdata[1]:.1f}"
                "<br>Local strength: %{customdata[2]:.1f}"
                "<br>Shaping power: %{customdata[3]:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=partner_piece_x,
            y=partner_piece_y,
            mode="lines",
            fill="toself",
            fillcolor=_rgba("#F58518", 0.88),
            line={"color": "#A65A0A", "width": 2.5},
            customdata=[
                [recognition, trust, integration, params.partner_reach * 100]
                for _ in partner_piece_x
            ],
            hovertemplate=(
                "<b>Partner jigsaw piece</b><br>Recognition: %{customdata[0]:.1f}"
                "<br>Trust: %{customdata[1]:.1f}"
                "<br>Integration: %{customdata[2]:.1f}"
                "<br>Reach: %{customdata[3]:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=imitator_piece_x,
            y=imitator_piece_y,
            mode="lines",
            fill="toself",
            fillcolor=imitation_colour,
            line={"color": "#A23B3A", "width": 1.2},
            hovertemplate=(
                f"<b>Look-alike jigsaw piece</b><br>Commoditisation risk: "
                f"{commoditisation:.1f}<br>Rarity lost: {100 - rarity:.1f}"
                f"<br>Imitation pressure: {params.imitation_pressure * 100:.1f}"
                "<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=[point[0] for point in markets],
            y=[point[1] for point in markets],
            mode="markers+text",
            text=["Market agents", "", "", "", "", "", ""],
            textposition="top center",
            marker={
                "color": [
                    _rgba("#54A24B", opacity) for opacity in market_opacities
                ],
                "size": [17 + 8 * opacity for opacity in market_opacities],
                "line": {"color": "#327333", "width": 1},
            },
            customdata=[
                [adoption, realised_synergy, params.market_demand * 100]
                for _ in markets
            ],
            hovertemplate=(
                "<b>Market agent</b><br>Adoption: %{customdata[0]:.1f}"
                "<br>Realised synergy: %{customdata[1]:.1f}"
                "<br>Market demand: %{customdata[2]:.1f}<extra></extra>"
            ),
            showlegend=False,
        ),
        go.Scatter(
            x=[
                0.22,
                interlock_midpoint[0],
                0.83,
                0.43,
                0.84,
            ],
            y=[
                0.70,
                min(specialist[1], partner[1]) - 0.18,
                0.16,
                0.76,
                0.88,
            ],
            mode="text",
            text=[
                f"Look-alike pressure {state.imitation_strength * 100:.0f}",
                f"Fit {state.fit_alignment * 100:.0f} · Interlock {state.assembly_progress * 100:.0f}"
                f"<br>Trust {trust:.0f} · Integration {integration:.0f}",
                f"Adoption {adoption:.0f} · Demand {params.market_demand * 100:.0f}",
                f"Misalignment {state.friction_strength * 100:.0f}",
                f"Wider picture {state.picture_completion * 100:.0f}% complete",
            ],
            textposition="middle center",
            textfont={"color": "#5D6470", "size": 11},
            hoverinfo="skip",
            showlegend=False,
        ),
        go.Scatter(
            x=[specialist[0], partner[0]],
            y=[specialist[1], partner[1]],
            mode="text",
            text=["SPECIALIST", "PARTNER"],
            textposition="middle center",
            textfont={"color": "#FFFFFF", "size": 10},
            hoverinfo="skip",
            showlegend=False,
        ),
        go.Scatter(
            x=[0.5],
            y=[0.98],
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
        go.Frame(data=_frame_traces(row, params), name=str(int(row["Month"])))
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
        height=640,
        margin={"l": 10, "r": 10, "t": 20, "b": 115},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel={"namelength": -1},
        xaxis={"range": [0, 1.02], "visible": False, "fixedrange": True},
        yaxis={"range": [0.05, 1.03], "visible": False, "fixedrange": True},
        shapes=[
            {
                "type": "rect",
                "x0": 0.015,
                "x1": 0.33,
                "y0": 0.10,
                "y1": 0.92,
                "fillcolor": "rgba(76,120,168,0.035)",
                "line": {"color": "rgba(76,120,168,0.16)", "width": 1},
                "layer": "below",
            },
            {
                "type": "rect",
                "x0": 0.34,
                "x1": 0.65,
                "y0": 0.10,
                "y1": 0.92,
                "fillcolor": "rgba(122,81,149,0.035)",
                "line": {"color": "rgba(122,81,149,0.16)", "width": 1},
                "layer": "below",
            },
            {
                "type": "rect",
                "x0": 0.66,
                "x1": 1.005,
                "y0": 0.10,
                "y1": 0.92,
                "fillcolor": "rgba(84,162,75,0.035)",
                "line": {"color": "rgba(84,162,75,0.16)", "width": 1},
                "layer": "below",
            },
        ],
        annotations=[
            {
                "x": 0.17,
                "y": 0.105,
                "text": "SCARCE PIECE",
                "showarrow": False,
                "font": {"size": 10, "color": "#6C7480"},
                "yanchor": "bottom",
            },
            {
                "x": 0.495,
                "y": 0.105,
                "text": "FIT & INTERLOCK",
                "showarrow": False,
                "font": {"size": 10, "color": "#6C7480"},
                "yanchor": "bottom",
            },
            {
                "x": 0.83,
                "y": 0.105,
                "text": "COMPLETED PICTURE",
                "showarrow": False,
                "font": {"size": 10, "color": "#6C7480"},
                "yanchor": "bottom",
            },
        ],
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "showactive": False,
                "x": 0,
                "y": -0.075,
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
                                    "duration": min(90, frame_duration // 2)
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
