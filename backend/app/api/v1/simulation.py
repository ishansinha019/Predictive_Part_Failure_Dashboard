from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db import models
from app.db.database import get_db
from app.services.ml_loader import make_prediction
from app.schemas.prediction import PredictionRequest

router = APIRouter()

@router.post("/daily-scan")
def run_daily_fleet_scan(db: Session = Depends(get_db)):
    """
    Simulates the passage of one day.
    Iterates through the LATEST record for every machine, 
    increments time_in_service by 1, and saves a new prediction.
    """
    print("--- 🔄 STARTING DAILY FLEET SCAN ---")
    
    # 1. Get the latest log for each unique machine
    # We use a subquery approach or distinct on machine_id to get the last state
    # For compatibility, we'll fetch all and filter in Python (efficient enough for <1000 machines)
    all_logs = db.query(models.PredictionLog).order_by(models.PredictionLog.prediction_timestamp.desc()).all()
    
    # Filter to get only the unique latest log per machine
    latest_logs = {}
    for log in all_logs:
        if log.machine_id not in latest_logs:
            latest_logs[log.machine_id] = log
            
    new_logs = []
    
    for machine_id, log in latest_logs.items():
        # 2. Simulate 1 day passing
        new_days = log.time_in_service_days + 1
        part_id = log.part_id
        
        # 3. Create prediction request
        # Note: We rely on the model's logic to handle the risk calculation
        pred_req = PredictionRequest(
            machine_id=machine_id,
            part_id=part_id,
            time_in_service_days=new_days
        )
        
        try:
            # 4. Get new risk score
            # Returns a numpy float, so we convert to python float
            raw_risk = make_prediction(pred_req) 
            risk_score = float(raw_risk)
            
            # Determine recommendation
            rec = "Routine Check"
            if risk_score > 0.75:
                rec = "CRITICAL: Inspect Immediately"
            elif risk_score > 0.5:
                rec = "High Risk: Schedule Maintenance"
            
            # 5. Create new DB Entry
            new_log = models.PredictionLog(
                machine_id=machine_id,
                part_id=part_id,
                time_in_service_days=new_days,
                prediction_score=risk_score,
                recommendation=rec,
                prediction_timestamp=datetime.now()
            )
            new_logs.append(new_log)
            
        except Exception as e:
            print(f"Error predicting for {machine_id}: {e}")
            continue

    # 6. Bulk save to database
    if new_logs:
        db.add_all(new_logs)
        db.commit()
        
    print(f"--- ✅ SCAN COMPLETE. Updated {len(new_logs)} machines. ---")
    return {"message": f"Daily scan complete. {len(new_logs)} machines updated.", "machines_scanned": len(new_logs)}