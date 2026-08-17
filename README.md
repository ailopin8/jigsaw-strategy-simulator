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

- The blue diamond is the specialist; its size follows expertise and its border
  reflects rarity.
- The orange square is the partner; the connecting line strengthens as
  recognition, trust, and integration develop.
- Red triangles are imitators; they become more prominent as copying pressure
  and commoditisation increase.
- Green circles are market agents; they activate as the combined offer gains
  adoption.
- Moving particles represent capability exchange and value reaching the market.

Use **Play** and **Pause** inside the chart, drag its month slider to scrub the
timeline, or change playback speed above it.

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
