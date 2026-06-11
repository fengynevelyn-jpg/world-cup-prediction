#!/usr/bin/env python3
"""Evaluate adaptive version-B strategies built from strength buckets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from train_world_cup_baseline import multiclass_brier, multiclass_log_loss


BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "world_cup_version_b_walk_forward_predictions.csv"
SUMMARY_CSV_PATH = BASE_DIR / "world_cup_version_b_adaptive_results.csv"
SUMMARY_MD_PATH = BASE_DIR / "world_cup_version_b_adaptive_results.md"
PREDICTIONS_CSV_PATH = BASE_DIR / "world_cup_version_b_adaptive_predictions.csv"

PROBABILITY_COLUMNS = ["prob_team_a_win", "prob_draw", "prob_team_b_win"]


@dataclass(frozen=True)
class AdaptiveStrategy:
    name: str
    description: str
    close_preset: str
    medium_preset: str
    lopsided_preset: str


STRATEGIES = [
    AdaptiveStrategy(
        name="adaptive_base_svg",
        description="close/lopsided 用 base_form，medium 用 player_state_squad_value",
        close_preset="base_form",
        medium_preset="player_state_squad_value",
        lopsided_preset="base_form",
    ),
    AdaptiveStrategy(
        name="adaptive_base_svgxg",
        description="close/lopsided 用 base_form，medium 用 player_state_squad_value_xg",
        close_preset="base_form",
        medium_preset="player_state_squad_value_xg",
        lopsided_preset="base_form",
    ),
    AdaptiveStrategy(
        name="adaptive_best_bucket",
        description="每个强弱桶单独拿当前 log loss 最优 preset",
        close_preset="player_state_squad_value",
        medium_preset="player_state_squad_value_xg",
        lopsided_preset="player_state",
    ),
]


def evaluate_subset(df: pd.DataFrame) -> tuple[float, float, float]:
    y_true = np.eye(3)[df["true_result_90m"].astype(int).to_numpy()]
    probs = df[PROBABILITY_COLUMNS].to_numpy(dtype=float)
    predicted = df["predicted_result_90m"].astype(int).to_numpy()
    actual = df["true_result_90m"].astype(int).to_numpy()
    accuracy = float((predicted == actual).mean())
    log_loss = multiclass_log_loss(y_true, probs)
    brier = multiclass_brier(y_true, probs)
    return accuracy, log_loss, brier


def materialize_strategy(predictions: pd.DataFrame, strategy: AdaptiveStrategy) -> pd.DataFrame:
    mapping = {
        "close": strategy.close_preset,
        "medium": strategy.medium_preset,
        "lopsided": strategy.lopsided_preset,
    }
    parts: list[pd.DataFrame] = []
    for bucket, preset in mapping.items():
        subset = predictions[
            predictions["strength_bucket"].eq(bucket) & predictions["preset"].eq(preset)
        ].copy()
        subset["adaptive_strategy"] = strategy.name
        subset["selected_preset"] = preset
        parts.append(subset)

    materialized = pd.concat(parts, ignore_index=True)
    return materialized.sort_values(["match_date", "team_a", "team_b"], kind="stable").reset_index(drop=True)


def write_markdown(summary_df: pd.DataFrame) -> None:
    lines = [
        "# 世界杯版本 B 自适应策略结果",
        "",
        "更新时间：2026-06-10",
        "",
        "口径：先按 `abs(elo_diff)` 把比赛分成 `close / medium / lopsided`，再为每个桶选择不同 preset。",
        "",
        "| strategy | description | close | medium | lopsided | evaluated_matches | accuracy | log_loss | brier |",
        "|---|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in summary_df.itertuples(index=False):
        lines.append(
            f"| {row.strategy} | {row.description} | {row.close_preset} | {row.medium_preset} | "
            f"{row.lopsided_preset} | {row.evaluated_matches} | {row.accuracy:.3f} | "
            f"{row.log_loss:.3f} | {row.brier:.3f} |"
        )

    best = summary_df.sort_values(["log_loss", "brier", "accuracy"], ascending=[True, True, False]).iloc[0]
    lines.extend(
        [
            "",
            "## 当前判断",
            "",
            f"- 当前最稳的自适应策略是 `{best['strategy']}`。",
            f"- 它的指标是：`accuracy {best['accuracy']:.3f}`，`log loss {best['log_loss']:.3f}`，`Brier {best['brier']:.3f}`。",
        ]
    )
    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    predictions = pd.read_csv(INPUT_PATH, parse_dates=["match_date"])
    all_materialized: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []

    for strategy in STRATEGIES:
        materialized = materialize_strategy(predictions, strategy)
        accuracy, log_loss, brier = evaluate_subset(materialized)
        all_materialized.append(materialized)
        summary_rows.append(
            {
                "strategy": strategy.name,
                "description": strategy.description,
                "close_preset": strategy.close_preset,
                "medium_preset": strategy.medium_preset,
                "lopsided_preset": strategy.lopsided_preset,
                "evaluated_matches": len(materialized),
                "accuracy": accuracy,
                "log_loss": log_loss,
                "brier": brier,
            }
        )

    summary_df = pd.DataFrame(summary_rows).sort_values(
        ["log_loss", "brier", "accuracy"],
        ascending=[True, True, False],
        kind="stable",
    )
    materialized_df = pd.concat(all_materialized, ignore_index=True).sort_values(
        ["adaptive_strategy", "match_date", "team_a", "team_b"],
        kind="stable",
    )

    summary_df.to_csv(SUMMARY_CSV_PATH, index=False)
    materialized_df.to_csv(PREDICTIONS_CSV_PATH, index=False)
    write_markdown(summary_df)

    print(f"Wrote adaptive summary CSV to {SUMMARY_CSV_PATH}")
    print(f"Wrote adaptive summary Markdown to {SUMMARY_MD_PATH}")
    print(f"Wrote adaptive predictions CSV to {PREDICTIONS_CSV_PATH}")
    print()
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
