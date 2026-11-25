from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PredictionRequest(BaseModel):
    machine_id: str = Field(min_length=1, max_length=50)
    part_id: str = Field(min_length=1, max_length=50)
    time_in_service_days: int = Field(ge=0, le=36500)

    model_config = ConfigDict(json_schema_extra={
        "examples": [{"machine_id": "M-185", "part_id": "P-BRG-02", "time_in_service_days": 450}]
    })


class PredictionResponse(BaseModel):
    failure_risk: float
    recommendation: str
    prediction_id: Optional[int] = None
    model_version: Optional[str] = None


class PredictionLogInDB(BaseModel):
    id: int
    machine_id: str
    part_id: str
    time_in_service_days: int
    prediction_score: float
    recommendation: str
    prediction_timestamp: datetime
    model_version: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
