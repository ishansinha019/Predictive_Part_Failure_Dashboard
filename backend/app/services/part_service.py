from typing import List

from sqlalchemy.orm import Session

from app.repositories.part_repository import PartRepository
from app.repositories.prediction_repository import PredictionRepository
from app.services.exceptions import NotFoundError
from app.services.prediction_service import MAINTENANCE_THRESHOLD


class PartService:
    def __init__(self, db: Session):
        self.parts = PartRepository(db)
        self.predictions = PredictionRepository(db)

    def failure_days(self, part_id: str) -> List[int]:
        """Time in service of past predictions that crossed the maintenance threshold."""
        if self.parts.get(part_id) is None:
            raise NotFoundError(f"Part '{part_id}' not found")
        return self.predictions.failure_days_for_part(part_id, min_score=MAINTENANCE_THRESHOLD)
