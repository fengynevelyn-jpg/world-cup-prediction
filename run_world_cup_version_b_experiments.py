#!/usr/bin/env python3
"""Run version-B World Cup experiments with rolling walk-forward evaluation.

Version B means we explicitly allow in-tournament rolling state:
- pre-match Elo / FIFA / recent form
- player-state signals accumulated from prior matches
- squad value as a mostly static prior

The evaluation here is stricter than our earlier single split:
- sort matches by date
- train on all earlier World Cup matches
- predict the next match
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from train_world_cup_baseline import (
    SoftmaxRegression,
    TARGET_COLUMN,
    expand_probabilities,
    multiclass_brier,
    multiclass_log_loss,
)


BASE_DIR = Path("/Users/evelynfeng/Documents/gaming")
INPUT_PATH = BASE_DIR / "world_cup_matches_features_elo_form.csv"
SUMMARY_CSV_PATH = BASE_DIR / "world_cup_version_b_experiment_results.csv"
SUMMARY_MD_PATH = BASE_DIR / "world_cup_version_b_experiment_results.md"
PREDICTIONS_PATH = BASE_DIR / "world_cup_version_b_walk_forward_predictions.csv"
STAGE_BREAKDOWN_CSV_PATH = BASE_DIR / "world_cup_version_b_stage_breakdown.csv"
STAGE_BREAKDOWN_MD_PATH = BASE_DIR / "world_cup_version_b_stage_breakdown.md"
STRENGTH_BREAKDOWN_CSV_PATH = BASE_DIR / "world_cup_version_b_strength_breakdown.csv"
STRENGTH_BREAKDOWN_MD_PATH = BASE_DIR / "world_cup_version_b_strength_breakdown.md"
EVAL_START_DATE = pd.Timestamp("2022-11-20")

BASE_NUMERIC_FEATURES = [
    "elo_diff",
    "fifa_rank_diff",
    "last5_points_diff",
    "goals_for_diff",
    "goals_against_diff",
    "last5_goal_diff_gap",
    "rest_days_diff",
]
PLAYER_STATE_FEATURES = [
    "top11_rating_diff",
    "top11_minutes_diff",
]
XG_FEATURES = [
    "xg_diff",
    "xga_diff",
]
SQUAD_VALUE_FEATURES = [
    "squad_value_diff",
]
FULL_PLAYER_STATE_FEATURES = [
    "attack_core_form_diff",
    "gk_form_diff",
    "starts_stability_diff",
    "key_absence_diff",
]
CATEGORICAL_FEATURES = [
    "stage",
    "confederation_pair",
]
SPARSE_NUMERIC_FEATURES = set(
    PLAYER_STATE_FEATURES + XG_FEATURES + FULL_PLAYER_STATE_FEATURES + SQUAD_VALUE_FEATURES
)
MIN_TRAIN_ROWS = 24
KNOCKOUT_STAGES = {"round_of_16", "quarterfinal", "semifinal", "third_place", "final"}


@dataclass(frozen=True)
class FeaturePreset:
    name: str
    description: str
    numeric_features: list[str]
    categorical_features: list[str]


FEATURE_PRESETS = [
    FeaturePreset(
        name="base_form",
        description="Elo + FIFA + recent form + stage/confederation",
        numeric_features=BASE_NUMERIC_FEATURES,
        categorical_features=CATEGORICAL_FEATURES,
    ),
    FeaturePreset(
        name="player_state",
        description="Base + top11 rating/minutes",
        numeric_features=BASE_NUMERIC_FEATURES + PLAYER_STATE_FEATURES,
        categorical_features=CATEGORICAL_FEATURES,
    ),
    FeaturePreset(
        name="player_state_xg",
        description="Base + top11 rating/minutes + rolling xG/xGA",
        numeric_features=BASE_NUMERIC_FEATURES + PLAYER_STATE_FEATURES + XG_FEATURES,
        categorical_features=CATEGORICAL_FEATURES,
    ),
    FeaturePreset(
        name="player_state_squad_value",
        description="Player-state preset + squad value",
        numeric_features=BASE_NUMERIC_FEATURES + PLAYER_STATE_FEATURES + SQUAD_VALUE_FEATURES,
        categorical_features=CATEGORICAL_FEATURES,
    ),
    FeaturePreset(
        name="player_state_squad_value_xg",
        description="Player-state + squad value + rolling xG/xGA",
        numeric_features=BASE_NUMERIC_FEATURES + PLAYER_STATE_FEATURES + SQUAD_VALUE_FEATURES + XG_FEATURES,
        categorical_features=CATEGORICAL_FEATURES,
    ),
    FeaturePreset(
        name="all_signals",
        description="Player-state + squad value + rolling xG/xGA + all current player-state fields",
        numeric_features=BASE_NUMERIC_FEATURES + PLAYER_STATE_FEATURES + SQUAD_VALUE_FEATURES + XG_FEATURES + FULL_PLAYER_STATE_FEATURES,
        categorical_features=CATEGORICAL_FEATURES,
    ),
]


def standardize_train_eval(
    x_train: np.ndarray,
    x_eval: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    means = x_train.mean(axis=0)
    stds = x_train.std(axis=0)
    stds[stds == 0] = 1.0
    return (x_train - means) / stds, (x_eval - means) / stds


def build_feature_matrices(
    train_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    preset: FeaturePreset,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    numeric_train_parts: list[pd.DataFrame] = []
    numeric_eval_parts: list[pd.DataFrame] = []
    feature_names: list[str] = []

    for column in preset.numeric_features:
        if column not in train_df.columns:
            continue

        train_col = pd.to_numeric(train_df[column], errors="coerce")
        eval_col = pd.to_numeric(eval_df[column], errors="coerce")
        median = float(train_col.median()) if train_col.notna().any() else 0.0

        numeric_train_parts.append(train_col.fillna(median).to_frame(column))
        numeric_eval_parts.append(eval_col.fillna(median).to_frame(column))
        feature_names.append(column)

        if column in SPARSE_NUMERIC_FEATURES:
            indicator_name = f"{column}_missing"
            numeric_train_parts.append(train_col.isna().astype(float).to_frame(indicator_name))
            numeric_eval_parts.append(eval_col.isna().astype(float).to_frame(indicator_name))
            feature_names.append(indicator_name)

    if not numeric_train_parts:
        raise ValueError(f"No numeric features available for preset: {preset.name}")

    train_parts = [pd.concat(numeric_train_parts, axis=1)]
    eval_parts = [pd.concat(numeric_eval_parts, axis=1)]

    for column in preset.categorical_features:
        if column not in train_df.columns:
            continue

        train_encoded = pd.get_dummies(train_df[column].fillna("unknown"), prefix=column).astype(float)
        eval_encoded = pd.get_dummies(eval_df[column].fillna("unknown"), prefix=column).astype(float)
        eval_encoded = eval_encoded.reindex(columns=train_encoded.columns, fill_value=0.0)

        train_parts.append(train_encoded)
        eval_parts.append(eval_encoded)
        feature_names.extend(train_encoded.columns.tolist())

    x_train = pd.concat(train_parts, axis=1).to_numpy(dtype=float)
    x_eval = pd.concat(eval_parts, axis=1).to_numpy(dtype=float)
    return x_train, x_eval, feature_names


def walk_forward_evaluate(df: pd.DataFrame, preset: FeaturePreset) -> tuple[dict[str, object], list[dict[str, object]]]:
    eval_indices = df.index[df["match_date"] >= EVAL_START_DATE].tolist()
    if not eval_indices:
        raise ValueError("No matches found in the evaluation window.")

    start_idx = int(eval_indices[0])
    if start_idx < MIN_TRAIN_ROWS:
        raise ValueError("Not enough historical rows before the evaluation window.")

    prediction_rows: list[dict[str, object]] = []

    for eval_idx in eval_indices:
        train_df = df.iloc[:eval_idx].copy()
        eval_df = df.iloc[[eval_idx]].copy()

        observed_labels = sorted(int(label) for label in pd.unique(train_df[TARGET_COLUMN]))
        if len(observed_labels) < 3:
            raise ValueError(
                f"Training rows before eval index {eval_idx} do not contain all 3 outcome classes."
            )

        label_to_index = {label: idx for idx, label in enumerate(observed_labels)}
        y_train = train_df[TARGET_COLUMN].map(label_to_index).to_numpy(dtype=int)
        x_train, x_eval, feature_names = build_feature_matrices(train_df, eval_df, preset)
        x_train, x_eval = standardize_train_eval(x_train, x_eval)

        model = SoftmaxRegression()
        model.fit(x_train, y_train)

        probs_observed = model.predict_proba(x_eval)
        probs_full = expand_probabilities(probs_observed, observed_labels)
        predicted_label = int(np.argmax(probs_full[0]))
        true_label = int(eval_df.iloc[0][TARGET_COLUMN])

        prediction_rows.append(
            {
                "preset": preset.name,
                "match_date": eval_df.iloc[0]["match_date"],
                "stage": eval_df.iloc[0].get("stage"),
                "stage_bucket": (
                    "knockout" if eval_df.iloc[0].get("stage") in KNOCKOUT_STAGES else "group"
                ),
                "elo_diff": float(eval_df.iloc[0].get("elo_diff")),
                "abs_elo_diff": abs(float(eval_df.iloc[0].get("elo_diff"))),
                "team_a": eval_df.iloc[0].get("team_a"),
                "team_b": eval_df.iloc[0].get("team_b"),
                "true_result_90m": true_label,
                "predicted_result_90m": predicted_label,
                "prob_team_a_win": float(probs_full[0, 0]),
                "prob_draw": float(probs_full[0, 1]),
                "prob_team_b_win": float(probs_full[0, 2]),
                "train_rows": len(train_df),
                "feature_count": len(feature_names),
            }
        )

    predictions = pd.DataFrame(prediction_rows)
    if predictions.empty:
        raise ValueError(f"No predictions were produced for preset: {preset.name}")

    y_true = np.eye(3)[predictions["true_result_90m"].to_numpy(dtype=int)]
    probs = predictions[["prob_team_a_win", "prob_draw", "prob_team_b_win"]].to_numpy(dtype=float)
    predicted = predictions["predicted_result_90m"].to_numpy(dtype=int)
    actual = predictions["true_result_90m"].to_numpy(dtype=int)

    summary = {
        "preset": preset.name,
        "description": preset.description,
        "start_eval_index": start_idx,
        "train_rows_before_first_prediction": start_idx,
        "evaluated_matches": len(predictions),
        "accuracy": float((predicted == actual).mean()),
        "log_loss": multiclass_log_loss(y_true, probs),
        "brier": multiclass_brier(y_true, probs),
        "mean_train_rows": float(predictions["train_rows"].mean()),
        "feature_count": int(predictions["feature_count"].iloc[0]),
    }
    return summary, prediction_rows


def summarize_prediction_subset(predictions: pd.DataFrame) -> dict[str, float | int]:
    y_true = np.eye(3)[predictions["true_result_90m"].to_numpy(dtype=int)]
    probs = predictions[["prob_team_a_win", "prob_draw", "prob_team_b_win"]].to_numpy(dtype=float)
    predicted = predictions["predicted_result_90m"].to_numpy(dtype=int)
    actual = predictions["true_result_90m"].to_numpy(dtype=int)
    return {
        "evaluated_matches": int(len(predictions)),
        "accuracy": float((predicted == actual).mean()),
        "log_loss": multiclass_log_loss(y_true, probs),
        "brier": multiclass_brier(y_true, probs),
    }


def build_stage_breakdown(predictions_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for (preset, stage_bucket), subset in predictions_df.groupby(["preset", "stage_bucket"], sort=True):
        metrics = summarize_prediction_subset(subset)
        rows.append(
            {
                "preset": preset,
                "breakdown_type": "stage_bucket",
                "segment": stage_bucket,
                **metrics,
            }
        )

    for (preset, stage), subset in predictions_df.groupby(["preset", "stage"], sort=True):
        metrics = summarize_prediction_subset(subset)
        rows.append(
            {
                "preset": preset,
                "breakdown_type": "stage",
                "segment": stage,
                **metrics,
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["breakdown_type", "preset", "segment"],
        kind="stable",
    ).reset_index(drop=True)


def assign_strength_bucket(predictions_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    q25 = float(predictions_df["abs_elo_diff"].quantile(0.25))
    q75 = float(predictions_df["abs_elo_diff"].quantile(0.75))

    def bucket(value: float) -> str:
        if value <= q25:
            return "close"
        if value <= q75:
            return "medium"
        return "lopsided"

    enriched = predictions_df.copy()
    enriched["strength_bucket"] = enriched["abs_elo_diff"].map(bucket)
    return enriched, {"q25": q25, "q75": q75}


def build_strength_breakdown(predictions_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (preset, strength_bucket), subset in predictions_df.groupby(["preset", "strength_bucket"], sort=True):
        metrics = summarize_prediction_subset(subset)
        rows.append(
            {
                "preset": preset,
                "strength_bucket": strength_bucket,
                **metrics,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["preset", "strength_bucket"],
        kind="stable",
    ).reset_index(drop=True)


def write_markdown_summary(summary_df: pd.DataFrame) -> None:
    lines = [
        "# 世界杯版本 B 实验结果",
        "",
        "更新时间：2026-06-10",
        "",
        "口径：用 `2018` 世界杯作为历史训练底座，并在 `2022-11-20` 到 `2022-12-18` 之间逐场滚动训练和预测；允许使用世界杯进行中的滚动状态特征。",
        "",
        "| preset | description | evaluated_matches | accuracy | log_loss | brier | feature_count |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary_df.itertuples(index=False):
        lines.append(
            f"| {row.preset} | {row.description} | {row.evaluated_matches} | "
            f"{row.accuracy:.3f} | {row.log_loss:.3f} | {row.brier:.3f} | {row.feature_count} |"
        )

    best_row = summary_df.sort_values(["log_loss", "brier", "accuracy"], ascending=[True, True, False]).iloc[0]
    lines.extend(
        [
            "",
            "## 当前判断",
            "",
            f"- 如果版本 B 以概率质量为主，当前最稳的 preset 是 `{best_row['preset']}`。",
            f"- 它的指标是：`accuracy {best_row['accuracy']:.3f}`，`log loss {best_row['log_loss']:.3f}`，`Brier {best_row['brier']:.3f}`。",
        ]
    )

    SUMMARY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_stage_breakdown_markdown(stage_df: pd.DataFrame) -> None:
    lines = [
        "# 世界杯版本 B 分阶段结果",
        "",
        "更新时间：2026-06-10",
        "",
        "口径：用 `2018` 训练底座，对 `2022` 比赛逐场滚动预测；按 `group/knockout` 和具体阶段拆分。",
        "",
        "## Group vs Knockout",
        "",
        "| preset | segment | evaluated_matches | accuracy | log_loss | brier |",
        "|---|---|---:|---:|---:|---:|",
    ]

    bucket_df = stage_df[stage_df["breakdown_type"].eq("stage_bucket")]
    for row in bucket_df.itertuples(index=False):
        lines.append(
            f"| {row.preset} | {row.segment} | {row.evaluated_matches} | "
            f"{row.accuracy:.3f} | {row.log_loss:.3f} | {row.brier:.3f} |"
        )

    lines.extend(
        [
            "",
            "## By Stage",
            "",
            "| preset | stage | evaluated_matches | accuracy | log_loss | brier |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )

    stage_only_df = stage_df[stage_df["breakdown_type"].eq("stage")]
    for row in stage_only_df.itertuples(index=False):
        lines.append(
            f"| {row.preset} | {row.segment} | {row.evaluated_matches} | "
            f"{row.accuracy:.3f} | {row.log_loss:.3f} | {row.brier:.3f} |"
        )

    STAGE_BREAKDOWN_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_strength_breakdown_markdown(
    strength_df: pd.DataFrame,
    strength_thresholds: dict[str, float],
) -> None:
    lines = [
        "# 世界杯版本 B 强弱分层结果",
        "",
        "更新时间：2026-06-10",
        "",
        "口径：按 `2022` 评估窗口里的 `abs(elo_diff)` 分位数分桶。",
        "",
        f"- `close`: `abs(elo_diff) <= {strength_thresholds['q25']:.3f}`",
        f"- `medium`: `{strength_thresholds['q25']:.3f} < abs(elo_diff) <= {strength_thresholds['q75']:.3f}`",
        f"- `lopsided`: `abs(elo_diff) > {strength_thresholds['q75']:.3f}`",
        "",
        "| preset | strength_bucket | evaluated_matches | accuracy | log_loss | brier |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in strength_df.itertuples(index=False):
        lines.append(
            f"| {row.preset} | {row.strength_bucket} | {row.evaluated_matches} | "
            f"{row.accuracy:.3f} | {row.log_loss:.3f} | {row.brier:.3f} |"
        )

    STRENGTH_BREAKDOWN_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    df = pd.read_csv(INPUT_PATH, parse_dates=["match_date"])
    df = df.sort_values("match_date", kind="stable").reset_index(drop=True)
    df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(int)

    summary_rows: list[dict[str, object]] = []
    all_predictions: list[dict[str, object]] = []
    for preset in FEATURE_PRESETS:
        summary, prediction_rows = walk_forward_evaluate(df, preset)
        summary_rows.append(summary)
        all_predictions.extend(prediction_rows)

    summary_df = pd.DataFrame(summary_rows).sort_values(
        ["log_loss", "brier", "accuracy"],
        ascending=[True, True, False],
        kind="stable",
    )
    predictions_df = pd.DataFrame(all_predictions).sort_values(
        ["preset", "match_date", "team_a", "team_b"],
        kind="stable",
    )
    predictions_df, strength_thresholds = assign_strength_bucket(predictions_df)

    summary_df.to_csv(SUMMARY_CSV_PATH, index=False)
    predictions_df.to_csv(PREDICTIONS_PATH, index=False)
    stage_breakdown_df = build_stage_breakdown(predictions_df)
    stage_breakdown_df.to_csv(STAGE_BREAKDOWN_CSV_PATH, index=False)
    strength_breakdown_df = build_strength_breakdown(predictions_df)
    strength_breakdown_df.to_csv(STRENGTH_BREAKDOWN_CSV_PATH, index=False)
    write_markdown_summary(summary_df)
    write_stage_breakdown_markdown(stage_breakdown_df)
    write_strength_breakdown_markdown(strength_breakdown_df, strength_thresholds)

    print(f"Wrote summary CSV to {SUMMARY_CSV_PATH}")
    print(f"Wrote summary Markdown to {SUMMARY_MD_PATH}")
    print(f"Wrote walk-forward predictions to {PREDICTIONS_PATH}")
    print(f"Wrote stage breakdown CSV to {STAGE_BREAKDOWN_CSV_PATH}")
    print(f"Wrote stage breakdown Markdown to {STAGE_BREAKDOWN_MD_PATH}")
    print(f"Wrote strength breakdown CSV to {STRENGTH_BREAKDOWN_CSV_PATH}")
    print(f"Wrote strength breakdown Markdown to {STRENGTH_BREAKDOWN_MD_PATH}")
    print()
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
