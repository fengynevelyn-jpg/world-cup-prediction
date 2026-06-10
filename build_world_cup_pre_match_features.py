#!/usr/bin/env python3
"""Build pre-match World Cup features from historical international results."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


BASE_DIR = Path("/Users/evelynfeng/Documents/gaming")
RESULTS_PATH = BASE_DIR / "data" / "international_results" / "results.csv"
SEED_PATH = BASE_DIR / "world_cup_matches_seed_2018_2022.csv"
OUTPUT_PATH = BASE_DIR / "world_cup_matches_features_elo_form.csv"
SQUAD_VALUE_PATH = BASE_DIR / "world_cup_team_squad_values.csv"
FIFA_SNAPSHOT_PATHS = {
    2018: BASE_DIR / "data" / "fifa" / "fifaranking_2018_06_07.html",
    2022: BASE_DIR / "data" / "fifa" / "fifaranking_2022_10_06.html",
}

DEFAULT_ELO = 1500.0
HOME_ADVANTAGE_ELO = 80.0

CONFEDERATION_MAP = {
    "Argentina": "CONMEBOL",
    "Australia": "AFC",
    "Belgium": "UEFA",
    "Brazil": "CONMEBOL",
    "Cameroon": "CAF",
    "Canada": "CONCACAF",
    "Costa Rica": "CONCACAF",
    "Croatia": "UEFA",
    "Denmark": "UEFA",
    "Ecuador": "CONMEBOL",
    "Egypt": "CAF",
    "England": "UEFA",
    "France": "UEFA",
    "Germany": "UEFA",
    "Ghana": "CAF",
    "Iran": "AFC",
    "Iceland": "UEFA",
    "Japan": "AFC",
    "Mexico": "CONCACAF",
    "Morocco": "CAF",
    "Netherlands": "UEFA",
    "Nigeria": "CAF",
    "Panama": "CONCACAF",
    "Peru": "CONMEBOL",
    "Poland": "UEFA",
    "Portugal": "UEFA",
    "Qatar": "AFC",
    "Russia": "UEFA",
    "Saudi Arabia": "AFC",
    "Senegal": "CAF",
    "Serbia": "UEFA",
    "South Korea": "AFC",
    "Spain": "UEFA",
    "Sweden": "UEFA",
    "Switzerland": "UEFA",
    "Tunisia": "CAF",
    "United States": "CONCACAF",
    "Uruguay": "CONMEBOL",
    "Wales": "UEFA",
}

WORLD_CUP_TOURNAMENTS = {
    "FIFA World Cup": 60.0,
    "Confederations Cup": 40.0,
    "UEFA Euro": 50.0,
    "Copa América": 50.0,
    "AFC Asian Cup": 45.0,
    "African Cup of Nations": 45.0,
    "CONCACAF Championship": 45.0,
    "CONCACAF Nations League": 35.0,
    "UEFA Nations League": 35.0,
    "FIFA World Cup qualification": 40.0,
    "UEFA Euro qualification": 35.0,
    "AFC Asian Cup qualification": 30.0,
    "African Cup of Nations qualification": 30.0,
    "CONCACAF Championship qualification": 30.0,
    "Copa América qualification": 30.0,
    "Friendly": 20.0,
}

FIFA_TEAM_NAME_MAP = {
    "Iran": "IR Iran",
    "South Korea": "Korea Republic",
    "United States": "USA",
}


@dataclass
class TeamSnapshot:
    elo: float
    last5_points: float
    last5_goals_for: float
    last5_goals_against: float
    rest_days: float | None


def tournament_weight(tournament: str) -> float:
    return WORLD_CUP_TOURNAMENTS.get(tournament, 25.0)


def goal_difference_multiplier(home_score: float, away_score: float) -> float:
    diff = abs(home_score - away_score)
    if diff <= 1:
        return 1.0
    if diff == 2:
        return 1.5
    return (11.0 + diff) / 8.0


def expected_score(team_rating: float, opp_rating: float, home_advantage: float) -> float:
    return 1.0 / (1.0 + 10 ** (-(team_rating + home_advantage - opp_rating) / 400.0))


def actual_score(goals_for: float, goals_against: float) -> float:
    if goals_for > goals_against:
        return 1.0
    if goals_for == goals_against:
        return 0.5
    return 0.0


def snapshot_for_team(
    team: str,
    match_date: pd.Timestamp,
    ratings: dict[str, float],
    recent_matches: dict[str, deque[dict]],
    last_match_dates: dict[str, pd.Timestamp],
) -> TeamSnapshot:
    history = list(recent_matches[team])[-5:]
    last5_points = sum(item["points"] for item in history)
    last5_goals_for = sum(item["goals_for"] for item in history)
    last5_goals_against = sum(item["goals_against"] for item in history)
    if team in last_match_dates:
        rest_days = float((match_date - last_match_dates[team]).days)
    else:
        rest_days = None

    return TeamSnapshot(
        elo=ratings[team],
        last5_points=last5_points,
        last5_goals_for=last5_goals_for,
        last5_goals_against=last5_goals_against,
        rest_days=rest_days,
    )


def build_match_key(df: pd.DataFrame) -> pd.Series:
    return (
        df["match_date"].astype(str)
        + "|"
        + df["team_a"].astype(str)
        + "|"
        + df["team_b"].astype(str)
    )


def normalize_team_for_fifa(team: str) -> str:
    return FIFA_TEAM_NAME_MAP.get(team, team)


def load_fifa_rankings() -> dict[int, dict[str, int]]:
    snapshots: dict[int, dict[str, int]] = {}

    for year, path in FIFA_SNAPSHOT_PATHS.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing FIFA ranking snapshot: {path}")

        tables = pd.read_html(path)
        snapshot_frames: list[pd.DataFrame] = []

        for table in tables:
            if "Team" in table.columns and "Rank" in table.columns:
                frame = table[["Rank", "Team"]].copy()
            elif 3 in table.columns and 0 in table.columns:
                frame = table[[0, 3]].copy()
                frame.columns = ["Rank", "Team"]
            else:
                continue

            frame["Rank"] = pd.to_numeric(frame["Rank"], errors="coerce")
            frame["Team"] = frame["Team"].astype(str).str.strip()
            frame = frame.dropna(subset=["Rank"])
            frame = frame[frame["Team"].ne("")]
            snapshot_frames.append(frame)

        if not snapshot_frames:
            raise ValueError(f"Could not parse FIFA rankings from {path}")

        snapshot = pd.concat(snapshot_frames, ignore_index=True)
        snapshot = snapshot.drop_duplicates(subset=["Team"], keep="first")
        snapshots[year] = {
            row.Team: int(row.Rank)
            for row in snapshot.itertuples(index=False)
        }

    return snapshots


def load_squad_value_lookup() -> dict[tuple[int, str], float]:
    if not SQUAD_VALUE_PATH.exists():
        return {}

    squad_values = pd.read_csv(SQUAD_VALUE_PATH)
    required_columns = {"year", "team", "squad_value_eur"}
    if not required_columns.issubset(squad_values.columns):
        return {}

    squad_values = squad_values.dropna(subset=["year", "team", "squad_value_eur"])
    return {
        (int(row.year), str(row.team)): float(row.squad_value_eur)
        for row in squad_values.itertuples(index=False)
    }


def main() -> None:
    results = pd.read_csv(RESULTS_PATH, parse_dates=["date"])
    results = results.sort_values(
        ["date", "home_team", "away_team", "tournament"],
        kind="stable",
    ).reset_index(drop=True)

    seed = pd.read_csv(SEED_PATH, parse_dates=["match_date"])
    seed["match_key"] = build_match_key(seed)
    seed_lookup = {
        (row.match_date.date().isoformat(), row.team_a, row.team_b): row.match_key
        for row in seed.itertuples(index=False)
    }
    fifa_rankings = load_fifa_rankings()
    squad_value_lookup = load_squad_value_lookup()

    ratings = defaultdict(lambda: DEFAULT_ELO)
    recent_matches: dict[str, deque[dict]] = defaultdict(lambda: deque(maxlen=5))
    last_match_dates: dict[str, pd.Timestamp] = {}

    world_cup_features: dict[str, dict] = {}

    for match_date, daily_matches in results.groupby("date", sort=True):
        daily_feature_rows: list[tuple[pd.Series, TeamSnapshot, TeamSnapshot]] = []

        for _, match in daily_matches.iterrows():
            home_team = match["home_team"]
            away_team = match["away_team"]

            home_snapshot = snapshot_for_team(
                home_team, match_date, ratings, recent_matches, last_match_dates
            )
            away_snapshot = snapshot_for_team(
                away_team, match_date, ratings, recent_matches, last_match_dates
            )
            daily_feature_rows.append((match, home_snapshot, away_snapshot))

        for match, home_snapshot, away_snapshot in daily_feature_rows:
            home_team = match["home_team"]
            away_team = match["away_team"]
            seed_match_key = seed_lookup.get((match_date.date().isoformat(), home_team, away_team))
            reversed_orientation = False
            if seed_match_key is None:
                seed_match_key = seed_lookup.get(
                    (match_date.date().isoformat(), away_team, home_team)
                )
                reversed_orientation = seed_match_key is not None

            if seed_match_key is not None:
                team_a_snapshot = away_snapshot if reversed_orientation else home_snapshot
                team_b_snapshot = home_snapshot if reversed_orientation else away_snapshot
                team_a_name = away_team if reversed_orientation else home_team
                team_b_name = home_team if reversed_orientation else away_team
                conf_a = CONFEDERATION_MAP.get(team_a_name)
                conf_b = CONFEDERATION_MAP.get(team_b_name)
                fifa_snapshot = fifa_rankings.get(match_date.year, {})
                team_a_fifa_rank = fifa_snapshot.get(normalize_team_for_fifa(team_a_name))
                team_b_fifa_rank = fifa_snapshot.get(normalize_team_for_fifa(team_b_name))
                world_cup_features[seed_match_key] = {
                    "team_a_elo": round(team_a_snapshot.elo, 2),
                    "team_b_elo": round(team_b_snapshot.elo, 2),
                    "elo_diff": round(team_a_snapshot.elo - team_b_snapshot.elo, 2),
                    "team_a_fifa_rank": team_a_fifa_rank,
                    "team_b_fifa_rank": team_b_fifa_rank,
                    "fifa_rank_diff": (
                        None
                        if team_a_fifa_rank is None or team_b_fifa_rank is None
                        else team_a_fifa_rank - team_b_fifa_rank
                    ),
                    "team_a_last5_points": team_a_snapshot.last5_points,
                    "team_b_last5_points": team_b_snapshot.last5_points,
                    "last5_points_diff": team_a_snapshot.last5_points - team_b_snapshot.last5_points,
                    "team_a_last5_goals_for": team_a_snapshot.last5_goals_for,
                    "team_b_last5_goals_for": team_b_snapshot.last5_goals_for,
                    "goals_for_diff": team_a_snapshot.last5_goals_for - team_b_snapshot.last5_goals_for,
                    "team_a_last5_goals_against": team_a_snapshot.last5_goals_against,
                    "team_b_last5_goals_against": team_b_snapshot.last5_goals_against,
                    "goals_against_diff": team_a_snapshot.last5_goals_against - team_b_snapshot.last5_goals_against,
                    "team_a_last5_goal_diff": team_a_snapshot.last5_goals_for - team_a_snapshot.last5_goals_against,
                    "team_b_last5_goal_diff": team_b_snapshot.last5_goals_for - team_b_snapshot.last5_goals_against,
                    "last5_goal_diff_gap": (
                        (team_a_snapshot.last5_goals_for - team_a_snapshot.last5_goals_against)
                        - (team_b_snapshot.last5_goals_for - team_b_snapshot.last5_goals_against)
                    ),
                    "team_a_rest_days": team_a_snapshot.rest_days,
                    "team_b_rest_days": team_b_snapshot.rest_days,
                    "rest_days_diff": (
                        None
                        if team_a_snapshot.rest_days is None or team_b_snapshot.rest_days is None
                        else team_a_snapshot.rest_days - team_b_snapshot.rest_days
                    ),
                    "confederation_a": conf_a,
                    "confederation_b": conf_b,
                    "confederation_pair": (
                        f"{conf_a}_vs_{conf_b}" if conf_a and conf_b else None
                    ),
                    "same_confederation_flag": (
                        None if conf_a is None or conf_b is None else int(conf_a == conf_b)
                    ),
                }

        for match, home_snapshot, away_snapshot in daily_feature_rows:
            home_team = match["home_team"]
            away_team = match["away_team"]
            home_score = float(match["home_score"])
            away_score = float(match["away_score"])
            home_advantage = 0.0 if bool(match["neutral"]) else HOME_ADVANTAGE_ELO

            expected_home = expected_score(home_snapshot.elo, away_snapshot.elo, home_advantage)
            actual_home = actual_score(home_score, away_score)
            k = tournament_weight(match["tournament"]) * goal_difference_multiplier(home_score, away_score)
            delta = k * (actual_home - expected_home)

            ratings[home_team] = home_snapshot.elo + delta
            ratings[away_team] = away_snapshot.elo - delta

            recent_matches[home_team].append(
                {
                    "points": 3 if home_score > away_score else 1 if home_score == away_score else 0,
                    "goals_for": home_score,
                    "goals_against": away_score,
                }
            )
            recent_matches[away_team].append(
                {
                    "points": 3 if away_score > home_score else 1 if home_score == away_score else 0,
                    "goals_for": away_score,
                    "goals_against": home_score,
                }
            )
            last_match_dates[home_team] = match_date
            last_match_dates[away_team] = match_date

    feature_frame = pd.DataFrame.from_dict(world_cup_features, orient="index")
    feature_frame.index.name = "match_key"
    feature_frame = feature_frame.reset_index()
    enriched = seed.copy()
    feature_columns = [column for column in feature_frame.columns if column != "match_key"]
    drop_columns = [column for column in feature_columns if column in enriched.columns]
    if drop_columns:
        enriched = enriched.drop(columns=drop_columns)
    enriched = enriched.merge(feature_frame, on="match_key", how="left")

    if squad_value_lookup:
        match_years = enriched["match_date"].dt.year.astype(int)
        enriched["team_a_squad_value"] = [
            squad_value_lookup.get((year, team))
            for year, team in zip(match_years, enriched["team_a"], strict=True)
        ]
        enriched["team_b_squad_value"] = [
            squad_value_lookup.get((year, team))
            for year, team in zip(match_years, enriched["team_b"], strict=True)
        ]
        enriched["squad_value_diff"] = (
            enriched["team_a_squad_value"] - enriched["team_b_squad_value"]
        )

    enriched = enriched.drop(columns=["match_key"])
    enriched.to_csv(OUTPUT_PATH, index=False)

    missing_elo = int(enriched["team_a_elo"].isna().sum())
    missing_fifa_rank = int(enriched["team_a_fifa_rank"].isna().sum())
    print(f"Wrote {len(enriched)} rows to {OUTPUT_PATH}")
    print(f"Rows missing Elo features: {missing_elo}")
    print(f"Rows missing FIFA ranking features: {missing_fifa_rank}")


if __name__ == "__main__":
    main()
