from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.enums import MachineStatus
from app.schemas.machine import FleetSortField, MachineSummary, SortOrder
from app.schemas.prediction import PredictionLogInDB
from app.services.machine_service import MachineService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=List[MachineSummary])
def get_all_machines(
    response: Response,
    skip: int = Query(0, ge=0, description="Number of machines to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum machines to return"),
    search: Optional[str] = Query(None, max_length=50, description="Case-insensitive machine ID substring"),
    status: Optional[MachineStatus] = Query(None, description="Only machines with this status"),
    sort_by: FleetSortField = Query("machine_id", description="Sort field"),
    order: SortOrder = Query("asc", description="Sort direction"),
    db: Session = Depends(get_db),
):
    """
    List the fleet with each machine's latest risk. The total number of
    matching machines is returned in the `X-Total-Count` header.
    """
    machines, total = MachineService(db).list_fleet(
        skip=skip,
        limit=limit,
        search=search,
        status=status.value if status else None,
        sort_by=sort_by,
        order=order,
    )
    response.headers["X-Total-Count"] = str(total)
    return machines


@router.get("/{machine_id}/history", response_model=List[PredictionLogInDB])
def read_machine_history(
    machine_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Prediction history for a machine, newest first. Unknown machines return 404."""
    return MachineService(db).history(machine_id, skip=skip, limit=limit)
