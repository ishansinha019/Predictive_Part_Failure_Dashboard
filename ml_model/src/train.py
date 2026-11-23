import argparse
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path

import joblib
import mlflow
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

from src.evaluate import evaluate_model, export_evaluation
from src.preprocess import FEATURES, TARGET, build_pipeline, chronological_split, load_data

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = PROJECT_ROOT / "ml_model" / "data" / "service_history_extended.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "ml_model" / "outputs" / "v2.0"
DEFAULT_TRACKING = PROJECT_ROOT / "ml_model" / "mlflow.db"
PARAMETER_GRID = [
    {"scale_pos_weight": 5, "learning_rate": 0.05, "max_depth": 3},
    {"scale_pos_weight": 5, "learning_rate": 0.1, "max_depth": 4},
]


def train_model(data_path: Path, output_dir: Path, tracking_uri: str):
    data = load_data(data_path)
    development, test = chronological_split(data)
    train, validation = chronological_split(development, test_fraction=0.25)
    mlflow.set_tracking_uri(tracking_uri)
    client = mlflow.MlflowClient()
    if client.get_experiment_by_name("part-failure") is None:
        client.create_experiment(
            "part-failure",
            artifact_location=(output_dir / "mlflow-artifacts").resolve().as_uri(),
        )
    mlflow.set_experiment("part-failure")
    output_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(data_path.read_bytes()).hexdigest()
    age_ranges = data.groupby(TARGET)["time_in_service_days"].agg(["min", "max"])
    age_summary = "; ".join(
        f"class {label}: {int(row['min'])}-{int(row['max'])} days"
        for label, row in age_ranges.iterrows()
    )
    ages_separate = (
        age_ranges.loc[0, "max"] < age_ranges.loc[1, "min"]
        or age_ranges.loc[1, "max"] < age_ranges.loc[0, "min"]
    )
    versions = {
        "python": platform.python_version(),
        **{package: version(package) for package in ("pandas", "scikit-learn", "xgboost", "joblib")},
    }

    best_parameters = None
    best_score = float("-inf")
    for parameters in PARAMETER_GRID:
        candidate = build_pipeline(XGBClassifier(
            **parameters, n_estimators=100, random_state=42, eval_metric="logloss",
            n_jobs=1,
        ))
        candidate.fit(train[FEATURES], train[TARGET])
        metrics, _ = evaluate_model(candidate, validation[FEATURES], validation[TARGET])
        with mlflow.start_run(run_name="xgboost-validation"):
            mlflow.log_params({**parameters, "n_estimators": 100, "random_state": 42})
            mlflow.log_metrics({f"validation_{key}": value for key, value in metrics.items()})
            mlflow.log_param("dataset_sha256", digest)
        if metrics["average_precision"] > best_score:
            best_score = metrics["average_precision"]
            best_parameters = parameters

    estimators = {
        "dummy": DummyClassifier(strategy="prior"),
        "logistic_regression": LogisticRegression(max_iter=1000, random_state=42),
        "xgboost": XGBClassifier(
            **best_parameters, n_estimators=100, random_state=42,
            eval_metric="logloss", n_jobs=1,
        ),
    }
    results = {}
    model_run_id = None
    for name, estimator in estimators.items():
        pipeline = build_pipeline(estimator)
        pipeline.fit(development[FEATURES], development[TARGET])
        metrics, matrix = evaluate_model(pipeline, test[FEATURES], test[TARGET])
        results[name] = metrics
        metric_path, matrix_path = export_evaluation(output_dir, name, metrics, matrix)
        with mlflow.start_run(run_name=name) as run:
            mlflow.log_param("dataset_sha256", digest)
            mlflow.log_params({
                "training_rows": len(development), "test_rows": len(test),
                "train_end": str(development["service_date"].max().date()),
                "test_start": str(test["service_date"].min().date()),
            })
            if name == "xgboost":
                mlflow.log_params({**best_parameters, "n_estimators": 100, "random_state": 42})
                mlflow.log_dict(versions, "environment.json")
                names = pipeline.named_steps["preprocessor"].get_feature_names_out()
                importance = dict(zip(names, map(float, estimator.feature_importances_)))
                importance_path = output_dir / "feature_importance.json"
                importance_path.write_text(json.dumps(importance, indent=2) + "\n", encoding="utf-8")
                mlflow.log_artifact(str(importance_path))
                artifact = {
                    "schema_version": 2,
                    "model_version": "v2.0",
                    "features": FEATURES,
                    "dataset_sha256": digest,
                    "versions": versions,
                    "training_parameters": best_parameters,
                    "pipeline": pipeline,
                }
                artifact_path = output_dir / "part_failure_model.joblib"
                joblib.dump(artifact, artifact_path)
                mlflow.log_artifact(str(artifact_path))
                model_run_id = run.info.run_id
            mlflow.log_metrics(metrics)
            mlflow.log_artifact(str(metric_path))
            mlflow.log_artifact(str(matrix_path))

    card = output_dir / "MODEL_CARD.md"
    card.write_text(
        "# Model card: v2.0\n\n"
        "For demonstration on synthetic service records only; not for maintenance decisions.\n\n"
        f"Dataset SHA-256: `{digest}`\n\n"
        f"Environment: `{json.dumps(versions)}`\n\n"
        f"Training rows: {len(development)}; test rows: {len(test)}. "
        f"Training ends {development['service_date'].max().date()}; "
        f"test starts {test['service_date'].min().date()}.\n\n"
        "Features: machine ID, part ID, and time in service. Service type is excluded "
        "because it reveals the outcome in this dataset. "
        "Unseen IDs are encoded as unknown categories.\n\n"
        "Metrics use the held-out chronological test set; average precision summarizes "
        "the precision-recall curve. Threshold-dependent metrics use the classifier's "
        "default threshold.\n\n"
        + "\n".join(f"- {name}: {json.dumps(metrics)}" for name, metrics in results.items())
        + f"\n\nService-age ranges: {age_summary}. "
        + ("These ranges do not overlap, so strong scores can reflect data construction "
           "rather than real-world skill. " if ages_separate else "")
        + "Synthetic data and a small test set limit generalization and confidence. "
        "No calibration, subgroup fairness, or real-world validation has been established.\n",
        encoding="utf-8",
    )
    client.log_artifact(model_run_id, str(card))
    return results


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate the part failure model.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tracking-uri", default=f"sqlite:///{DEFAULT_TRACKING}")
    args = parser.parse_args()
    print(json.dumps(train_model(args.data, args.output, args.tracking_uri), indent=2))


if __name__ == "__main__":
    main()
