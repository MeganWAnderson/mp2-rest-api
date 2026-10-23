"""
Data Models
DS 3500 - MP2

Defines Pydantic models for REST API responses.

Specifies the structure and data types for health check
responses and dataset metadata returned by the API.
"""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str


class DatasetInfo(BaseModel):
    # TODO: id (int), filename (str), rows (int),
    # columns (int), column_names (list[str])
    id: int
    filename: str
    rows: int
    columns: int
    column_names: list[str]
