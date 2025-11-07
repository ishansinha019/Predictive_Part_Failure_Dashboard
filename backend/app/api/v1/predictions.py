import traceback
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.ml_loader import make_prediction
from app.db import models
from app.db.database import get_db

router = APIRouter()

@router.post("/predict", response_model=PredictionResponse)
def predict_failure(request: PredictionRequest, db: Session = Depends(get_db)):
    """
    Predicts the failure risk and provides a recommendation.
    """
    try:
        # This returns a numpy.float32
        risk_score_raw = make_prediction(request, model_version="v1.0")
        # Convert it to a standard Python float
        risk_score = float(risk_score_raw)
        # Determine recommendation based on risk score
        recommendation = "No action needed"
        if risk_score > 0.75:
            recommendation = "Recommend immediate replacement"
        elif risk_score > 0.5:
            recommendation = "Schedule maintenance soon"

        # Log the prediction to the database
        log_entry = models.PredictionLog(
            machine_id=request.machine_id,
            part_id=request.part_id,
            time_in_service_days=request.time_in_service_days,
            prediction_score=risk_score,
            recommendation=recommendation
        )
        db.add(log_entry)
        db.commit()

        return PredictionResponse(failure_risk=risk_score, recommendation=recommendation)
    
    except Exception as e:
            print("\n---  PREDICTION FAILED :( ---")
            traceback.print_exc()
            print("---------------------------------\n")
            raise HTTPException(status_code=500, detail=str(e))