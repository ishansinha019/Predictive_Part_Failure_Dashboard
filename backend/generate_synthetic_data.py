import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from app.db.database import SessionLocal, engine
from app.db import models

# Initialize DB
models.Base.metadata.create_all(bind=engine)

def generate_fleet():
    db = SessionLocal()
    
    # 1. Load the original "seed" data patterns
    print("Loading patterns from real data...")
    df_real = pd.read_csv("../ml_model/data/service_history_extended.csv")
    
    # Get distinct real machines to use as templates
    templates = df_real['machine_id'].unique()
    
    # We want to create 100 total machines
    target_machines = 100
    new_data = []
    
    print(f"Generating synthetic fleet of {target_machines} machines...")

    for i in range(target_machines):
        # Pick a random template (e.g., M-185) to mimic
        template_id = np.random.choice(templates)
        
        # Create a new unique ID (e.g., M-1001, H-2045)
        prefix = template_id.split('-')[0] # 'M' or 'H'
        new_id = f"{prefix}-{1000 + i}"
        
        # Create a current status for this machine
        # We simulate that this machine has a part installed
        parts = ['P-BRG-02', 'P-SEN-04', 'P-VLV-01', 'P-MTR-05', 'P-CTR-03']
        current_part = np.random.choice(parts)
        
        # Randomize "Time in Service"
        # Most machines are new (low days), some are old (high days)
        days_active = int(np.random.gamma(shape=2, scale=150)) 
        
        # Determine risk (using simplified logic matching your ML model)
        # This acts as our "Ground Truth" for the simulation
        is_failure = 0
        rec = "Routine Check"
        risk_score = 0.1
        
        # Logic: Older bearings fail more often
        if current_part == 'P-BRG-02' and days_active > 400:
            risk_score = np.random.uniform(0.6, 0.95)
            rec = "High Risk - Inspect"
        elif days_active > 600:
            risk_score = np.random.uniform(0.5, 0.8)
            rec = "Aging - Monitor"
            
        # Create the DB entry
        log_entry = models.PredictionLog(
            machine_id=new_id,
            part_id=current_part,
            time_in_service_days=days_active,
            prediction_score=risk_score,
            recommendation=rec,
            prediction_timestamp=datetime.now()
        )
        db.add(log_entry)

    db.commit()
    db.close()
    print("Success! Your fleet has expanded.")

if __name__ == "__main__":
    generate_fleet()