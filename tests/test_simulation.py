from math import dist

import pandas as pd

from jigsaw_agent_visualization import make_agent_simulation_chart, snapshot_for
from jigsaw_strategy_model import Params, phase_bands, simulate


def test_default_simulation_has_one_row_per_month() -> None:
    result = simulate(Params(months=24))

    assert len(result) == 25
    assert result["Month"].tolist() == list(range(25))


def test_scores_stay_within_zero_to_one_hundred() -> None:
    result = simulate(Params())
    score_columns = [
        column
        for column in result.columns
        if column not in {"Month", "Phase", "Phase name", "Status"}
    ]

    assert ((result[score_columns] >= 0) & (result[score_columns] <= 100)).all().all()
    assert result["Phase"].between(1, 6).all()


def test_simulation_is_deterministic() -> None:
    params = Params(months=36, initial_rarity=0.48, imitation_pressure=0.06)

    pd.testing.assert_frame_equal(simulate(params), simulate(params))


def test_phase_bands_cover_the_full_timeline() -> None:
    result = simulate(Params(months=12))
    bands = phase_bands(result)

    assert bands[0][0] == 0
    assert bands[-1][1] == 12
    assert sum(end - start + 1 for start, end, _ in bands) == 13


def test_agent_snapshot_visual_values_are_bounded() -> None:
    params = Params(months=12)
    final_row = simulate(params).iloc[-1]
    snapshot = snapshot_for(final_row, params)

    assert 30 <= snapshot.specialist_size <= 56
    assert 40 <= snapshot.partner_size <= 62
    assert 1 <= snapshot.relationship_width <= 8
    assert 0 <= snapshot.relationship_opacity <= 1
    assert 0 <= snapshot.imitation_strength <= 1
    assert 0 <= snapshot.market_activity <= 1
    assert 0 <= snapshot.value_flow_strength <= 1
    assert 0 <= snapshot.demand_feedback_strength <= 1
    assert 0 <= snapshot.friction_strength <= 1
    assert 0 <= snapshot.rarity_strength <= 1
    assert 0 <= snapshot.specialist_position[0] <= 1
    assert 0 <= snapshot.partner_position[0] <= 1


def test_agent_animation_has_one_frame_per_month() -> None:
    params = Params(months=12)
    result = simulate(params)
    figure = make_agent_simulation_chart(result, params)

    assert len(figure.frames) == 13
    assert [frame.name for frame in figure.frames] == [str(month) for month in range(13)]
    assert len(figure.data) == len(figure.frames[0].data)
    assert len(figure.layout.shapes) == 3


def test_agent_motion_reflects_strategic_forces() -> None:
    protected_params = Params(
        months=72,
        initial_rarity=0.90,
        imitation_pressure=0.0,
        innovation_rate=0.08,
    )
    copied_params = Params(
        months=72,
        initial_rarity=0.45,
        imitation_pressure=0.08,
        innovation_rate=0.0,
    )
    protected = snapshot_for(simulate(protected_params).iloc[-1], protected_params)
    copied = snapshot_for(simulate(copied_params).iloc[-1], copied_params)

    protected_distance = sum(
        dist(position, protected.specialist_position)
        for position in protected.imitator_positions
    )
    copied_distance = sum(
        dist(position, copied.specialist_position)
        for position in copied.imitator_positions
    )

    assert copied.imitation_strength > protected.imitation_strength
    assert copied_distance < protected_distance


def test_integration_reduces_barrier_and_draws_partners_together() -> None:
    params = Params(
        months=72,
        initial_trust=0.70,
        partner_openness=0.95,
        complementarity=0.95,
        integration_effort=0.95,
        delivery_reliability=0.98,
        market_demand=0.95,
    )
    result = simulate(params)
    first = snapshot_for(result.iloc[0], params)
    final = snapshot_for(result.iloc[-1], params)

    assert final.friction_strength < first.friction_strength
    assert dist(final.specialist_position, final.partner_position) < dist(
        first.specialist_position, first.partner_position
    )
    assert final.market_activity > first.market_activity
