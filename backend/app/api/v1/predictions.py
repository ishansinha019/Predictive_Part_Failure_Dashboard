from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_operator
from app.db.database import get_db
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction_service import PredictionService

# Predictions are stored, so read-only viewers are excluded.
router = APIRouter(dependencies=[Depends(require_operator)])


@router.post("/predict", response_model=PredictionResponse)
def predict_failure(request: PredictionRequest, db: Session = Depends(get_db)):
    """
    Predicts the failure risk, stores the result in the machine history and
    returns a recommendation. Use the returned `prediction_id` to raise a
    work order. Unknown machines or parts return 404.
    """
    log = PredictionService(db).predict(request)
    return PredictionResponse(
        failure_risk=log.prediction_score,
        recommendation=log.recommendation,
        prediction_id=log.id,
        model_version=log.model_version,
    )
