import logging
from typing import List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.prediction_log import PredictionLog
from app.models.work_order import utcnow
from app.repositories.machine_repository import MachineRepository
from app.repositories.part_repository import PartRepository
from app.repositories.prediction_repository import PredictionRepository
from app.schemas.prediction import PredictionRequest
from app.services import ml_loader
from app.services.exceptions import NotFoundError, ServiceUnavailableError

logger = logging.getLogger(__name__)

# Risk above these scores triggers the corresponding recommendation.
MAINTENANCE_THRESHOLD = 0.5
REPLACEMENT_THRESHOLD = 0.75


def recommend(risk_score: float) -> str:
    if risk_score > REPLACEMENT_THRESHOLD:
        return "Recommend immediate replacement"
    if risk_score > MAINTENANCE_THRESHOLD:
        return "Schedule maintenance soon"
    return "No action needed"


class PredictionService:
    """Orchestrates model inference, prediction logging and recommendations."""

    def __init__(self, db: Session):
        self.db = db
        self.machines = MachineRepository(db)
        self.parts = PartRepository(db)
        self.predictions = PredictionRepository(db)

    def _score(self, request: PredictionRequest, model_version: str) -> float:
        try:
            return float(ml_loader.make_prediction(request, model_version))
        except Exception:
            logger.exception("Prediction failed for machine %s, part %s", request.machine_id, request.part_id)
            raise ServiceUnavailableError("The prediction model is currently unavailable")

    def predict(self, request: PredictionRequest) -> PredictionLog:
        if self.machines.get(request.machine_id) is None:
            raise NotFoundError(f"Machine '{request.machine_id}' not found")
        if self.parts.get(request.part_id) is None:
            raise NotFoundError(f"Part '{request.part_id}' not found")

        model_version = settings.MODEL_VERSION
        risk_score = self._score(request, model_version)
        log = self.predictions.add(PredictionLog(
            machine_id=request.machine_id,
            part_id=request.part_id,
            time_in_service_days=request.time_in_service_days,
            prediction_score=risk_score,
            recommendation=recommend(risk_score),
            model_version=model_version,
        ))
        self.db.commit()
        self.db.refresh(log)
        return log

    def run_daily_scan(self) -> int:
        """Advances every machine's latest record by one day and stores a new prediction."""
        model_version = settings.MODEL_VERSION
        new_logs: List[PredictionLog] = []
        for latest in self.predictions.latest_per_machine():
            days = latest.time_in_service_days + 1
            request = PredictionRequest(
                machine_id=latest.machine_id, part_id=latest.part_id, time_in_service_days=days
            )
            try:
                risk_score = self._score(request, model_version)
            except ServiceUnavailableError:
                continue
            new_logs.append(PredictionLog(
                machine_id=latest.machine_id,
                part_id=latest.part_id,
                time_in_service_days=days,
                prediction_score=risk_score,
                recommendation=recommend(risk_score),
                prediction_timestamp=utcnow(),
                model_version=model_version,
            ))

        if new_logs:
            self.predictions.add_all(new_logs)
            self.db.commit()
        return len(new_logs)
