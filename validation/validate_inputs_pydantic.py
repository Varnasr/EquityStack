"""Validate input config using Pydantic schemas."""
from pydantic import BaseModel, validator

class Config(BaseModel):
    input_path: str
    report_year: int

    @validator("report_year")
    def validate_year(cls, v):
        if v < 2000 or v > 2030:
            raise ValueError("Invalid reporting year")
        return v