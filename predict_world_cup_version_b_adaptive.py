#!/usr/bin/env python3
"""Predict World Cup outcomes with the current adaptive version-B strategy."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from run_world_cup_version_b_experiments import (
    BASE_NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    PLAYER_STATE_FEATURES,
    SQUAD_VALUE_FEATURES,
    XG_FEATURES,
    FeaturePreset,
    build_feature_matrices,
    standardize_train_eval,
)
from train_world_cup_baseline import OUTCOME_LABELS, SoftmaxRegression, TARGET_COLUMN, expand_probabilities


DEFAULT_INPUT = Path("/Users/evelynfeng/Documents/gaming/world_cup_matches_features_elo_form.csv")
DEFAULT_OUTPUT = Path("/Users/evelynfeng/Documents/gaming/world_cup_version_b_adaptive_predictions.csv")

# Fixed thresholds from the current 2022 version-B calibration run.
CLOSE_THRESHOLD = 75.735
LOPSIDED_THRESHOLD = 218.435


STRATEGY_PRESETS = {
    "adaptive_base_svg": {
        "close": FeaturePreset(
            name="base_form",
            description="Elo + FIFA + recent form + stage/confederation",
            numeric_features=BASE_NUMERIC_FEATURES,
            categorical_features=CATEGORICAL_FEATURES,
        ),
        "medium": FeaturePreset(
            name="player_state_squad_value",
            description="Player-state preset + squad value",
            numeric_features=BASE_NUMERIC_FEATURES + PLAYER_STATE_FEATURES + SQUAD_VALUE_FEATURES,
            categorical_features=CATEGORICAL_FEATURES,
        ),
        "lopsided": FeaturePreset(
            name="base_form",
            description="Elo + FIFA + recent form + stage/confederation",
            numeric_features=BASE_NUMERIC_FEATURES,
            categorical_features=CATEGORICAL_FEATURES,
        ),
    },
    "adaptive_base_svgxg": {
        "close": FeaturePreset(
            name="base_form",
            description="Elo + FIFA + recent form + stage/confederation",
            numeric_features=BASE_NUMERIC_FEATURES,
            categorical_features=CATEGORICAL_FEATURES,
        ),
        "medium": FeaturePreset(
            name="player_state_squad_value_xg",
            description="Player-state + squad value + rolling xG/xGA",
            numeric_features=BASE_NUMERIC_FEATURES + PLAYER_STATE_FEATURES + SQUAD_VALUE_FEATURES + XG_FEATURES,
            categorical_features=CATEGORICAL_FEATURES,
        ),
        "lopsided": FeaturePreset(
            name="base_form",
            description="Elo + FIFA + recent form + stage/confederation",
            numeric_features=BASE_NUMERIC_FEATURES,
            categorical_features=CATEGORICAL_FEATURES,
        ),
    },
    "adaptive_best_bucket": {
        "close": FeaturePreset(
            name="player_state_squad_value",
            description="Player-state preset + squad value",
            numeric_features=BASE_NUMERIC_FEATURES + PLAYER_STATE_FEATURES + SQUAD_VALUE_FEATURES,
            categorical_features=CATEGORICAL_FEATURES,
        ),
        "medium": FeaturePreset(
            name="player_state_squad_value_xg",
            description="Player-state + squad value + rolling xG/xGA",
            numeric_features=BASE_NUMERIC_FEATURES + PLAYER_STATE_FEATURES + SQUAD_VALUE_FEATURES + XG_FEATURES,
            categorical_features=CATEGORICAL_FEATURES,
        ),
        "lopsided": FeaturePreset(
            name="player_state",
            description="Base + top11 rating/minutes",
            numeric_features=BASE_NUMERIC_FEATURES + PLAYER_STATE_FEATURES,
            categorical_features=CATEGORICAL_FEATURES,
        ),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Predict World Cup matches with the current adaptive version-B strategy."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help="Feature table to read.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Where to write prediction rows.",
    )
    parser.add_argument(
        "--strategy",
        default="adaptive_base_svgxg",
        choices=sorted(STRATEGY_PRESETS),
        help="Adaptive strategy to apply.",
    )
    return parser.parse_args()


def strength_bucket(elo_diff: float) -> str:
    abs_diff = abs(float(elo_diff))
    if abs_diff <= CLOSE_THRESHOLD:
        return "close"
    if abs_diff <= LOPSIDED_THRESHOLD:
        return "medium"
    return "lopsided"


def prediction_indices(df: pd.DataFrame) -> list[int]:
    if TARGET_COLUMN in df.columns:
        missing = df.index[df[TARGET_COLUMN].isna()].tolist()
        if missing:
            return [int(idx) for idx in missing]
    return [len(df) - 1]


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    df = pd.read_csv(input_path, parse_dates=["match_date"])
    df = df.sort_values("match_date", kind="stable").reset_index(drop=True)

    if TARGET_COLUMN not in df.columns:
        df[TARGET_COLUMN] = np.nan

    rows_to_predict = prediction_indices(df)
    strategy = STRATEGY_PRESETS[args.strategy]

    output_rows: list[dict[str, object]] = []

    for eval_idx in rows_to_predict:
        eval_row = df.iloc[[eval_idx]].copy()
        prior_rows = df.iloc[:eval_idx].copy()
        train_df = prior_rows[prior_rows[TARGET_COLUMN].notna()].copy()

        if len(train_df) < 24:
            raise ValueError(
                f"Not enough labeled history before row {eval_idx}. Need at least 24 prior labeled matches."
            )

        observed_labels = sorted(int(label) for label in pd.unique(train_df[TARGET_COLUMN]))
        if len(observed_labels) < 3:
            raise ValueError(
                f"Training data before row {eval_idx} does not contain all 3 outcome classes."
            )

        bucket = strength_bucket(float(eval_row.iloc[0]["elo_diff"]))
        preset = strategy[bucket]

        label_to_index = {label: idx for idx, label in enumerate(observed_labels)}
        y_train = train_df[TARGET_COLUMN].astype(int).map(label_to_index).to_numpy(dtype=int)

        x_train, x_eval, feature_names = build_feature_matrices(train_df, eval_row, preset)
        x_train, x_eval = standardize_train_eval(x_train, x_eval)

        model = SoftmaxRegression()
        model.fit(x_train, y_train)

        probs_observed = model.predict_proba(x_eval)
        probs_full = expand_probabilities(probs_observed, observed_labels)
        predicted_result = int(np.argmax(probs_full[0]))

        result = eval_row.iloc[0].to_dict()
        result["adaptive_strategy"] = args.strategy
        result["strength_bucket"] = bucket
        result["selected_preset"] = preset.name
        result["selected_feature_count"] = len(feature_names)
        result["train_rows"] = len(train_df)
        result["predicted_result_90m"] = predicted_result
        result["predicted_result_label"] = OUTCOME_LABELS[predicted_result]
        result["prob_team_a_win"] = float(probs_full[0, 0])
        result["prob_draw"] = float(probs_full[0, 1])
        result["prob_team_b_win"] = float(probs_full[0, 2])
        output_rows.append(result)

    output_df = pd.DataFrame(output_rows)
    output_df.to_csv(output_path, index=False)

    print(f"Strategy: {args.strategy}")
    print(f"Predicted rows: {len(output_df)}")
    print(f"Output written to: {output_path}")
    if not output_df.empty:
        preview_cols = [
            "match_date",
            "team_a",
            "team_b",
            "strength_bucket",
            "selected_preset",
            "predicted_result_label",
            "prob_team_a_win",
            "prob_draw",
            "prob_team_b_win",
        ]
        print()
        print(output_df[preview_cols].to_string(index=False))


if __name__ == "__main__":
    main()
