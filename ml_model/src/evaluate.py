import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    average_precision_score,
    confusion_matrix,
    f1_score,
    recall_score,
    roc_auc_score,
)


def evaluate_model(pipeline, features, labels):
    probabilities = pipeline.predict_proba(features)[:, 1]
    predictions = pipeline.predict(features)
    return {
        "average_precision": float(average_precision_score(labels, probabilities)),
        "roc_auc": float(roc_auc_score(labels, probabilities)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
    }, confusion_matrix(labels, predictions, labels=[0, 1])


def export_evaluation(output_dir: Path, name: str, metrics, matrix):
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / f"{name}_metrics.json"
    matrix_path = output_dir / f"{name}_confusion_matrix.png"
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    display = ConfusionMatrixDisplay(matrix, display_labels=["no failure", "failure"])
    display.plot()
    display.figure_.savefig(matrix_path, bbox_inches="tight")
    plt.close(display.figure_)
    return metrics_path, matrix_path
