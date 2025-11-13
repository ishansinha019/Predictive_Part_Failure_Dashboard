from pydantic import BaseModel, ConfigDict
from typing import List

class PartStatsResponse(BaseModel):
    time_to_failure_days: List[int]

    model_config = ConfigDict(from_attributes=True)