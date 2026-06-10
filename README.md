# World Cup Prediction

An experimental football match prediction project built around the **2018** and **2022** men's FIFA World Cups.

The current project focus is a **Version B** setup:

- use historical World Cup matches as the training base
- allow in-tournament rolling state features when they exist
- compare simple priors against richer state-driven models
- evaluate with probability-quality metrics, not just accuracy

## What is in this repo

- feature-building scripts for Elo, form, player status, squad value, and sparse xG/xGA
- baseline and adaptive prediction scripts
- experiment summaries and handoff notes
- lightweight example CSVs and derived experiment outputs

## What is intentionally not in this repo

Large raw data files are excluded from version control:

- StatsBomb event/match raw dumps
- historical international results raw archive
- large downloaded HTML/ZIP assets

Those files live locally under `data/` and can be regenerated or redownloaded.

## Current project state

The most important project summary is here:

- [world_cup_project_handoff.md](world_cup_project_handoff.md)

Supporting experiment summaries:

- [world_cup_experiment_comparison.md](world_cup_experiment_comparison.md)
- [world_cup_version_b_experiment_results.md](world_cup_version_b_experiment_results.md)
- [world_cup_version_b_adaptive_results.md](world_cup_version_b_adaptive_results.md)

## Main scripts

- `build_world_cup_pre_match_features.py`
- `build_world_cup_player_status_features.py`
- `build_world_cup_squad_values.py`
- `train_world_cup_baseline.py`
- `run_world_cup_version_b_experiments.py`
- `run_world_cup_version_b_adaptive_experiments.py`
- `predict_world_cup_version_b_adaptive.py`

## Current modeling takeaway

The strongest current default is not a single static model.

The most practical setup so far is an **adaptive Version B** strategy:

- `close` matches: use `base_form`
- `medium` matches: use `player_state_squad_value_xg`
- `lopsided` matches: use `base_form`

This came from walk-forward evaluation on the **2022 World Cup**, using **2018** as the historical training base.

## Metrics we care about

This project prioritizes:

- `log loss`
- `Brier score`

Accuracy is still reported, but it is not the main decision criterion.

## Dependencies

Python 3 with:

- `pandas`
- `numpy`
- `beautifulsoup4`

You can install them with:

```bash
pip install -r requirements.txt
```

## Data sources

See:

- [world_cup_data_sources.md](world_cup_data_sources.md)

Main sources used in the local workflow include:

- StatsBomb open data
- historical international match results
- FIFA ranking snapshots
- a Transfermarkt-derived public player market value dataset

## Notes

- This is an experiment repo, not a production forecasting system.
- Some features are still sparse, especially event-derived player state and xG.
- Opening-match predictions should fall back to a pre-tournament branch when no current-tournament state exists yet.

