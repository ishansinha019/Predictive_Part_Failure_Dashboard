import os
import pandas as pd
import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from preprocess import preprocess_data

def train_model():
    """
    Main function to train and save the part failure prediction model.
    """
    print("Loading data...")
    df = pd.read_csv('../data/service_history_extended.csv')

    print("Preprocessing data...")
    X, y, encoder, feature_columns = preprocess_data(df)

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Handle class imbalance by calculating scale_pos_weight
    # This tells the model to pay more attention to the minority class (failures)
    scale_pos_weight = y_train.value_counts()[0] / y_train.value_counts()[1]
    
    print("Training XGBoost model...")
    model = xgb.XGBClassifier(
        objective='binary:logistic',
        eval_metric='logloss',
        use_label_encoder=False,
        scale_pos_weight=scale_pos_weight,
        random_state=42
    )
    model.fit(X_train, y_train)

    print("\nEvaluating model performance...")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))

    # Save the model, encoder, and feature columns together in one file
    # This is crucial for ensuring the API can process new data correctly
    model_artifact = {
        'model': model,
        'encoder': encoder,
        'feature_columns': feature_columns
    }
    
# Define the new save path pointing to the backend's model directory
    model_version = "v1.0"
    save_directory = f'../backend/models/{model_version}'
    save_path = f'{save_directory}/part_failure_model.joblib'

    # Create the directory if it doesn't exist
    os.makedirs(save_directory, exist_ok=True)

    joblib.dump(model_artifact, save_path)
    print(f"\nModel artifact for version {model_version} saved to {save_path}")