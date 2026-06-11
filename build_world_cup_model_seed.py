#!/usr/bin/env python3
"""Create a model-ready seed CSV from the flattened World Cup results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RESULTS_PATH = BASE_DIR / "world_cup_match_results_2018_2022.csv"
TEMPLATE_PATH = BASE_DIR / "world_cup_matches_template.csv"
OUTPUT_PATH = BASE_DIR / "world_cup_matches_seed_2018_2022.csv"


def main() -> None:
    results = pd.read_csv(RESULTS_PATH)
    template_columns = pd.read_csv(TEMPLATE_PATH, nrows=0).columns.tolist()

    seed = pd.DataFrame(columns=template_columns)
    seed["match_id"] = results["match_id"]
    seed["match_date"] = results["match_date"]
    seed["tournament"] = "FIFA World Cup"
    seed["stage"] = results["stage"]
    seed["is_knockout"] = results["is_knockout"]
    seed["team_a"] = results["team_a"]
    seed["team_b"] = results["team_b"]
    seed["target_result_90m"] = results["target_result_90m"]

    # Keep the template column order so additional features can be filled later.
    seed = seed.reindex(columns=template_columns)
    seed.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(seed)} seed rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
