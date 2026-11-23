import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.schemas.prediction import PredictionRequest
from app.services import ml_loader


def test_v2_serving_uses_bundled_preprocessor(monkeypatch):
    features = ["machine_id", "part_id", "time_in_service_days"]
    data = pd.DataFrame([
        ["M-1", "P-1", 10],
        ["M-2", "P-2", 100],
        ["M-1", "P-1", 200],
        ["M-2", "P-2", 300],
    ], columns=features)
    pipeline = Pipeline([
        ("preprocessor", ColumnTransformer([
            ("ids", OneHotEncoder(handle_unknown="ignore"), ["machine_id", "part_id"]),
            ("days", "passthrough", ["time_in_service_days"]),
        ])),
        ("model", LogisticRegression()),
    ])
    pipeline.fit(data, [0, 0, 1, 1])
    artifact = {"schema_version": 2, "features": features, "pipeline": pipeline}
    monkeypatch.setattr(ml_loader, "load_model", lambda version: artifact)
    request = PredictionRequest(
        machine_id="unseen-machine", part_id="unseen-part", time_in_service_days=120
    )
    expected = pipeline.predict_proba(pd.DataFrame([request.model_dump()]))[0, 1]
    assert ml_loader.make_prediction(request, model_version="v2.0") == expected
