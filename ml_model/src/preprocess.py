import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

def load_data(raw_data_path):
    """
    Loads the raw data from the service_history_extended.csv file.
    """
    try:
        df = pd.read_csv(raw_data_path)
    except FileNotFoundError:
        print(f"Error: Data file not found at {raw_data_path}")
        return None
    
    # --- Feature Engineering (from Notebook 2) ---
    # Create the 'machine_type' feature by splitting the 'machine_id'
    df['machine_type'] = df['machine_id'].str.split('-').str[0]
    
    # Rename 'part_failed' to 'failed' to match the original script's target variable
    df = df.rename(columns={'part_failed': 'failed'})
    
    # Drop columns that are not used for training
    df = df.drop(columns=['service_id', 'service_date'])
    
    print(f"Successfully loaded and engineered data from {raw_data_path}")
    return df

def preprocess_data(df):
    """
    Applies one-hot encoding to all categorical features.
    """
    
    # --- UPDATED ---
    # Add 'machine_type' to the list of categorical features
    categorical_features = ['machine_id', 'part_id', 'service_type', 'machine_type']
    numerical_features = ['time_in_service_days']
    target = 'failed'

    # Filter out any potential rows with NaNs just in case
    df = df.dropna(subset=categorical_features + numerical_features + [target])

    # Set up the encoder
    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    
    # We fit the encoder on the categorical features
    encoder.fit(df[categorical_features])
    
    # Transform data
    encoded_data = encoder.transform(df[categorical_features])
    encoded_columns = encoder.get_feature_names_out(categorical_features)
    
    X_encoded = pd.DataFrame(encoded_data, columns=encoded_columns)
    X_numerical = df[numerical_features]
    
    # Combine all features
    X = pd.concat([X_numerical.reset_index(drop=True), X_encoded.reset_index(drop=True)], axis=1)
    y = df[target]
    
    # Get all feature columns for the backend to use
    feature_columns = X.columns.tolist()

    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    return X_train, X_test, y_train, y_test, encoder, feature_columns
