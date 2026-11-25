from pydantic import BaseModel, ConfigDict
from typing import List

class PartRef(BaseModel):
    id: str
    name: str
    category: str

    model_config = ConfigDict(from_attributes=True)


class PartStatsResponse(BaseModel):
    time_to_failure_days: List[int]

    model_config = ConfigDict(from_attributes=True)