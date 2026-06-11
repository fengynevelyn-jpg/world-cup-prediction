# World Cup Prediction

An experimental football match prediction project built around the **2018** and **2022** men's FIFA World Cups.

The current modeling focus is a **Version B** setup:

- use historical World Cup matches as the training base
- allow in-tournament rolling state features when they exist
- compare simple priors against richer state-driven models
- prioritize probability quality over raw accuracy

## What is in this repo

- feature-building scripts for Elo, recent form, player-state proxies, optional squad value, and sparse xG/xGA
- baseline and adaptive prediction scripts
- a schema document and lightweight example/template CSVs

## What is intentionally excluded

This public repo does **not** bundle:

- raw third-party datasets
- locally generated feature tables
- experiment output tables
- internal handoff notes

That is intentional for both privacy and data-rights reasons.

## Data and compliance

Please read [world_cup_data_sources.md](world_cup_data_sources.md) before using the pipeline.

Short version:

- obtain third-party data yourself
- check and follow each source's license or terms
- attribute sources where required
- do not assume that a locally generated CSV is automatically safe to redistribute

## Main files

- `build_world_cup_pre_match_features.py`
- `build_world_cup_player_status_features.py`
- `build_world_cup_squad_values.py`
- `train_world_cup_baseline.py`
- `run_world_cup_version_b_experiments.py`
- `run_world_cup_version_b_adaptive_experiments.py`
- `predict_world_cup_version_b_adaptive.py`
- `world_cup_prediction_schema.md`
- `world_cup_matches_template.csv`
- `world_cup_matches_example.csv`
- `world_cup_matches_demo.csv`

## Current modeling takeaway

The most practical setup so far is an adaptive Version B strategy:

- `close` matches: use `base_form`
- `medium` matches: use `player_state_squad_value_xg`
- `lopsided` matches: use `base_form`

This repo treats that as an experiment workflow, not a production forecasting system.

## Metrics

The project mainly tracks:

- `log loss`
- `Brier score`

Accuracy is reported, but it is not the primary decision criterion.

## Dependencies

Python 3 with:

- `pandas`
- `numpy`
- `beautifulsoup4`

Install with:

```bash
pip install -r requirements.txt
```
