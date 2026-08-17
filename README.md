# Jigsaw Strategy Simulator

An interactive learning model of the Jigsaw strategy from *Patterns of Strategy*.
It explores how a smaller specialist can concentrate scarce expertise, become
locally stronger than a larger partner, and turn complementarity into joint value.

The app includes a playable ecosystem simulation. A specialist, partner,
imitators, and market agents visibly evolve as expertise, trust, integration,
imitation, and adoption change month by month.

The model is explanatory, not predictive. All outputs are dimensionless scores
on a 0–100 scale.

## Run locally

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run jigsaw_strategy_simulator.py
```

Streamlit will print the local URL in the terminal, typically
`http://localhost:8501`.

## What to explore

- Reduce scarcity or increase imitation pressure to observe commoditisation.
- Increase capability concentration to see a small specialist build local strength.
- Reduce partner complementarity to test why expertise alone is insufficient.
- Increase coordination friction to separate potential from realised synergy.
- Increase renewal to preserve differentiation after success.

## Read the agent simulation

- The blue tabbed piece is the scarce specialist capability; its size follows
  expertise and its halo reflects rarity. Orbiting dots show renewal activity.
- The orange platform piece has the complementary slot. Complementarity aligns
  the two pieces; recognition, trust, and integration bring them together until
  they interlock.
- Red look-alike pieces grow and move toward the specialist as copying pressure
  and commoditisation increase, competing for the same place in the system.
- Green circles are market agents; they activate and move toward the joint offer
  as adoption increases, gradually revealing a more complete value picture.
- Blue arrows carry specialist capability to the partner, while orange arrows
  return resources and recognition.
- Green arrows carry joint value into the market, while gold arrows return
  demand feedback. Red arrows show capability knowledge being copied.
- The translucent red barrier represents effective coordination friction. It
  shrinks as trust and integration reduce friction's effect.
- Background zones distinguish the scarce piece, the fit-and-interlock process,
  and the completed market picture.

Use **Play** and **Pause** inside the chart, drag its month slider to scrub the
timeline, or change playback speed above it.

Choose **Integrated jigsaw** to watch a high-fit relationship progress to a
complete phase-6 interlock and reveal the wider market picture.

## Control groups

The sidebar groups controls by their primary target in the agent simulation:

- **Specialist piece (blue):** capability concentration, initial expertise,
  learning, renewal, and scarcity.
- **Partner platform (orange):** partner reach and openness.
- **Fit & interlock (blue ↔ orange):** complementarity, trust, reliability,
  integration effort, and coordination friction.
- **Look-alike imitators (red):** imitation pressure.
- **Market picture (green):** market demand.

These are primary effects, not isolated ones. For example, higher imitation
pressure acts through the red pieces but eventually reduces the blue piece's
rarity, while stronger interlock can increase green-agent adoption.

## Test

```bash
python -m pip install -r requirements-dev.txt
pytest
```

## Repository layout

- `jigsaw_strategy_simulator.py` — Streamlit interface and Plotly charts.
- `jigsaw_strategy_model.py` — deterministic simulation model.
- `jigsaw_agent_visualization.py` — animated ecosystem view.
- `tests/test_simulation.py` — smoke tests for model invariants.
