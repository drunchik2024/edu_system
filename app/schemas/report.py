from datetime import datetime
from pydantic import BaseModel
from app.models.report import ReportStatusEnum


class ReportStatusOut(BaseModel):
    id: int
    status: ReportStatusEnum
    status_label: str
    submitted_at: datetime | None
    approved_at: datetime | None
    approved_by_name: str | None
    model_config = {"from_attributes": True}
