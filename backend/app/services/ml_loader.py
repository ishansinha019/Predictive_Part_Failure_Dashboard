import joblib
import pandas as pd
from pathlib import Path
from app.core.config import settings
from app.schemas.prediction import PredictionRequest

# --- In-memory cache for the loaded model (v1.0 trained on service_history_extended) ---
model_cache = {}

def load_model(version: str = "v1.0"):
    """Loads a specific version of the model artifact from disk."""
    if version in model_cache:
        return model_cache[version]
    
    path = Path(__file__).resolve().parents[2] / "models" / version / "part_failure_model.joblib"
    model_artifact = joblib.load(path)
    model_cache[version] = model_artifact
    print(f"Model version {version} loaded successfully.")
    return model_artifact

def make_prediction(input_data: PredictionRequest, model_version: str | None = None):
    """Makes a prediction using the loaded model."""
    artifact = load_model(model_version or settings.MODEL_VERSION)

    data_dict = {
        "machine_id": [input_data.machine_id],
        "part_id": [input_data.part_id],
        "time_in_service_days": [input_data.time_in_service_days],
    }
    df = pd.DataFrame(data_dict)
    if artifact.get("schema_version") == 2:
        return artifact["pipeline"].predict_proba(df[artifact["features"]])[0, 1]

    model = artifact['model']
    encoder = artifact['encoder']
    feature_columns = artifact['feature_columns']
    df["service_type"] = "Routine Check"
    df["machine_type"] = df["machine_id"].str.split("-").str[0]

    # Preprocess the data using the loaded encoder
    categorical_features = list(encoder.feature_names_in_)
    numerical_features = ['time_in_service_days']

    encoded_data = encoder.transform(df[categorical_features])
    encoded_columns = encoder.get_feature_names_out(categorical_features)
    X_encoded = pd.DataFrame(encoded_data, columns=encoded_columns)
    
    X_processed = pd.concat([df[numerical_features].reset_index(drop=True), X_encoded], axis=1)

    # Align columns with the training data
    missing_cols = set(feature_columns) - set(X_processed.columns)
    for c in missing_cols:
        X_processed[c] = 0
    X_processed = X_processed[feature_columns]

    # Get probability of the "failure" class (class 1)
    prediction_proba = model.predict_proba(X_processed)[:, 1]
    
    return prediction_proba[0]