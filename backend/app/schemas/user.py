from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=72)
    role: UserRole = UserRole.TECHNICIAN

    model_config = ConfigDict(json_schema_extra={
        "examples": [{"username": "jane.doe", "password": "a-long-passphrase", "role": "technician"}]
    })


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TechnicianSummary(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)
