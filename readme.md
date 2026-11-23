Disclaimer: This project utilizes a synthetic dataset generated to simulate real-world service order patterns. 
All data is synthetically created and does not contain any real, proprietary, or confidential information from any company.

## ML training and evaluation

From `ml_model`, install `requirements.txt` in a Python virtual environment,
then run `python -m src.train` and `python -m pytest tests`. Training validates
the data, uses chronological train/validation/test splits, tunes XGBoost on
validation average precision, and evaluates XGBoost and two baselines on the
held-out test set. MLflow runs are stored locally in `ml_model/mlflow.db`, with
artifacts under `ml_model/outputs/v2.0/mlflow-artifacts`. Metrics, confusion
matrices, feature importances, and a generated model card are also in
`ml_model/outputs/v2.0`.

The existing backend model remains the default. To explicitly try v2, copy
`ml_model/outputs/v2.0/part_failure_model.joblib` to
`backend/models/v2.0/part_failure_model.joblib` and set `MODEL_VERSION=v2.0`
in the backend `.env`, then restart the backend. Install compatible versions
of the ML dependencies in the backend environment as well; the generated
model card records the versions used for training. Only load model artifacts
from trusted sources. See
[the model card](docs/MODEL_CARD.md) for limitations.
