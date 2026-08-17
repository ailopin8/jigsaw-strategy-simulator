"""Deterministic system-dynamics model for the Jigsaw strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Params:
    months: int = 72
    focus: float = 0.78
    initial_expertise: float = 0.35
    learning_rate: float = 0.045
    innovation_rate: float = 0.025
    initial_rarity: float = 0.82
    imitation_pressure: float = 0.018
    complementarity: float = 0.80
    partner_reach: float = 0.82
    partner_openness: float = 0.65
    initial_trust: float = 0.18
    delivery_reliability: float = 0.78
    integration_effort: float = 0.48
    coordination_friction: float = 0.25
    market_demand: float = 0.72
    specialist_size: float = 0.22
    partner_size: float = 0.85


PHASES = {
    1: "1 Focus scarce expertise",
    2: "2 Establish local strength",
    3: "3 Win partner recognition",
    4: "4 Build combined value",
    5: "5 Co-evolve and shape locally",
    6: "6 Synchronise delivery",
}


def clamp(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def simulate(p: Params) -> pd.DataFrame:
    """Run a deterministic system-dynamics simulation of the Jigsaw pattern."""
    expertise = p.initial_expertise
    rarity = p.initial_rarity
    trust = p.initial_trust
    integration = 0.05
    recognition = 0.04
    adoption = 0.02
    rows: List[Dict[str, float | int | str]] = []

    for month in range(p.months + 1):
        critical_mass = clamp(expertise * p.focus * rarity)
        local_strength = clamp(
            critical_mass
            / max(0.08, critical_mass + p.partner_size * (1.0 - p.complementarity))
        )

        fit_quality = clamp(
            0.42 * p.complementarity
            + 0.23 * rarity
            + 0.20 * trust
            + 0.15 * p.partner_openness
            - 0.20 * p.coordination_friction * (1.0 - integration)
        )
        potential_synergy = clamp(
            expertise
            * rarity
            * p.complementarity
            * p.partner_reach
            * (0.45 + 0.55 * fit_quality)
            * 2.0
        )
        realised_synergy = clamp(
            potential_synergy * recognition * (0.35 + 0.65 * integration)
        )
        shaping_power = clamp(
            local_strength * recognition * trust * (0.65 + 0.35 * rarity) * 2.0
        )
        defensibility = clamp(0.45 * rarity + 0.35 * expertise + 0.20 * trust)
        commoditisation = clamp(
            (1.0 - rarity) * recognition * (1.0 - defensibility) * 2.2
        )
        value_created = clamp(
            realised_synergy * p.market_demand * (0.55 + 0.45 * adoption)
        )
        value_captured = clamp(
            value_created * (0.30 + 0.50 * shaping_power + 0.20 * rarity)
        )
        effective_friction = clamp(
            p.coordination_friction * (1.0 - 0.72 * integration) * (1.0 - 0.22 * trust)
        )
        imitation_intensity = clamp(
            p.imitation_pressure
            * 12.5
            * (0.35 + 0.65 * recognition)
            * (1.0 - 0.50 * expertise)
            + 0.32 * (1.0 - rarity)
            + 0.20 * commoditisation
        )
        market_pull = clamp(p.market_demand * (0.35 + 0.65 * adoption))

        specialist_environment_balance = (
            0.45 * market_pull
            + 0.20 * trust
            + 0.20 * fit_quality
            + 0.15 * rarity
            - 0.55 * imitation_intensity
            - 0.45 * effective_friction
        )
        partner_environment_balance = (
            0.45 * market_pull
            + 0.20 * integration
            + 0.15 * trust
            + 0.20 * fit_quality
            - 0.55 * effective_friction
            - 0.20 * commoditisation
        )
        specialist_environment_support = clamp(
            0.50 + 0.50 * specialist_environment_balance
        )
        partner_environment_support = clamp(0.50 + 0.50 * partner_environment_balance)
        specialist_influence = clamp(
            0.20 * expertise
            + 0.20 * rarity
            + 0.20 * local_strength
            + 0.20 * shaping_power
            + 0.10 * value_captured
            + 0.10 * market_pull
            + 0.18 * specialist_environment_balance
        )
        partner_influence = clamp(
            0.24 * p.partner_reach
            + 0.16 * recognition
            + 0.15 * trust
            + 0.16 * integration
            + 0.15 * realised_synergy
            + 0.08 * adoption
            + 0.06 * market_pull
            + 0.18 * partner_environment_balance
        )
        imitator_influence = clamp(
            0.55 * imitation_intensity + 0.25 * commoditisation + 0.20 * (1.0 - rarity)
        )
        joint_environment_control = clamp(
            0.28 * specialist_influence
            + 0.28 * partner_influence
            + 0.16 * realised_synergy
            + 0.12 * adoption
            + 0.10 * integration
            + 0.06 * fit_quality
            - 0.18 * effective_friction
        )

        if integration >= 0.67 and trust >= 0.58 and recognition >= 0.70:
            phase = 6
        elif trust >= 0.46 and recognition >= 0.60:
            phase = 5
        elif recognition >= 0.42:
            phase = 4
        elif local_strength >= 0.48 and potential_synergy >= 0.32:
            phase = 3
        elif critical_mass >= 0.34:
            phase = 2
        else:
            phase = 1

        if commoditisation > 0.52:
            status = "Commoditising"
        elif fit_quality < 0.34 and recognition > 0.35:
            status = "Partnership strain"
        elif phase >= 5 and value_created > 0.35:
            status = "Jigsaw functioning"
        elif phase >= 3:
            status = "Partnership forming"
        else:
            status = "Capability building"

        rows.append(
            {
                "Month": month,
                "Phase": phase,
                "Phase name": PHASES[phase],
                "Status": status,
                "Expertise depth": expertise * 100,
                "Rarity": rarity * 100,
                "Critical mass": critical_mass * 100,
                "Local strength": local_strength * 100,
                "Partner recognition": recognition * 100,
                "Trust": trust * 100,
                "Integration": integration * 100,
                "Potential synergy": potential_synergy * 100,
                "Realised synergy": realised_synergy * 100,
                "Shaping power": shaping_power * 100,
                "Value created": value_created * 100,
                "Value captured": value_captured * 100,
                "Market adoption": adoption * 100,
                "Commoditisation risk": commoditisation * 100,
                "Market pull": market_pull * 100,
                "Specialist environmental support": specialist_environment_support
                * 100,
                "Partner environmental support": partner_environment_support * 100,
                "Specialist influence": specialist_influence * 100,
                "Partner influence": partner_influence * 100,
                "Imitator influence": imitator_influence * 100,
                "Joint environmental control": joint_environment_control * 100,
            }
        )

        if month == p.months:
            break

        expertise_gain = p.learning_rate * p.focus * (1.0 - expertise)
        expertise_loss = (
            0.009 * (1.0 - p.focus) + 0.006 * p.coordination_friction * integration
        )
        expertise = clamp(expertise + expertise_gain - expertise_loss)

        rarity = clamp(
            rarity
            + p.innovation_rate * expertise * (1.0 - rarity)
            - p.imitation_pressure * recognition * (0.45 + 0.55 * (1.0 - expertise))
        )

        recognition_target = clamp(
            local_strength
            * potential_synergy
            * p.partner_openness
            * (0.70 + 0.30 * trust)
            * 2.4
        )
        recognition = clamp(recognition + 0.11 * (recognition_target - recognition))

        delivery_signal = (
            recognition * p.delivery_reliability * (0.35 + 0.65 * fit_quality)
        )
        trust_target = clamp(
            delivery_signal - 0.32 * p.coordination_friction * (1.0 - integration)
        )
        trust = clamp(trust + 0.075 * (trust_target - trust))

        integration_target = clamp(
            p.integration_effort
            * recognition
            * trust
            * (1.0 - 0.55 * p.coordination_friction)
            * 2.5
        )
        integration = clamp(integration + 0.065 * (integration_target - integration))

        adoption_target = clamp(
            realised_synergy * p.market_demand * p.partner_reach * 1.55
        )
        adoption = clamp(adoption + 0.085 * (adoption_target - adoption))

    return pd.DataFrame(rows)


def phase_bands(df: pd.DataFrame) -> List[tuple[int, int, int]]:
    """Return contiguous phase spans as (start, end, phase) tuples."""
    bands: List[tuple[int, int, int]] = []
    start = 0
    previous = int(df.iloc[0]["Phase"])
    for idx in range(1, len(df)):
        current = int(df.iloc[idx]["Phase"])
        if current != previous:
            bands.append((start, idx - 1, previous))
            start, previous = idx, current
    bands.append((start, len(df) - 1, previous))
    return bands


def insight_for(row: pd.Series) -> str:
    """Explain the state represented by a simulation row."""
    phase = int(row["Phase"])
    if row["Commoditisation risk"] > 52:
        return (
            "The specialist is becoming interchangeable. Imitation is eroding rarity "
            "faster than innovation renews it, so bargaining shifts toward price."
        )
    if row["Status"] == "Partnership strain":
        return (
            "The capability is recognised, but friction is preventing trust and "
            "integration. The Jigsaw piece exists without fitting cleanly into the "
            "partner's system."
        )
    messages = {
        1: "The organisation is still concentrating resources and deepening a scarce capability.",
        2: "Critical mass has created local strength even though the specialist remains smaller overall.",
        3: "The partner can now see a combined value proposition and begins treating the specialist as an edge expert.",
        4: "The parties are turning complementary capabilities into realised joint value.",
        5: "The relationship co-evolves overall, while the specialist shapes decisions inside its narrow domain.",
        6: "Delivery interfaces are synchronised; the specialist capability now functions as part of a larger system.",
    }
    return messages[phase]
