import pandas as pd
import pandera as pa
import pytest
import joblib
from sklearn.linear_model import LogisticRegression

from src.preprocess import FEATURES, TARGET, build_pipeline, chronological_split, load_data
from src.train import DEFAULT_DATA, train_model
from src.validate import validate_dataset


def test_invalid_records_are_rejected():
    data = load_data(DEFAULT_DATA)
    data.loc[0, "time_in_service_days"] = -1
    with pytest.raises(pa.errors.SchemaErrors):
        validate_dataset(data)


def test_split_keeps_dates_and_future_data_separate():
    data = load_data(DEFAULT_DATA)
    train, test = chronological_split(data)
    assert train["service_date"].max() < test["service_date"].min()
    assert len(train) + len(test) == len(data)


def test_pipeline_predicts_deterministically_for_unseen_categories():
    data = load_data(DEFAULT_DATA)
    train, _ = chronological_split(data)
    pipeline = build_pipeline(LogisticRegression(max_iter=1000, random_state=42))
    pipeline.fit(train[FEATURES], train[TARGET])
    unseen = pd.DataFrame([{
        "machine_id": "unseen-machine", "part_id": "unseen-part",
        "time_in_service_days": 120,
    }])
    first = pipeline.predict_proba(unseen)[0, 1]
    assert 0 <= first <= 1
    assert first == pipeline.predict_proba(unseen)[0, 1]


def test_training_exports_a_usable_versioned_artifact(tmp_path):
    output = tmp_path / "output"
    results = train_model(DEFAULT_DATA, output, f"sqlite:///{tmp_path / 'mlflow.db'}")
    assert set(results) == {"dummy", "logistic_regression", "xgboost"}
    artifact = joblib.load(output / "part_failure_model.joblib")
    assert artifact["schema_version"] == 2
    data = load_data(DEFAULT_DATA)
    assert 0 <= artifact["pipeline"].predict_proba(data[FEATURES].iloc[:1])[0, 1] <= 1
    assert (output / "MODEL_CARD.md").is_file()
    assert (output / "xgboost_confusion_matrix.png").is_file()
