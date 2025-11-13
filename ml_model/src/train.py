import os
import joblib
from xgboost import XGBClassifier
from sklearn.metrics import classification_report
from src.preprocess import load_data, preprocess_data

def train_model():
    print("Loading raw data...")
    
    # --- UPDATED ---
    # Define the path to your real data
    data_path = 'data/service_history_extended.csv'
    df = load_data(raw_data_path=data_path) 
    
    if df is None:
        print("Data loading failed. Exiting.")
        return

    print("Preprocessing data...")
    X_train, X_test, y_train, y_test, encoder, feature_columns = preprocess_data(df)

    print("Training XGBoost model...")
    # We use scale_pos_weight to handle the class imbalance found in the notebook
    # The failure rate is ~22%, so a weight of ~78/22 = 3.5 is good. Let's stick with 5 for a stronger penalty.
    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', scale_pos_weight=5)
    model.fit(X_train, y_train)

    print("\nEvaluating model performance...")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))

    # --- THIS IS THE HAND-OFF ---
    
    # Bundle all necessary artifacts into one file
    model_artifact = {
        'model': model,
        'encoder': encoder,
        'feature_columns': feature_columns
    }

    # Define the new save path pointing to the backend's model directory
    model_version = "v1.0"
    # This path goes up one level (..) and then into the backend/models directory
    save_directory = f'../backend/models/{model_version}' 
    save_path = f'{save_directory}/part_failure_model.joblib'

    # Create the directory if it doesn't exist
    os.makedirs(save_directory, exist_ok=True)

    joblib.dump(model_artifact, save_path)
    print(f"\nModel artifact for version {model_version} saved to {save_path}")

if __name__ == "__main__":
    train_model()