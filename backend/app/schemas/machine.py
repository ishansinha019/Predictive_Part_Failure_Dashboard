from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


class MachineSummary(BaseModel):
    machine_id: str
    machine_type: str
    status: str
    # Timestamp of the latest prediction; None when the machine has none yet.
    last_updated: Optional[datetime] = None
    latest_risk_score: Optional[float] = None
    latest_recommendation: Optional[str] = None

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "machine_id": "M-185",
            "machine_type": "M",
            "status": "Operational",
            "last_updated": "2026-11-25T09:30:00",
            "latest_risk_score": 0.82,
            "latest_recommendation": "Recommend immediate replacement",
        }]
    })


class MachineRef(BaseModel):
    id: str
    machine_type: str
    status: str

    model_config = ConfigDict(from_attributes=True)


FleetSortField = Literal["machine_id", "last_updated", "risk"]
SortOrder = Literal["asc", "desc"]
