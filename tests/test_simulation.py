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

    assert 28 <= snapshot.specialist_size <= 64
    assert 34 <= snapshot.partner_size <= 68
    assert 1 <= snapshot.relationship_width <= 8
    assert 0 <= snapshot.relationship_opacity <= 1
    assert 0 <= snapshot.imitation_strength <= 1
    assert 0 <= snapshot.market_activity <= 1
    assert 0 <= snapshot.value_flow_strength <= 1
    assert 0 <= snapshot.demand_feedback_strength <= 1
    assert 0 <= snapshot.friction_strength <= 1
    assert 0 <= snapshot.rarity_strength <= 1
    assert 0 <= snapshot.fit_alignment <= 1
    assert 0 <= snapshot.assembly_progress <= 1
    assert 0 <= snapshot.picture_completion <= 1
    assert 0 <= snapshot.market_pull <= 1
    assert 0 <= snapshot.specialist_environment_support <= 1
    assert 0 <= snapshot.partner_environment_support <= 1
    assert 0 <= snapshot.specialist_influence <= 1
    assert 0 <= snapshot.partner_influence <= 1
    assert 0 <= snapshot.imitator_influence <= 1
    assert 0 <= snapshot.joint_environment_control <= 1
    assert 0 <= snapshot.specialist_position[0] <= 1
    assert 0 <= snapshot.partner_position[0] <= 1


def test_agent_animation_has_one_frame_per_month() -> None:
    params = Params(months=12)
    result = simulate(params)
    figure = make_agent_simulation_chart(result, params)

    assert len(figure.frames) == 13
    assert [frame.name for frame in figure.frames] == [
        str(month) for month in range(13)
    ]
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
    assert final.assembly_progress > first.assembly_progress
    assert final.picture_completion > first.picture_completion
    assert dist(final.specialist_position, final.partner_position) < dist(
        first.specialist_position, first.partner_position
    )
    assert final.market_activity > first.market_activity


def test_complementarity_controls_jigsaw_alignment() -> None:
    shared = {
        "months": 0,
        "coordination_friction": 0.10,
        "initial_trust": 0.70,
        "partner_openness": 0.95,
    }
    good_params = Params(complementarity=0.95, **shared)
    poor_params = Params(complementarity=0.20, **shared)
    good = snapshot_for(simulate(good_params).iloc[0], good_params)
    poor = snapshot_for(simulate(poor_params).iloc[0], poor_params)

    good_misalignment = abs(good.specialist_position[1] - good.partner_position[1])
    poor_misalignment = abs(poor.specialist_position[1] - poor.partner_position[1])

    assert good.fit_alignment > poor.fit_alignment
    assert good_misalignment < poor_misalignment


def test_environment_expands_or_contracts_piece_influence() -> None:
    supportive_params = Params(
        months=72,
        initial_rarity=0.90,
        imitation_pressure=0.0,
        innovation_rate=0.08,
        complementarity=0.95,
        partner_openness=0.95,
        initial_trust=0.55,
        delivery_reliability=0.98,
        integration_effort=0.95,
        coordination_friction=0.05,
        market_demand=0.95,
    )
    imitative_environment_params = Params(
        months=72,
        initial_rarity=0.65,
        imitation_pressure=0.08,
        innovation_rate=0.0,
        complementarity=0.80,
        partner_openness=0.80,
        initial_trust=0.30,
        delivery_reliability=0.85,
        integration_effort=0.60,
        coordination_friction=0.25,
        market_demand=0.70,
    )

    supportive_result = simulate(supportive_params)
    imitative_result = simulate(imitative_environment_params)
    supportive_first = snapshot_for(supportive_result.iloc[0], supportive_params)
    supportive_final = snapshot_for(supportive_result.iloc[-1], supportive_params)
    imitative_first = snapshot_for(
        imitative_result.iloc[0], imitative_environment_params
    )
    imitative_final = snapshot_for(
        imitative_result.iloc[-1], imitative_environment_params
    )

    assert supportive_final.specialist_influence > supportive_first.specialist_influence
    assert supportive_final.partner_influence > supportive_first.partner_influence
    assert (
        supportive_final.joint_environment_control
        > supportive_first.joint_environment_control
    )
    assert imitative_final.imitator_influence > imitative_first.imitator_influence
    assert imitative_final.specialist_influence < imitative_first.specialist_influence
    assert (
        imitative_final.joint_environment_control
        < imitative_first.joint_environment_control
    )
    assert imitative_final.specialist_size < imitative_first.specialist_size
    assert imitative_final.specialist_size < supportive_final.specialist_size
