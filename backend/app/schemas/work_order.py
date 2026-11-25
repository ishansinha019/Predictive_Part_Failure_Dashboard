from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import WorkOrderPriority, WorkOrderStatus
from app.schemas.machine import MachineRef
from app.schemas.part import PartRef
from app.schemas.user import TechnicianSummary


class WorkOrderCreate(BaseModel):
    machine_id: str = Field(min_length=1, max_length=50)
    part_id: str = Field(min_length=1, max_length=50)
    # Planned maintenance raised from a model prediction for this machine and part.
    prediction_id: Optional[int] = Field(default=None, ge=1)
    # Derived from the prediction risk (or Medium without one) when omitted.
    priority: Optional[WorkOrderPriority] = None
    # Defaults to the part's unit cost when omitted.
    estimated_cost: Optional[float] = Field(default=None, ge=0)
    scheduled_date: Optional[datetime] = None
    assigned_technician_id: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = Field(default=None, max_length=2000)

    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "machine_id": "M-185",
            "part_id": "P-BRG-02",
            "prediction_id": 42,
            "scheduled_date": "2026-12-01T08:00:00",
            "notes": "Replace during the planned outage.",
        }]
    })


class WorkOrderUpdate(BaseModel):
    status: Optional[WorkOrderStatus] = None
    priority: Optional[WorkOrderPriority] = None
    scheduled_date: Optional[datetime] = None
    # Send null explicitly to unassign.
    assigned_technician_id: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = Field(default=None, max_length=2000)

    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "In_Progress"}]})

    @model_validator(mode="after")
    def require_a_change(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        for field in ("status", "priority"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class WorkOrderResponse(BaseModel):
    id: int
    machine: MachineRef
    part: PartRef
    status: str
    priority: str
    estimated_cost: float
    scheduled_date: Optional[datetime] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    assigned_technician: Optional[TechnicianSummary] = None
    prediction_log_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
