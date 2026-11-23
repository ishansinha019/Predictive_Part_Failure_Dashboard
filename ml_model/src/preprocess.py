from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.validate import validate_dataset

FEATURES = ["machine_id", "part_id", "time_in_service_days"]
CATEGORICAL_FEATURES = ["machine_id", "part_id"]
TARGET = "part_failed"


def load_data(raw_data_path: str | Path) -> pd.DataFrame:
    data = pd.read_csv(raw_data_path)
    data["service_date"] = pd.to_datetime(data["service_date"], errors="raise")
    return validate_dataset(data)


def chronological_split(data: pd.DataFrame, test_fraction: float = 0.2):
    """Split at a date boundary so a day never spans training and evaluation."""
    dates = sorted(data["service_date"].unique())
    if len(dates) < 2:
        raise ValueError("At least two distinct service dates are required.")
    train_dates, test_dates = train_test_split(
        dates, test_size=test_fraction, shuffle=False
    )
    train = data[data["service_date"].isin(train_dates)].copy()
    test = data[data["service_date"].isin(test_dates)].copy()
    for name, split in (("train", train), ("test", test)):
        if split[TARGET].nunique() != 2:
            raise ValueError(f"{name} split must contain both failure classes.")
    return train, test


def build_pipeline(estimator):
    preprocessor = ColumnTransformer(
        [
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", StandardScaler(), ["time_in_service_days"]),
        ]
    )
    return Pipeline([("preprocessor", preprocessor), ("model", estimator)])
