#!/usr/bin/env python3
"""Build World Cup squad-value features from squad pages and player values."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re
import unicodedata

from bs4 import BeautifulSoup
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
SQUAD_HTML_PATHS = {
    2018: BASE_DIR / "data" / "world_cup_squads_2018.html",
    2022: BASE_DIR / "data" / "world_cup_squads_2022.html",
}
PROFILES_PATH = BASE_DIR / "data" / "player_profiles.csv"
MARKET_VALUES_PATH = BASE_DIR / "data" / "player_market_value.csv"
FEATURES_PATH = BASE_DIR / "world_cup_matches_features_elo_form.csv"
TEAM_VALUES_OUTPUT = BASE_DIR / "world_cup_team_squad_values.csv"
PLAYER_VALUES_OUTPUT = BASE_DIR / "world_cup_squad_player_values.csv"

TOURNAMENT_CUTOFFS = {
    2018: pd.Timestamp("2018-06-14"),
    2022: pd.Timestamp("2022-11-20"),
}

TEAM_NAME_ALIASES = {
    "Iran": {"Iran", "IR Iran"},
    "South Korea": {"South Korea", "Korea Republic", "Korea, South"},
    "United States": {"United States", "USA", "United States of America"},
}


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def token_sort_key(value: str) -> str:
    tokens = normalize_text(value).split()
    return " ".join(sorted(tokens))


def clean_profile_name(value: str) -> str:
    value = re.sub(r"\s*\(\d+\)\s*$", "", value or "")
    return " ".join(value.split())


def clean_squad_name(value: str) -> str:
    value = re.sub(r"\(\s*captain\s*\)", "", value or "", flags=re.IGNORECASE)
    return " ".join(value.split())


def citizenship_aliases(team: str) -> set[str]:
    aliases = TEAM_NAME_ALIASES.get(team, {team})
    return {normalize_text(alias) for alias in aliases}


def parse_squads() -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for year, path in SQUAD_HTML_PATHS.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing squad page: {path}")

        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        for heading in soup.find_all("h3"):
            group_heading = heading.find_previous("h2")
            if group_heading is None:
                continue
            group_name = " ".join(group_heading.get_text(" ", strip=True).split())
            if not group_name.startswith("Group "):
                continue

            team = " ".join(heading.get_text(" ", strip=True).split())
            table = heading.find_next("table")
            if table is None:
                continue

            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["th", "td"])
                if len(cells) < 7:
                    continue

                player_cell = cells[2]
                player_link = player_cell.find("a")
                player_name = player_link.get_text(" ", strip=True) if player_link else player_cell.get_text(" ", strip=True)
                player_name = clean_squad_name(player_name)

                dob_text = cells[3].get_text(" ", strip=True)
                dob_match = re.search(r"\(\s*(\d{4}-\d{2}-\d{2})\s*\)", dob_text)
                if dob_match is None:
                    continue

                rows.append(
                    {
                        "year": year,
                        "team": team,
                        "player_name": player_name,
                        "birth_date": dob_match.group(1),
                    }
                )

    squad = pd.DataFrame(rows)
    if squad.empty:
        raise ValueError("No squad rows were parsed from the squad pages.")
    return squad.drop_duplicates(subset=["year", "team", "player_name", "birth_date"])


def load_profiles() -> tuple[pd.DataFrame, dict[tuple[str, str], list[int]]]:
    profiles = pd.read_csv(
        PROFILES_PATH,
        usecols=["player_id", "player_name", "name_in_home_country", "date_of_birth", "citizenship"],
        dtype={"player_id": "string", "player_name": "string", "name_in_home_country": "string", "date_of_birth": "string", "citizenship": "string"},
    ).fillna("")

    profiles["clean_player_name"] = profiles["player_name"].map(clean_profile_name)
    profiles["name_key"] = profiles["clean_player_name"].map(normalize_text)
    profiles["home_name_key"] = profiles["name_in_home_country"].map(normalize_text)
    profiles["name_token_key"] = profiles["clean_player_name"].map(token_sort_key)
    profiles["home_name_token_key"] = profiles["name_in_home_country"].map(token_sort_key)
    profiles["citizenship_keys"] = profiles["citizenship"].map(
        lambda value: {
            normalize_text(part)
            for part in re.split(r"[,/;]+", value)
            if normalize_text(part)
        }
    )

    candidate_index: dict[tuple[str, str], list[int]] = defaultdict(list)
    for idx, row in profiles.iterrows():
        if row["date_of_birth"] and row["name_key"]:
            candidate_index[(row["date_of_birth"], row["name_key"])].append(idx)
        if row["date_of_birth"] and row["home_name_key"]:
            candidate_index[(row["date_of_birth"], row["home_name_key"])].append(idx)
        if row["date_of_birth"] and row["name_token_key"]:
            candidate_index[(row["date_of_birth"], row["name_token_key"])].append(idx)
        if row["date_of_birth"] and row["home_name_token_key"]:
            candidate_index[(row["date_of_birth"], row["home_name_token_key"])].append(idx)

    return profiles, candidate_index


def choose_profile_match(
    player_name: str,
    birth_date: str,
    team: str,
    profiles: pd.DataFrame,
    candidate_index: dict[tuple[str, str], list[int]],
) -> tuple[str | None, str | None]:
    name_key = normalize_text(player_name)
    token_key = token_sort_key(player_name)
    candidate_ids = list(dict.fromkeys(candidate_index.get((birth_date, name_key), [])))
    if not candidate_ids and token_key:
        candidate_ids = list(dict.fromkeys(candidate_index.get((birth_date, token_key), [])))
    if not candidate_ids:
        return None, "no_birthdate_name_match"

    candidates = profiles.loc[candidate_ids].copy()
    team_alias_keys = citizenship_aliases(team)
    citizenship_mask = candidates["citizenship_keys"].map(lambda keys: bool(keys & team_alias_keys))
    if citizenship_mask.any():
        candidates = candidates[citizenship_mask]

    if len(candidates) == 1:
        return str(candidates.iloc[0]["player_id"]), "matched"

    exact_name = candidates[candidates["name_key"].eq(name_key)]
    if len(exact_name) == 1:
        return str(exact_name.iloc[0]["player_id"]), "matched"

    exact_home = candidates[candidates["home_name_key"].eq(name_key)]
    if len(exact_home) == 1:
        return str(exact_home.iloc[0]["player_id"]), "matched"

    return str(candidates.iloc[0]["player_id"]), "matched_ambiguous"


def build_matched_squad_players(
    squad: pd.DataFrame,
    profiles: pd.DataFrame,
    candidate_index: dict[tuple[str, str], list[int]],
) -> pd.DataFrame:
    matched_rows: list[dict[str, object]] = []

    for row in squad.itertuples(index=False):
        player_id, match_status = choose_profile_match(
            player_name=row.player_name,
            birth_date=row.birth_date,
            team=row.team,
            profiles=profiles,
            candidate_index=candidate_index,
        )
        matched_rows.append(
            {
                "year": row.year,
                "team": row.team,
                "player_name": row.player_name,
                "birth_date": row.birth_date,
                "player_id": player_id,
                "match_status": match_status,
            }
        )

    return pd.DataFrame(matched_rows)


def load_player_values(player_ids: set[str]) -> pd.DataFrame:
    chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        MARKET_VALUES_PATH,
        usecols=["player_id", "date_unix", "value"],
        dtype={"player_id": "string", "date_unix": "string", "value": "float64"},
        chunksize=200_000,
    ):
        filtered = chunk[chunk["player_id"].isin(player_ids)].copy()
        if filtered.empty:
            continue
        filtered["value_date"] = pd.to_datetime(filtered["date_unix"], errors="coerce")
        filtered = filtered.dropna(subset=["value_date", "value"])
        chunks.append(filtered[["player_id", "value_date", "value"]])

    if not chunks:
        raise ValueError("No historical market values found for the matched player ids.")

    values = pd.concat(chunks, ignore_index=True)
    values["player_id"] = values["player_id"].astype("string")
    return values.sort_values(["player_id", "value_date"], kind="stable").reset_index(drop=True)


def latest_value_before_cutoff(
    values: pd.DataFrame,
    year: int,
    cutoff: pd.Timestamp,
) -> pd.DataFrame:
    eligible = values[values["value_date"] <= cutoff].copy()
    if eligible.empty:
        return pd.DataFrame(columns=["player_id", "value_date", "value"])
    eligible = eligible.sort_values(["player_id", "value_date"], kind="stable")
    latest = eligible.groupby("player_id", as_index=False).tail(1).copy()
    latest["year"] = year
    return latest[["year", "player_id", "value_date", "value"]]


def build_team_value_tables(matched_players: pd.DataFrame, values: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    value_frames = [
        latest_value_before_cutoff(values, year, cutoff)
        for year, cutoff in TOURNAMENT_CUTOFFS.items()
    ]
    latest_values = pd.concat(value_frames, ignore_index=True)

    player_values = matched_players.merge(
        latest_values,
        on=["year", "player_id"],
        how="left",
    )

    team_values = (
        player_values.groupby(["year", "team"], as_index=False)
        .agg(
            squad_size=("player_name", "count"),
            matched_players=("player_id", lambda col: int(col.notna().sum())),
            valued_players=("value", lambda col: int(col.notna().sum())),
            squad_value_eur=("value", lambda col: col.sum(min_count=1)),
        )
    )
    team_values["avg_player_value_eur"] = team_values["squad_value_eur"] / team_values["valued_players"].where(team_values["valued_players"] > 0)
    team_values["coverage_ratio"] = team_values["valued_players"] / team_values["squad_size"]
    return player_values, team_values


def update_feature_table(team_values: pd.DataFrame) -> pd.DataFrame:
    features = pd.read_csv(FEATURES_PATH, parse_dates=["match_date"])
    lookup = {
        (int(row.year), str(row.team)): float(row.squad_value_eur)
        for row in team_values.itertuples(index=False)
    }

    feature_years = features["match_date"].dt.year.astype(int)
    features["team_a_squad_value"] = [
        lookup.get((year, team))
        for year, team in zip(feature_years, features["team_a"], strict=True)
    ]
    features["team_b_squad_value"] = [
        lookup.get((year, team))
        for year, team in zip(feature_years, features["team_b"], strict=True)
    ]
    features["squad_value_diff"] = features["team_a_squad_value"] - features["team_b_squad_value"]
    features.to_csv(FEATURES_PATH, index=False)
    return features


def main() -> None:
    squad = parse_squads()
    profiles, candidate_index = load_profiles()
    matched_players = build_matched_squad_players(squad, profiles, candidate_index)
    matched_ids = {player_id for player_id in matched_players["player_id"].dropna().astype(str)}
    values = load_player_values(matched_ids)
    player_values, team_values = build_team_value_tables(matched_players, values)

    player_values.to_csv(PLAYER_VALUES_OUTPUT, index=False)
    team_values.to_csv(TEAM_VALUES_OUTPUT, index=False)
    enriched_features = update_feature_table(team_values)

    print(f"Wrote player-level squad values to {PLAYER_VALUES_OUTPUT}")
    print(f"Wrote team-level squad values to {TEAM_VALUES_OUTPUT}")
    print(f"Updated features in {FEATURES_PATH}")
    print(f"Matched squad players: {int(matched_players['player_id'].notna().sum())}/{len(matched_players)}")
    print(f"Players with pre-tournament market values: {int(player_values['value'].notna().sum())}/{len(player_values)}")
    print(f"Matches with team_a squad value: {int(enriched_features['team_a_squad_value'].notna().sum())}/{len(enriched_features)}")


if __name__ == "__main__":
    main()
