from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel 

from app.db import models
from app.db.database import get_db
from app.schemas.prediction import PredictionLogInDB

# Define a simple schema for the machine list
class MachineSummary(BaseModel):
    machine_id: str
    last_updated: str

router = APIRouter()

# --- 1. GET ALL MACHINES (For Fleet Page) ---
@router.get("/", response_model=List[MachineSummary])
def get_all_machines(db: Session = Depends(get_db)):
    """
    Get a list of all unique machines in the fleet.
    """
    # Efficient query to get distinct machine_ids
    unique_machines = db.query(models.PredictionLog.machine_id).distinct().all()
    
    results = []
    for (m_id,) in unique_machines:
        # For each machine, just return its ID (and a dummy date for now)
        results.append({"machine_id": m_id, "last_updated": "2023-01-01"})
    
    return results

# --- 2. GET MACHINE HISTORY (For Detail Page) ---
@router.get("/{machine_id}/history", response_model=List[PredictionLogInDB])
def read_machine_history(machine_id: str, db: Session = Depends(get_db)):
    """
    Retrieve the prediction history for a specific machine.
    """
    history = db.query(models.PredictionLog)\
                .filter(models.PredictionLog.machine_id == machine_id)\
                .order_by(models.PredictionLog.prediction_timestamp.desc())\
                .limit(100)\
                .all()
    return history