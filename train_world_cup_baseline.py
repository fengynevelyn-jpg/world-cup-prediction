#!/usr/bin/env python3
"""Train a minimal World Cup match outcome baseline from CSV.

This script is intentionally lightweight:
- reads the schema we defined for the World Cup experiment
- uses only pandas + numpy
- trains a multinomial logistic regression with gradient descent
- writes per-match predicted probabilities to a CSV
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


TARGET_COLUMN = "target_result_90m"
OUTCOME_LABELS = {
    0: "team_a_win",
    1: "draw",
    2: "team_b_win",
}

PREFERRED_NUMERIC_FEATURES = [
    "elo_diff",
    "fifa_rank_diff",
    "squad_value_diff",
    "last5_points_diff",
    "goals_for_diff",
    "goals_against_diff",
    "last5_goal_diff_gap",
    # Keep the player-status layer conservative by default.
    # These two fields currently have the best probability-quality tradeoff
    # on our small 2018/2022 validation split.
    "top11_rating_diff",
    "top11_minutes_diff",
    "rest_days_diff",
]

OPTIONAL_CATEGORICAL_FEATURES = [
    "stage",
    "confederation_pair",
]


@dataclass
class FeatureBundle:
    matrix: np.ndarray
    feature_names: list[str]


class SoftmaxRegression:
    def __init__(
        self,
        learning_rate: float = 0.05,
        epochs: int = 2500,
        l2: float = 1e-3,
        seed: int = 42,
    ) -> None:
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.l2 = l2
        self.rng = np.random.default_rng(seed)
        self.weights: np.ndarray | None = None
        self.bias: np.ndarray | None = None

    def fit(self, features: np.ndarray, labels: np.ndarray) -> None:
        n_samples, n_features = features.shape
        classes = int(labels.max()) + 1
        self.weights = self.rng.normal(0.0, 0.01, size=(n_features, classes))
        self.bias = np.zeros(classes, dtype=float)

        y_one_hot = np.eye(classes)[labels]

        for epoch in range(self.epochs):
            logits = features @ self.weights + self.bias
            probs = softmax(logits)

            error = probs - y_one_hot
            grad_w = (features.T @ error) / n_samples + self.l2 * self.weights
            grad_b = error.mean(axis=0)

            self.weights -= self.learning_rate * grad_w
            self.bias -= self.learning_rate * grad_b

            # A lightweight stability check every few hundred iterations.
            if epoch % 500 == 0:
                loss = multiclass_log_loss(y_one_hot, probs)
                if not np.isfinite(loss):
                    raise RuntimeError("Training diverged. Try a smaller learning rate.")

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        if self.weights is None or self.bias is None:
            raise RuntimeError("Model has not been fitted yet.")
        logits = features @ self.weights + self.bias
        return softmax(logits)

    def predict(self, features: np.ndarray) -> np.ndarray:
        return self.predict_proba(features).argmax(axis=1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a minimal World Cup outcome baseline from CSV."
    )
    parser.add_argument(
        "--input",
        default="world_cup_matches_example.csv",
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "--output",
        default="baseline_predictions.csv",
        help="Where to write the prediction CSV.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=2500,
        help="Number of gradient descent epochs.",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=0.05,
        help="Learning rate for gradient descent.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    df = pd.read_csv(input_path)
    if df.empty:
        print("Input CSV is empty.", file=sys.stderr)
        return 1

    if TARGET_COLUMN not in df.columns:
        print(
            f"Missing required target column: {TARGET_COLUMN}.",
            file=sys.stderr,
        )
        return 1

    if "match_date" in df.columns:
        df["match_date"] = pd.to_datetime(df["match_date"], errors="coerce")
        df = df.sort_values("match_date", kind="stable").reset_index(drop=True)

    if df[TARGET_COLUMN].isna().any():
        print(
            f"Column {TARGET_COLUMN} contains missing values. "
            "Please fill each row with 0, 1, or 2.",
            file=sys.stderr,
        )
        return 1

    observed_labels = sorted(int(label) for label in pd.unique(df[TARGET_COLUMN]))
    if len(observed_labels) < 2:
        print(
            "Need at least 2 observed outcome classes in the dataset to train a model. "
            "Right now the file only contains one class.",
            file=sys.stderr,
        )
        return 1

    if len(df) < 6:
        print(
            "Need at least 6 matches to train this baseline meaningfully. "
            "Add more 2018/2022 rows and try again.",
            file=sys.stderr,
        )
        return 1

    label_to_index = {label: idx for idx, label in enumerate(observed_labels)}
    index_to_label = {idx: label for label, idx in label_to_index.items()}
    y = df[TARGET_COLUMN].map(label_to_index).to_numpy(dtype=int)

    features = build_features(df)
    split = choose_split(len(df), len(observed_labels))
    train_idx, eval_idx = split

    x_train = features.matrix[train_idx]
    x_eval = features.matrix[eval_idx]
    y_train = y[train_idx]
    y_eval = y[eval_idx]

    x_train, x_eval = standardize_train_eval(x_train, x_eval)

    model = SoftmaxRegression(learning_rate=args.lr, epochs=args.epochs)
    model.fit(x_train, y_train)

    eval_probs_observed = model.predict_proba(x_eval)
    eval_pred_observed = eval_probs_observed.argmax(axis=1)

    eval_probs_full = expand_probabilities(eval_probs_observed, observed_labels)
    eval_pred_labels = np.array([index_to_label[idx] for idx in eval_pred_observed], dtype=int)

    eval_accuracy = float((eval_pred_observed == y_eval).mean())
    eval_log_loss = multiclass_log_loss(np.eye(len(observed_labels))[y_eval], eval_probs_observed)
    eval_brier = multiclass_brier(np.eye(len(observed_labels))[y_eval], eval_probs_observed)

    predictions = df.iloc[eval_idx].copy()
    predictions["predicted_result_90m"] = eval_pred_labels
    predictions["predicted_result_label"] = predictions["predicted_result_90m"].map(OUTCOME_LABELS)
    predictions["prob_team_a_win"] = eval_probs_full[:, 0]
    predictions["prob_draw"] = eval_probs_full[:, 1]
    predictions["prob_team_b_win"] = eval_probs_full[:, 2]
    predictions.to_csv(output_path, index=False)

    print(f"Loaded {len(df)} matches from {input_path}")
    print(f"Using {len(features.feature_names)} features")
    print("Features:", ", ".join(features.feature_names))
    print()
    print(f"Train rows: {len(train_idx)}")
    print(f"Eval rows: {len(eval_idx)}")
    print(f"Eval accuracy: {eval_accuracy:.3f}")
    print(f"Eval log loss: {eval_log_loss:.3f}")
    print(f"Eval Brier score: {eval_brier:.3f}")
    print(f"Predictions written to: {output_path}")

    return 0


def build_features(df: pd.DataFrame) -> FeatureBundle:
    numeric_columns = [
        column for column in PREFERRED_NUMERIC_FEATURES if column in df.columns
    ]

    if not numeric_columns:
        numeric_columns = [
            column
            for column in df.columns
            if column != TARGET_COLUMN and pd.api.types.is_numeric_dtype(df[column])
        ]

    if not numeric_columns:
        raise ValueError("No usable numeric feature columns found.")

    numeric_frame = df[numeric_columns].apply(pd.to_numeric, errors="coerce")
    numeric_frame = numeric_frame.fillna(numeric_frame.median()).fillna(0.0)

    categorical_frames: list[pd.DataFrame] = []
    for column in OPTIONAL_CATEGORICAL_FEATURES:
        if column in df.columns:
            encoded = pd.get_dummies(df[column].fillna("unknown"), prefix=column)
            categorical_frames.append(encoded.astype(float))

    frames = [numeric_frame.astype(float)] + categorical_frames
    full_frame = pd.concat(frames, axis=1)
    return FeatureBundle(
        matrix=full_frame.to_numpy(dtype=float),
        feature_names=full_frame.columns.tolist(),
    )


def choose_split(n_rows: int, n_classes: int) -> tuple[np.ndarray, np.ndarray]:
    if n_rows >= 12:
        eval_size = max(2, int(math.ceil(n_rows * 0.2)))
    else:
        eval_size = max(2, n_classes)

    eval_size = min(eval_size, n_rows - n_classes)
    if eval_size <= 0:
        raise ValueError("Not enough rows to create a valid train/eval split.")

    train_size = n_rows - eval_size
    train_idx = np.arange(train_size)
    eval_idx = np.arange(train_size, n_rows)
    return train_idx, eval_idx


def standardize_train_eval(
    x_train: np.ndarray,
    x_eval: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    means = x_train.mean(axis=0)
    stds = x_train.std(axis=0)
    stds[stds == 0] = 1.0
    return (x_train - means) / stds, (x_eval - means) / stds


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp_logits = np.exp(shifted)
    return exp_logits / exp_logits.sum(axis=1, keepdims=True)


def multiclass_log_loss(y_true: np.ndarray, probs: np.ndarray) -> float:
    clipped = np.clip(probs, 1e-12, 1.0)
    return float(-np.mean(np.sum(y_true * np.log(clipped), axis=1)))


def multiclass_brier(y_true: np.ndarray, probs: np.ndarray) -> float:
    return float(np.mean(np.sum((probs - y_true) ** 2, axis=1)))


def expand_probabilities(probs: np.ndarray, observed_labels: Iterable[int]) -> np.ndarray:
    expanded = np.zeros((probs.shape[0], 3), dtype=float)
    for observed_index, raw_label in enumerate(observed_labels):
        expanded[:, raw_label] = probs[:, observed_index]
    return expanded


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
