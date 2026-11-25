from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.database import get_db
from app.services.prediction_service import PredictionService

# The scan writes a prediction for every machine, so it is administrator-only.
router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/daily-scan")
def run_daily_fleet_scan(db: Session = Depends(get_db)):
    """
    Simulates the passage of one day: takes the latest record of every
    machine, adds one day in service and stores a new prediction.
    """
    scanned = PredictionService(db).run_daily_scan()
    return {"message": f"Daily scan complete. {scanned} machines updated.", "machines_scanned": scanned}
