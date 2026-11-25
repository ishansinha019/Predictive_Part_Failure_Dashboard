import os
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import models
from app.core.security import get_password_hash

PARTS_CATALOG = [
    {
        "id": "P-BRG-02",
        "category": "Bearing",
        "name": "Heavy-Duty Main Roller Bearing",
        "expected_lifespan_days": 450,
        "unit_cost": 12000.0,
        "planned_repair_hours": 16.0,
        "unplanned_repair_hours": 56.0,
    },
    {
        "id": "P-GBX-01",
        "category": "Gearbox",
        "name": "Planetary High-Torque Gearbox",
        "expected_lifespan_days": 800,
        "unit_cost": 45000.0,
        "planned_repair_hours": 24.0,
        "unplanned_repair_hours": 112.0,
    },
    {
        "id": "P-MTR-05",
        "category": "Motor",
        "name": "Pitch/Yaw Drive Servo Motor",
        "expected_lifespan_days": 600,
        "unit_cost": 3500.0,
        "planned_repair_hours": 8.0,
        "unplanned_repair_hours": 32.0,
    },
    {
        "id": "P-VLV-01",
        "category": "Valve",
        "name": "Proportional Hydraulic Valve",
        "expected_lifespan_days": 400,
        "unit_cost": 600.0,
        "planned_repair_hours": 4.0,
        "unplanned_repair_hours": 16.0,
    },
    {
        "id": "P-SEN-04",
        "category": "Sensor",
        "name": "Piezoelectric Vibration Sensor",
        "expected_lifespan_days": 365,
        "unit_cost": 300.0,
        "planned_repair_hours": 2.0,
        "unplanned_repair_hours": 8.0,
    },
    {
        "id": "P-CTR-03",
        "category": "Controller",
        "name": "Embedded PLC Main Controller Unit",
        "expected_lifespan_days": 700,
        "unit_cost": 2500.0,
        "planned_repair_hours": 4.0,
        "unplanned_repair_hours": 24.0,
    },
]

def seed_database():
    db: Session = SessionLocal()
    try:
        print("--- 1. Seeding Default Users ---")
        default_users = [
            ("admin", "admin123", "admin"),
            ("technician", "tech123", "technician"),
            ("operator", "operator123", "viewer"),
        ]
        for uname, pwd, role in default_users:
            existing = db.query(models.User).filter(models.User.username == uname).first()
            if not existing:
                user = models.User(
                    username=uname,
                    hashed_password=get_password_hash(pwd),
                    role=role,
                )
                db.add(user)
                print(f"Created user: {uname} ({role})")

        print("--- 2. Seeding Parts Catalog ---")
        for part_data in PARTS_CATALOG:
            existing_part = db.query(models.Part).filter(models.Part.id == part_data["id"]).first()
            if not existing_part:
                db.add(models.Part(**part_data))
                print(f"Added part to catalog: {part_data['id']} - {part_data['name']}")

        db.commit()

        print("--- 3. Seeding Machines & Historical Logs from CSV ---")
        csv_path = "../ml_model/data/service_history_extended.csv"
        if not os.path.exists(csv_path):
            csv_path = "ml_model/data/service_history_extended.csv"

        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            
            # Seed unique machines first
            unique_machines = df['machine_id'].unique()
            for m_id in unique_machines:
                existing_m = db.query(models.Machine).filter(models.Machine.id == m_id).first()
                if not existing_m:
                    m_type = m_id.split('-')[0]
                    db.add(models.Machine(
                        id=m_id,
                        machine_type=m_type,
                        status="Operational",
                        install_date=datetime.utcnow() - timedelta(days=700),
                    ))
            db.commit()

            # Seed historical prediction logs
            log_count = db.query(models.PredictionLog).count()
            if log_count == 0:
                print(f"Loading historical logs from {csv_path}...")
                for _, row in df.iterrows():
                    score = 1.0 if row['part_failed'] == 1 else 0.0
                    rec = "Historical Failure" if row['part_failed'] == 1 else "Historical Pass"
                    log_entry = models.PredictionLog(
                        machine_id=row['machine_id'],
                        part_id=row['part_id'],
                        time_in_service_days=int(row['time_in_service_days']),
                        prediction_score=score,
                        recommendation=rec,
                        prediction_timestamp=pd.to_datetime(row['service_date']),
                    )
                    db.add(log_entry)
                db.commit()
                print(f"Successfully inserted {len(df)} historical service logs.")
        else:
            print(f"Warning: CSV dataset not found at {csv_path}")

        print("--- 4. Seeding Sample Work Orders ---")
        sample_wo = db.query(models.WorkOrder).first()
        sample_machine = db.get(models.Machine, "M-185")
        if not sample_wo and sample_machine is not None:
            db.add(models.WorkOrder(
                machine_id="M-185",
                part_id="P-BRG-02",
                status="Open",
                priority="Critical",
                estimated_cost=15000.0,
                scheduled_date=datetime.utcnow() + timedelta(days=2),
                notes="Scheduled early replacement due to elevated vibration profile."
            ))
            db.commit()
            print("Added initial sample work order.")

        print("--- Database Seeding Complete ---")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
