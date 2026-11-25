from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.schemas.part import PartStatsResponse
from app.services.part_service import PartService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/{part_id}/stats", response_model=PartStatsResponse)
def get_part_failure_stats(part_id: str, db: Session = Depends(get_db)):
    """
    Time-in-service days of past predictions for this part that crossed the
    maintenance threshold (risk above 0.5). Unknown parts return 404.
    """
    return PartStatsResponse(time_to_failure_days=PartService(db).failure_days(part_id))
