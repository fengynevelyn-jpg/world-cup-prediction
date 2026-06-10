#!/usr/bin/env python3
"""Build player-status and lineup-stability features from StatsBomb event data."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


BASE_DIR = Path("/Users/evelynfeng/Documents/gaming")
INPUT_PATH = BASE_DIR / "world_cup_matches_features_elo_form.csv"
OUTPUT_PATH = BASE_DIR / "world_cup_matches_features_elo_form.csv"
EVENT_DIR = BASE_DIR / "data" / "statsbomb" / "events"

RECENT_MATCH_WINDOW = 5
KEY_PLAYER_COUNT = 4

FEATURE_COLUMNS = [
    "team_a_top11_avg_rating_last5",
    "team_b_top11_avg_rating_last5",
    "top11_rating_diff",
    "team_a_top11_avg_minutes_last5",
    "team_b_top11_avg_minutes_last5",
    "top11_minutes_diff",
    "team_a_attack_core_form_score",
    "team_b_attack_core_form_score",
    "attack_core_form_diff",
    "team_a_gk_form_score",
    "team_b_gk_form_score",
    "gk_form_diff",
    "team_a_recent_starts_stability",
    "team_b_recent_starts_stability",
    "starts_stability_diff",
    "team_a_key_absence_score",
    "team_b_key_absence_score",
    "key_absence_diff",
    "team_a_avg_xg_last5",
    "team_b_avg_xg_last5",
    "xg_diff",
    "team_a_avg_xga_last5",
    "team_b_avg_xga_last5",
    "xga_diff",
]

SAVE_EVENT_TYPES = {"Shot Saved", "Save", "Penalty Saved"}
ON_TARGET_SHOT_OUTCOMES = {"Saved", "Goal", "Saved to Post", "Saved To Post"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-missing-events",
        action="store_true",
        help="Fill only matches whose event files already exist instead of failing fast.",
    )
    return parser.parse_args()


@dataclass
class PlayerMatchStats:
    minutes: float = 0.0
    goals: float = 0.0
    goal_assists: float = 0.0
    shot_assists: float = 0.0
    xg: float = 0.0
    shots_on_target: float = 0.0
    saves: float = 0.0
    goals_conceded: float = 0.0

    @property
    def rating(self) -> float:
        # A lightweight proxy rating that blends usage, attack output, and GK shot-stopping.
        return (
            6.0
            + 0.01 * self.minutes
            + 1.5 * self.goals
            + 1.0 * self.goal_assists
            + 0.5 * self.shot_assists
            + 0.8 * self.xg
            + 0.15 * self.shots_on_target
            + 0.12 * self.saves
            - 0.25 * self.goals_conceded
        )


@dataclass
class TeamMatchData:
    starters: list[str]
    positions: dict[str, tuple[int, str]]
    player_stats: dict[str, PlayerMatchStats]


def safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def safe_diff(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return float(a - b)


def current_goalkeeper(starters: list[str], positions: dict[str, tuple[int, str]]) -> str | None:
    for player in starters:
        position = positions.get(player)
        if position and position[0] == 1:
            return player
    return None


def choose_attack_core(starters: list[str], positions: dict[str, tuple[int, str]]) -> list[str]:
    outfield = [player for player in starters if positions.get(player, (999, ""))[0] != 1]
    ranked = sorted(
        outfield,
        key=lambda player: positions.get(player, (0, ""))[0],
        reverse=True,
    )
    return ranked[:3]


def player_attack_form(recent_matches: deque[PlayerMatchStats]) -> float:
    total_minutes = sum(match.minutes for match in recent_matches)
    if total_minutes <= 0:
        return 0.0
    total_score = sum(
        2.0 * match.goals
        + 1.5 * match.goal_assists
        + 0.5 * match.shot_assists
        + 1.0 * match.xg
        + 0.25 * match.shots_on_target
        for match in recent_matches
    )
    return float(total_score * 90.0 / total_minutes)


def player_gk_form(recent_matches: deque[PlayerMatchStats]) -> float | None:
    total_minutes = sum(match.minutes for match in recent_matches)
    if total_minutes <= 0:
        return None
    total_saves = sum(match.saves for match in recent_matches)
    total_goals_conceded = sum(match.goals_conceded for match in recent_matches)
    return float((total_saves - total_goals_conceded) * 90.0 / total_minutes)


def build_core_player_weights(
    player_recent: dict[str, deque[PlayerMatchStats]],
    player_positions: dict[str, Counter],
) -> list[tuple[str, float]]:
    scored: list[tuple[str, float]] = []
    for player, matches in player_recent.items():
        if not matches:
            continue
        total_minutes = sum(match.minutes for match in matches)
        total_goals = sum(match.goals for match in matches)
        total_goal_assists = sum(match.goal_assists for match in matches)
        total_shot_assists = sum(match.shot_assists for match in matches)
        total_saves = sum(match.saves for match in matches)
        primary_position_id = player_positions[player].most_common(1)[0][0] if player_positions[player] else None
        role_weight = 1.5 if primary_position_id == 1 else 1.0
        score = (
            total_minutes
            + 25.0 * total_goals
            + 15.0 * total_goal_assists
            + 5.0 * total_shot_assists
            + 4.0 * total_saves
        )
        scored.append((player, score * role_weight))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:KEY_PLAYER_COUNT]


def compute_team_pre_match_features(
    team: str,
    starters: list[str],
    positions: dict[str, tuple[int, str]],
    player_recent: dict[str, deque[PlayerMatchStats]],
    player_positions: dict[str, Counter],
    previous_starters: list[str] | None,
    recent_team_xg: deque[dict[str, float]],
) -> dict[str, float | None]:
    starter_recent_matches = [player_recent[player] for player in starters if player_recent[player]]
    starter_ratings = [
        safe_mean([match.rating for match in recent_matches])
        for recent_matches in starter_recent_matches
    ]
    starter_ratings = [value for value in starter_ratings if value is not None]
    starter_minutes = [
        sum(match.minutes for match in player_recent[player])
        for player in starters
        if player_recent[player]
    ]

    attack_core = choose_attack_core(starters, positions)
    attack_scores = [
        player_attack_form(player_recent[player])
        for player in attack_core
        if player_recent[player]
    ]

    goalkeeper = current_goalkeeper(starters, positions)
    gk_form = (
        player_gk_form(player_recent[goalkeeper])
        if goalkeeper is not None and player_recent[goalkeeper]
        else None
    )

    starts_stability = None
    if previous_starters:
        starts_stability = float(
            len(set(starters) & set(previous_starters)) / max(len(previous_starters), 1)
        )

    key_absence_score = None
    core_players = build_core_player_weights(player_recent, player_positions)
    if core_players:
        starter_set = set(starters)
        key_absence_score = float(
            sum(
                1.5 if player_positions[player].most_common(1)[0][0] == 1 else 1.0
                for player, _ in core_players
                if player not in starter_set
            )
        )

    avg_xg_last5 = safe_mean([match["xg"] for match in recent_team_xg]) if recent_team_xg else None
    avg_xga_last5 = safe_mean([match["xga"] for match in recent_team_xg]) if recent_team_xg else None

    return {
        "top11_avg_rating_last5": safe_mean(starter_ratings),
        "top11_avg_minutes_last5": safe_mean(starter_minutes),
        "attack_core_form_score": safe_mean(attack_scores),
        "gk_form_score": gk_form,
        "recent_starts_stability": starts_stability,
        "key_absence_score": key_absence_score,
        "avg_xg_last5": avg_xg_last5,
        "avg_xga_last5": avg_xga_last5,
    }


def parse_match_events(match_id: int) -> dict[str, TeamMatchData]:
    path = EVENT_DIR / f"{match_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing event file: {path}")

    events = json.loads(path.read_text())
    if not events:
        raise ValueError(f"Event file is empty: {path}")

    match_end_minute = max(int(event.get("minute", 0)) for event in events)
    if match_end_minute < 90:
        match_end_minute = 90

    starters_by_team: dict[str, list[str]] = {}
    positions_by_team: dict[str, dict[str, tuple[int, str]]] = {}

    for event in events:
        if event.get("type", {}).get("name") != "Starting XI":
            continue
        team = event.get("team", {}).get("name")
        lineup = event.get("tactics", {}).get("lineup", [])
        starters: list[str] = []
        positions: dict[str, tuple[int, str]] = {}
        for row in lineup:
            player_name = row.get("player", {}).get("name")
            position = row.get("position", {})
            if not player_name:
                continue
            starters.append(player_name)
            positions[player_name] = (int(position.get("id", 0)), position.get("name", "Unknown"))
        if team:
            starters_by_team[team] = starters
            positions_by_team[team] = positions

    if len(starters_by_team) != 2:
        raise ValueError(f"Expected 2 Starting XI events in match {match_id}")

    minute_windows: dict[str, dict[str, list[float | None]]] = {}
    player_stats_by_team: dict[str, dict[str, PlayerMatchStats]] = {}

    for team, starters in starters_by_team.items():
        minute_windows[team] = {
            player: [0.0, float(match_end_minute)] for player in starters
        }
        player_stats_by_team[team] = {
            player: PlayerMatchStats() for player in starters
        }

    for event in events:
        if event.get("type", {}).get("name") != "Substitution":
            continue
        team = event.get("team", {}).get("name")
        player_out = event.get("player", {}).get("name")
        player_in = event.get("substitution", {}).get("replacement", {}).get("name")
        minute = float(event.get("minute", 0))
        if not team or not player_out or not player_in:
            continue

        minute_windows[team].setdefault(player_out, [0.0, float(match_end_minute)])[1] = minute
        minute_windows[team][player_in] = [minute, float(match_end_minute)]
        player_stats_by_team[team].setdefault(player_out, PlayerMatchStats())
        player_stats_by_team[team].setdefault(player_in, PlayerMatchStats())

    for team, windows in minute_windows.items():
        for player, (minute_in, minute_out) in windows.items():
            minutes = max(0.0, float(minute_out) - float(minute_in))
            player_stats_by_team[team].setdefault(player, PlayerMatchStats()).minutes = minutes

    for event in events:
        team = event.get("team", {}).get("name")
        player = event.get("player", {}).get("name")
        if not team or not player:
            continue
        player_stats_by_team.setdefault(team, {})
        player_stats_by_team[team].setdefault(player, PlayerMatchStats())
        stats = player_stats_by_team[team][player]
        event_type = event.get("type", {}).get("name")

        if event_type == "Shot":
            shot = event.get("shot", {})
            outcome = shot.get("outcome", {}).get("name")
            stats.xg += float(shot.get("statsbomb_xg") or 0.0)
            if outcome == "Goal":
                stats.goals += 1.0
            if outcome in ON_TARGET_SHOT_OUTCOMES:
                stats.shots_on_target += 1.0

        elif event_type == "Pass":
            passing = event.get("pass", {})
            if passing.get("goal_assist"):
                stats.goal_assists += 1.0
            if passing.get("shot_assist"):
                stats.shot_assists += 1.0

        elif event_type == "Goal Keeper":
            goalkeeper = event.get("goalkeeper", {})
            gk_type = goalkeeper.get("type", {}).get("name")
            if gk_type in SAVE_EVENT_TYPES:
                stats.saves += 1.0
            elif gk_type == "Goal Conceded":
                stats.goals_conceded += 1.0

    return {
        team: TeamMatchData(
            starters=starters_by_team[team],
            positions=positions_by_team.get(team, {}),
            player_stats=player_stats_by_team.get(team, {}),
        )
        for team in starters_by_team
    }


def event_file_is_complete(match_id: int) -> bool:
    path = EVENT_DIR / f"{match_id}.json"
    if not path.exists():
        return False
    try:
        json.loads(path.read_text())
    except json.JSONDecodeError:
        return False
    return True


def main() -> None:
    args = parse_args()
    df = pd.read_csv(INPUT_PATH, parse_dates=["match_date"])
    df = df.sort_values(["match_date", "match_id"], kind="stable").reset_index(drop=True)

    missing_events = [
        int(match_id)
        for match_id in df["match_id"].tolist()
        if not event_file_is_complete(int(match_id))
    ]
    if missing_events and not args.allow_missing_events:
        preview = ", ".join(str(match_id) for match_id in missing_events[:10])
        raise FileNotFoundError(
            f"Missing {len(missing_events)} event files. First missing match_ids: {preview}"
        )
    if missing_events and args.allow_missing_events:
        available_ids = {
            int(match_id)
            for match_id in df["match_id"].tolist()
            if (EVENT_DIR / f"{int(match_id)}.json").exists()
        }
        df = df[df["match_id"].isin(available_ids)].copy()

    team_player_recent: dict[tuple[int, str], dict[str, deque[PlayerMatchStats]]] = defaultdict(
        lambda: defaultdict(lambda: deque(maxlen=RECENT_MATCH_WINDOW))
    )
    team_player_positions: dict[tuple[int, str], dict[str, Counter]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    team_previous_starters: dict[tuple[int, str], list[str]] = {}
    team_recent_xg: dict[tuple[int, str], deque[dict[str, float]]] = defaultdict(
        lambda: deque(maxlen=RECENT_MATCH_WINDOW)
    )

    feature_rows: dict[int, dict[str, float | None]] = {}
    skipped_match_ids: list[int] = []

    for row in df.itertuples(index=False):
        tournament_year = int(row.match_date.year)
        try:
            match_data = parse_match_events(int(row.match_id))
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            if args.allow_missing_events:
                skipped_match_ids.append(int(row.match_id))
                continue
            raise

        team_a_key = (tournament_year, row.team_a)
        team_b_key = (tournament_year, row.team_b)

        team_a_match = match_data.get(row.team_a)
        team_b_match = match_data.get(row.team_b)
        if team_a_match is None or team_b_match is None:
            raise ValueError(
                f"Team names in event data do not match row {row.match_id}: "
                f"{row.team_a} vs {row.team_b}"
            )

        team_a_features = compute_team_pre_match_features(
            row.team_a,
            team_a_match.starters,
            team_a_match.positions,
            team_player_recent[team_a_key],
            team_player_positions[team_a_key],
            team_previous_starters.get(team_a_key),
            team_recent_xg[team_a_key],
        )
        team_b_features = compute_team_pre_match_features(
            row.team_b,
            team_b_match.starters,
            team_b_match.positions,
            team_player_recent[team_b_key],
            team_player_positions[team_b_key],
            team_previous_starters.get(team_b_key),
            team_recent_xg[team_b_key],
        )

        feature_rows[int(row.match_id)] = {
            "team_a_top11_avg_rating_last5": team_a_features["top11_avg_rating_last5"],
            "team_b_top11_avg_rating_last5": team_b_features["top11_avg_rating_last5"],
            "top11_rating_diff": safe_diff(
                team_a_features["top11_avg_rating_last5"],
                team_b_features["top11_avg_rating_last5"],
            ),
            "team_a_top11_avg_minutes_last5": team_a_features["top11_avg_minutes_last5"],
            "team_b_top11_avg_minutes_last5": team_b_features["top11_avg_minutes_last5"],
            "top11_minutes_diff": safe_diff(
                team_a_features["top11_avg_minutes_last5"],
                team_b_features["top11_avg_minutes_last5"],
            ),
            "team_a_attack_core_form_score": team_a_features["attack_core_form_score"],
            "team_b_attack_core_form_score": team_b_features["attack_core_form_score"],
            "attack_core_form_diff": safe_diff(
                team_a_features["attack_core_form_score"],
                team_b_features["attack_core_form_score"],
            ),
            "team_a_gk_form_score": team_a_features["gk_form_score"],
            "team_b_gk_form_score": team_b_features["gk_form_score"],
            "gk_form_diff": safe_diff(
                team_a_features["gk_form_score"],
                team_b_features["gk_form_score"],
            ),
            "team_a_recent_starts_stability": team_a_features["recent_starts_stability"],
            "team_b_recent_starts_stability": team_b_features["recent_starts_stability"],
            "starts_stability_diff": safe_diff(
                team_a_features["recent_starts_stability"],
                team_b_features["recent_starts_stability"],
            ),
            "team_a_key_absence_score": team_a_features["key_absence_score"],
            "team_b_key_absence_score": team_b_features["key_absence_score"],
            "key_absence_diff": safe_diff(
                team_a_features["key_absence_score"],
                team_b_features["key_absence_score"],
            ),
            "team_a_avg_xg_last5": team_a_features["avg_xg_last5"],
            "team_b_avg_xg_last5": team_b_features["avg_xg_last5"],
            "xg_diff": safe_diff(
                team_a_features["avg_xg_last5"],
                team_b_features["avg_xg_last5"],
            ),
            "team_a_avg_xga_last5": team_a_features["avg_xga_last5"],
            "team_b_avg_xga_last5": team_b_features["avg_xga_last5"],
            "xga_diff": safe_diff(
                team_a_features["avg_xga_last5"],
                team_b_features["avg_xga_last5"],
            ),
        }

        team_a_match_xg = sum(stats.xg for stats in team_a_match.player_stats.values())
        team_b_match_xg = sum(stats.xg for stats in team_b_match.player_stats.values())

        for team_name, match_team_data in [(row.team_a, team_a_match), (row.team_b, team_b_match)]:
            team_key = (tournament_year, team_name)
            for player, stats in match_team_data.player_stats.items():
                team_player_recent[team_key][player].append(stats)
            for player, (position_id, _) in match_team_data.positions.items():
                team_player_positions[team_key][player][position_id] += 1
            team_previous_starters[team_key] = match_team_data.starters
            if team_name == row.team_a:
                team_recent_xg[team_key].append({"xg": team_a_match_xg, "xga": team_b_match_xg})
            else:
                team_recent_xg[team_key].append({"xg": team_b_match_xg, "xga": team_a_match_xg})

    feature_frame = pd.DataFrame.from_dict(feature_rows, orient="index")
    feature_frame.index.name = "match_id"
    feature_frame = feature_frame.reset_index()

    full_df = pd.read_csv(INPUT_PATH, parse_dates=["match_date"])
    enriched = full_df.drop(columns=[column for column in FEATURE_COLUMNS if column in full_df.columns])
    enriched = enriched.merge(feature_frame, on="match_id", how="left")
    enriched.to_csv(OUTPUT_PATH, index=False)

    populated_rows = int(enriched["team_a_top11_avg_minutes_last5"].notna().sum())
    missing_feature_rows = int(enriched["team_a_top11_avg_minutes_last5"].isna().sum())
    print(f"Wrote {len(enriched)} rows to {OUTPUT_PATH}")
    print(f"Rows populated with player-status features: {populated_rows}")
    print(
        "Rows without prior player-status history "
        f"(expected for tournament openers or first-use teams): {missing_feature_rows}"
    )
    if skipped_match_ids:
        preview = ", ".join(str(match_id) for match_id in skipped_match_ids[:10])
        print(
            f"Skipped {len(skipped_match_ids)} matches because their event files "
            f"were not yet usable. First skipped match_ids: {preview}"
        )


if __name__ == "__main__":
    main()
