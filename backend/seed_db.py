import pandas as pd
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db import models

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

def seed_data():
    db: Session = SessionLocal()
    
    # Path to your CSV
    csv_path = "../ml_model/data/service_history_extended.csv"
    
    print(f"Reading data from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print("Error: CSV file not found. Check the path.")
        return

    print("Seeding database...")
    count = 0
    for index, row in df.iterrows():
        # Map CSV columns to Database columns
        # We treat historical failures as a '100%' risk score for the log
        score = 1.0 if row['part_failed'] == 1 else 0.0
        rec = "Historical Failure" if row['part_failed'] == 1 else "Historical Pass"

        log_entry = models.PredictionLog(
            machine_id=row['machine_id'],
            part_id=row['part_id'],
            time_in_service_days=row['time_in_service_days'],
            prediction_score=score,
            recommendation=rec,
            # We can use the service_date as the timestamp
            prediction_timestamp=pd.to_datetime(row['service_date'])
        )
        db.add(log_entry)
        count += 1

    db.commit()
    db.close()
    print(f"Success! Added {count} records to the database.")

if __name__ == "__main__":
    seed_data()