"""Pure paired Ridge slice of the frozen BTC V1 development evaluation.

This module expects already aligned, validated session rows. It does not load
historical artifacts or reproduce the published metrics by itself.
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Any, Mapping, Sequence

from .btc_reference import (
    BTC_V1_COMPARATOR_COLUMNS,
    BTC_V1_CONTROL_COLUMNS,
    BTC_V1_QUOTE_QUALITY_COLUMNS,
    BTC_V1_TARGET_FIELDS,
)


# These are the same frozen B0/B/L/A column sets used by the private runner.
BTC = BTC_V1_CONTROL_COLUMNS
Q = BTC_V1_QUOTE_QUALITY_COLUMNS
FEATURES = BTC_V1_COMPARATOR_COLUMNS
TARGETS = BTC_V1_TARGET_FIELDS
ALPHA = 1.0


def eligible(row: Mapping[str, Any], target: str, *, paired: bool = True) -> bool:
    """Apply the private runner's common-row rule for a target and comparator."""
    if target not in TARGETS:
        raise ValueError(f"Unsupported BTC V1 target: {target}")
    if (row["btc_status"] != "available" or row["target_status"][target] != "available"
            or not isinstance(row["targets"][target], (int, float))
            or not math.isfinite(row["targets"][target])
            or any(not isinstance(row["features"][name], (int, float))
                   or not math.isfinite(row["features"][name]) for name in BTC)):
        return False
    return not paired or (row["pm_status"] == "complete" and
                          row["causal_status"] == "ok" and
                          all(isinstance(row["features"][name], (int, float))
                              and math.isfinite(row["features"][name])
                              for name in Q + ("q", "dq10")))


def chronological_split(
    rows: Sequence[Mapping[str, Any]], boundary: dt.datetime, target: str,
) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]], int]:
    """Pair first, then purge train rows whose latest target crosses boundary."""
    if boundary.tzinfo is None or boundary.utcoffset() is None:
        raise ValueError("Chronological boundary must be timezone-aware")
    paired = [row for row in rows if eligible(row, target)]
    if list(rows) != sorted(rows, key=lambda row: (row["start"], row["session_id"])):
        raise ValueError("Feature rows are not chronological")
    if len({row["session_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate feature session")
    train = [row for row in paired if row["start"] < boundary and
             row["target_end"] <= boundary]
    validation = [row for row in paired if row["start"] >= boundary]
    purged = sum(row["start"] < boundary and row["target_end"] > boundary
                 for row in paired)
    if not train or not validation:
        raise ValueError(f"{target} has no computable training/validation split")
    return train, validation, purged


def solve_spd(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Cholesky solver copied from the frozen development Ridge runner."""
    size = len(rhs)
    lower = [[0.0] * size for _ in range(size)]
    for i in range(size):
        for j in range(i + 1):
            residual = matrix[i][j] - math.fsum(
                lower[i][k] * lower[j][k] for k in range(j)
            )
            if i == j:
                if residual <= 0 or not math.isfinite(residual):
                    raise ValueError("Ridge normal matrix is not positive definite")
                lower[i][j] = math.sqrt(residual)
            else:
                lower[i][j] = residual / lower[j][j]
    middle = [0.0] * size
    for i in range(size):
        middle[i] = (
            rhs[i] - math.fsum(lower[i][k] * middle[k] for k in range(i))
        ) / lower[i][i]
    result = [0.0] * size
    for i in range(size - 1, -1, -1):
        result[i] = (
            middle[i]
            - math.fsum(lower[k][i] * result[k] for k in range(i + 1, size))
        ) / lower[i][i]
    for i in range(size):
        error = math.fsum(matrix[i][j] * result[j] for j in range(size)) - rhs[i]
        if abs(error) > 1e-7 * (1 + abs(rhs[i])):
            raise ValueError("Ridge normal-equation residual failed")
    return result


def metrics(actual: list[float], predicted: list[float]) -> dict[str, float | None]:
    if len(actual) != len(predicted) or not actual:
        raise ValueError("Invalid metric inputs")
    n = len(actual)
    errors = [p - y for p, y in zip(predicted, actual)]
    mse = math.fsum(e * e for e in errors) / n
    mae = math.fsum(abs(e) for e in errors) / n
    ymean = math.fsum(actual) / n
    pmean = math.fsum(predicted) / n
    ydev = [y - ymean for y in actual]
    pdev = [p - pmean for p in predicted]
    yss = math.fsum(v * v for v in ydev)
    pss = math.fsum(v * v for v in pdev)
    covariance = math.fsum(a * b for a, b in zip(ydev, pdev))
    result = {
        "mse": mse,
        "rmse": math.sqrt(mse),
        "mae": mae,
        "r2": 1 - n * mse / yss if yss > 0 else None,
        "pearson_r": (
            covariance / math.sqrt(yss * pss)
            if yss > 0 and pss > 0 and min(predicted) != max(predicted)
            else None
        ),
    }
    if not all(v is None or math.isfinite(v) for v in result.values()):
        raise ValueError("Nonfinite metric")
    return result


def fit_and_evaluate(train: list[Mapping[str, Any]],
                     validation: list[Mapping[str, Any]],
                     columns: tuple[str, ...], target: str) -> dict[str, Any]:
    """Alpha-one Ridge with train-only population scaling and free intercept."""
    n, width = len(train), len(columns)
    xtrain = [[float(row["features"][col]) for col in columns] for row in train]
    xval = [[float(row["features"][col]) for col in columns] for row in validation]
    ytrain = [float(row["targets"][target]) for row in train]
    yval = [float(row["targets"][target]) for row in validation]
    if not all(math.isfinite(value) for row in xtrain + xval for value in row):
        raise ValueError("Nonfinite predictor")
    if not all(math.isfinite(value) for value in ytrain + yval):
        raise ValueError("Nonfinite target")

    # All fitted statistics below use training rows only.
    means = [math.fsum(row[j] for row in xtrain) / n for j in range(width)]
    scales = []
    for j in range(width):
        variance = math.fsum((row[j] - means[j]) ** 2 for row in xtrain) / n
        scales.append(math.sqrt(variance) if variance > 0 else 1.0)
    ztrain = [
        [(row[j] - means[j]) / scales[j] for j in range(width)]
        for row in xtrain
    ]
    intercept = math.fsum(ytrain) / n
    gram = [[0.0] * width for _ in range(width)]
    rhs = [0.0] * width
    for zrow, y in zip(ztrain, ytrain):
        centered_y = y - intercept
        for j in range(width):
            rhs[j] += zrow[j] * centered_y
            for k in range(j, width):
                gram[j][k] += zrow[j] * zrow[k]
    for j in range(width):
        for k in range(j + 1, width):
            gram[k][j] = gram[j][k]
        gram[j][j] += ALPHA
    weights = solve_spd(gram, rhs)
    predictions = [
        intercept + math.fsum(
            weights[j] * (row[j] - means[j]) / scales[j]
            for j in range(width)
        )
        for row in xval
    ]
    return {
        "train_rows": n,
        "validation_rows": len(validation),
        "metrics": metrics(yval, predictions),
        "intercept": intercept,
        "coefficients_standardized": dict(zip(columns, weights)),
        "training_feature_means": dict(zip(columns, means)),
        "training_feature_scales": dict(zip(columns, scales)),
    }


def naive(train: list[Mapping[str, Any]], validation: list[Mapping[str, Any]],
          target: str) -> dict[str, Any]:
    train_mean = math.fsum(row["targets"][target] for row in train) / len(train)
    actual = [row["targets"][target] for row in validation]
    return {
        "train_rows": len(train),
        "validation_rows": len(validation),
        "train_target_mean": train_mean,
        "metrics": metrics(actual, [train_mean] * len(validation)),
    }


def predict(model: Mapping[str, Any], rows: list[Mapping[str, Any]],
            columns: tuple[str, ...]) -> list[float]:
    """Use fitted training statistics for fixed validation predictions."""
    return [
        model["intercept"] + math.fsum(
            model["coefficients_standardized"][name]
            * (row["features"][name] - model["training_feature_means"][name])
            / model["training_feature_scales"][name]
            for name in columns
        )
        for row in rows
    ]


def compare(a: Mapping[str, Any], b: Mapping[str, Any], *,
            candidate: str, comparator: str) -> dict[str, Any]:
    am, bm = a["metrics"]["mse"], b["metrics"]["mse"]
    return {"a_mse": am, "comparator_mse": bm,
            "absolute_mse_improvement": bm - am,
            "relative_mse_improvement": (bm - am) / bm if bm else None,
            "winner": candidate if am < bm else comparator if bm < am else "tie"}


def evaluate_paired(rows: Sequence[Mapping[str, Any]], boundary: dt.datetime,
                    target: str = "y1") -> dict[str, Any]:
    """Fit B0/B/L/A and naive on identical eligible, chronological rows."""
    train, validation, purged = chronological_split(rows, boundary, target)
    ridge = {name: fit_and_evaluate(train, validation, columns, target)
             for name, columns in FEATURES.items()}
    baseline = naive(train, validation, target)
    return {
        "target": target,
        "paired_train_rows": len(train),
        "paired_validation_rows": len(validation),
        "purged_train_rows": purged,
        "paired_train_sessions": [row["session_id"] for row in train],
        "paired_validation_sessions": [row["session_id"] for row in validation],
        "ridge": ridge,
        "naive": baseline,
        "A_vs_B": compare(ridge["A"], ridge["B"], candidate="A", comparator="B"),
    }
