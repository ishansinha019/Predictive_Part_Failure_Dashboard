import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.db.database import SessionLocal
from app.db import models

def generate_fleet():
    db = SessionLocal()
    try:
        csv_path = "../ml_model/data/service_history_extended.csv"
        if not os.path.exists(csv_path):
            csv_path = "ml_model/data/service_history_extended.csv"

        print(f"Loading patterns from {csv_path}...")
        df_real = pd.read_csv(csv_path)
        templates = df_real['machine_id'].unique()
        
        target_machines = 100
        print(f"Generating synthetic fleet of {target_machines} machines...")

        parts = ['P-BRG-02', 'P-SEN-04', 'P-VLV-01', 'P-MTR-05', 'P-CTR-03']

        for i in range(target_machines):
            template_id = np.random.choice(templates)
            prefix = template_id.split('-')[0]  # 'M' or 'H'
            new_id = f"{prefix}-{1000 + i}"
            
            # Ensure Machine exists in DB
            machine = db.query(models.Machine).filter(models.Machine.id == new_id).first()
            if not machine:
                machine = models.Machine(
                    id=new_id,
                    machine_type=prefix,
                    status="Operational",
                    install_date=datetime.utcnow() - timedelta(days=int(np.random.uniform(100, 1000))),
                )
                db.add(machine)
            
            current_part = np.random.choice(parts)
            days_active = int(np.random.gamma(shape=2, scale=150))
            
            risk_score = 0.05
            rec = "Routine Check"
            
            if current_part == 'P-BRG-02' and days_active > 400:
                risk_score = float(np.random.uniform(0.65, 0.98))
                rec = "Recommend immediate replacement"
            elif days_active > 600:
                risk_score = float(np.random.uniform(0.52, 0.82))
                rec = "Schedule maintenance soon"
                
            log_entry = models.PredictionLog(
                machine_id=new_id,
                part_id=current_part,
                time_in_service_days=days_active,
                prediction_score=risk_score,
                recommendation=rec,
                prediction_timestamp=datetime.utcnow(),
            )
            db.add(log_entry)

        db.commit()
        print(f"Success! Fleet of {target_machines} synthetic machines initialized.")
    finally:
        db.close()

if __name__ == "__main__":
    generate_fleet()
