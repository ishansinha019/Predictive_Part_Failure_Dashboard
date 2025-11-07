import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

def load_data(raw_data_path):
    """Loads the raw data CSV."""
    # This is a mock function to create sample data
    # In a real-world scenario, you'd use pd.read_csv(raw_data_path)
    data = {
        'machine_id': ['M-185', 'M-185', 'M-201', 'M-202', 'M-185', 'M-201'],
        'part_id': ['P-BRG-02', 'P-FAN-01', 'P-BRG-02', 'P-PMP-04', 'P-BRG-02', 'P-FAN-01'],
        'time_in_service_days': [450, 450, 600, 120, 700, 700],
        'service_type': ['Routine Check', 'Failure', 'Routine Check', 'Failure', 'Routine Check', 'Failure'],
        'failed': [0, 1, 0, 1, 0, 1]
    }
    # Add more data to make the model meaningful
    for _ in range(100):
        data['machine_id'].append('M-185')
        data['part_id'].append('P-BRG-02')
        data['time_in_service_days'].append(300 + (_ * 5))
        data['service_type'].append('Routine Check')
        data['failed'].append(0)

    return pd.DataFrame(data)

def preprocess_data(df):
    """Applies one-hot encoding to categorical features."""
    
    categorical_features = ['machine_id', 'part_id', 'service_type']
    numerical_features = ['time_in_service_days']
    target = 'failed'

    # Set up the encoder
    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
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
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    return X_train, X_test, y_train, y_test, encoder, feature_columns