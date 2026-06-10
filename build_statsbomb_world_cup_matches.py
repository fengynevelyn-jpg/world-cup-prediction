#!/usr/bin/env python3
"""Flatten StatsBomb World Cup match JSON files into a CSV dataset."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path("/Users/evelynfeng/Documents/gaming")
MATCH_DIR = BASE_DIR / "data" / "statsbomb" / "matches"
OUTPUT_PATH = BASE_DIR / "world_cup_match_results_2018_2022.csv"

INPUTS = [
    ("2018", MATCH_DIR / "world_cup_2018_matches.json"),
    ("2022", MATCH_DIR / "world_cup_2022_matches.json"),
]

STAGE_MAP = {
    "Group Stage": "group",
    "Round of 16": "round_of_16",
    "Quarter-finals": "quarterfinal",
    "Semi-finals": "semifinal",
    "3rd Place Final": "third_place",
    "Final": "final",
}


def normalize_stage(raw_stage: str) -> str:
    return STAGE_MAP.get(raw_stage, raw_stage.lower().replace(" ", "_"))


def outcome_label(home_score: int, away_score: int) -> int:
    if home_score > away_score:
        return 0
    if home_score == away_score:
        return 1
    return 2


def load_matches(path: Path, season_name: str) -> list[dict]:
    rows = json.loads(path.read_text())
    output: list[dict] = []
    for row in rows:
        raw_stage = row["competition_stage"]["name"]
        home_score = int(row["home_score"])
        away_score = int(row["away_score"])
        output.append(
            {
                "season": season_name,
                "match_id": row["match_id"],
                "match_date": row["match_date"],
                "kick_off": row["kick_off"],
                "stage": normalize_stage(raw_stage),
                "stage_display": raw_stage,
                "is_knockout": int(raw_stage != "Group Stage"),
                "team_a": row["home_team"]["home_team_name"],
                "team_b": row["away_team"]["away_team_name"],
                "team_a_group": row["home_team"].get("home_team_group"),
                "team_b_group": row["away_team"].get("away_team_group"),
                "team_a_manager": first_manager_name(row["home_team"].get("managers", [])),
                "team_b_manager": first_manager_name(row["away_team"].get("managers", [])),
                "team_a_country": row["home_team"]["country"]["name"],
                "team_b_country": row["away_team"]["country"]["name"],
                "team_a_score": home_score,
                "team_b_score": away_score,
                "scoreline_90m": f"{home_score}-{away_score}",
                "target_result_90m": outcome_label(home_score, away_score),
                "stadium": row["stadium"]["name"] if row.get("stadium") else None,
                "host_country": row["stadium"]["country"]["name"] if row.get("stadium") else None,
                "referee": row.get("referee", {}).get("name"),
            }
        )
    return output


def first_manager_name(managers: list[dict]) -> str | None:
    if not managers:
        return None
    return managers[0].get("nickname") or managers[0].get("name")


def main() -> None:
    all_rows: list[dict] = []
    for season_name, path in INPUTS:
        if not path.exists():
            raise FileNotFoundError(f"Missing input file: {path}")
        all_rows.extend(load_matches(path, season_name))

    df = pd.DataFrame(all_rows)
    df["match_date"] = pd.to_datetime(df["match_date"], errors="raise")
    df = df.sort_values(["match_date", "kick_off", "match_id"], kind="stable").reset_index(drop=True)
    df.to_csv(OUTPUT_PATH, index=False)

    summary = (
        df.groupby("season", sort=True)
        .agg(matches=("match_id", "count"))
        .reset_index()
    )
    print(f"Wrote {len(df)} matches to {OUTPUT_PATH}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
