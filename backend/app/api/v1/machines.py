from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db import models
from app.db.database import get_db
from app.schemas.prediction import PredictionLogInDB

router = APIRouter()

@router.get("/{machine_id}/history", response_model=List[PredictionLogInDB])
def read_machine_history(machine_id: str, db: Session = Depends(get_db)):
    """
    Retrieve the prediction history for a specific machine.
    """
    history = db.query(models.PredictionLog).filter(models.PredictionLog.machine_id == machine_id).order_by(models.PredictionLog.prediction_timestamp.desc()).limit(100).all()
    return history