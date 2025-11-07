from pydantic import BaseModel
from datetime import datetime

class PredictionRequest(BaseModel):
    machine_id: str
    part_id: str
    time_in_service_days: int

class PredictionResponse(BaseModel):
    failure_risk: float
    recommendation: str

class PredictionLogInDB(BaseModel):
    id: int
    machine_id: str
    part_id: str
    prediction_score: float
    prediction_timestamp: datetime

    class Config:
        orm_mode = True