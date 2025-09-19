import pandas as pd
from sklearn.preprocessing import OneHotEncoder

def preprocess_data(df: pd.DataFrame, encoder=None, feature_columns=None):
    """
    Preprocesses the service history data for model training or prediction.

    Args:
        df (pd.DataFrame): The input dataframe.
        encoder (OneHotEncoder, optional): A fitted OneHotEncoder. If None, a new one will be fitted.
        feature_columns (list, optional): The list of feature columns from training. Required for prediction.

    Returns:
        tuple: A tuple containing:
            - X (pd.DataFrame): The processed features.
            - y (pd.Series): The target variable.
            - encoder (OneHotEncoder): The fitted encoder.
            - columns (list): The list of one-hot encoded column names.
    """
    # Define categorical and numerical features
    categorical_features = ['machine_id', 'part_id', 'service_type']
    numerical_features = ['time_in_service_days']
    
    # Drop unnecessary columns and define target
    df = df.drop(columns=['service_id', 'service_date'])
    y = df['part_failed']
    X_raw = df.drop(columns=['part_failed'])

    # Handle categorical features with One-Hot Encoding
    if encoder is None:
        encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
        encoder.fit(X_raw[categorical_features])

    encoded_data = encoder.transform(X_raw[categorical_features])
    encoded_columns = encoder.get_feature_names_out(categorical_features)
    X_encoded = pd.DataFrame(encoded_data, columns=encoded_columns, index=X_raw.index)

    # Combine numerical and encoded categorical features
    X_processed = pd.concat([X_raw[numerical_features], X_encoded], axis=1)

    # Align columns for prediction to match training
    if feature_columns is not None:
        # Add missing columns with 0
        missing_cols = set(feature_columns) - set(X_processed.columns)
        for c in missing_cols:
            X_processed[c] = 0
        # Ensure order is the same
        X_processed = X_processed[feature_columns]

    return X_processed, y, encoder, X_processed.columns.tolist()
# test change