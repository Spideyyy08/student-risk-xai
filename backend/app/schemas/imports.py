"""
Data Ingestion and Bulk Import Schemas.
"""

from typing import List, Optional, Any, Union
from pydantic import BaseModel, ConfigDict


class RawImportRecord(BaseModel):
    roll: str
    name: Optional[str] = None
    division: Optional[str] = None
    attendance: Union[float, str, int]
    quiz: Union[float, str, int]
    assignment: Union[float, str, int]
    backlogs: Union[int, str]
    outcome: Optional[str] = None  # Optional Low/Medium/High ground-truth outcome label

    model_config = ConfigDict(extra="ignore")


class ImportBatchRequest(BaseModel):
    records: List[RawImportRecord]
    semester: Optional[str] = "sem5"

    model_config = ConfigDict(extra="ignore")


class RowError(BaseModel):
    row: int
    message: str


class ImportBatchResponse(BaseModel):
    success: bool = True
    message: str
    rows_total: int
    rows_ok: int
    rows_failed: int
    errors: List[RowError] = []

    model_config = ConfigDict(from_attributes=True)
