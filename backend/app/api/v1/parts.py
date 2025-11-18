from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db import models
from app.db.database import get_db
from app.schemas.part import PartStatsResponse

router = APIRouter()

@router.get("/{part_id}/stats", response_model=PartStatsResponse)
def get_part_failure_stats(part_id: str, db: Session = Depends(get_db)):
    """
    Retrieve the time-in-service days for all historical failures
    of a specific part.
    """
    
    # We query the log for the given part_id where the prediction
    # score was high (e.g., > 0.5), indicating a failure or high risk.
    failure_logs = db.query(models.PredictionLog.time_in_service_days)\
                     .filter(models.PredictionLog.part_id == part_id)\
                     .filter(models.PredictionLog.prediction_score > 0.5)\
                     .all()
    
    # The query returns a list of tuples, so we flatten it
    days_list = [days for (days,) in failure_logs]
    
    return PartStatsResponse(time_to_failure_days=days_list)