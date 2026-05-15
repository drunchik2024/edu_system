from pydantic import BaseModel
from app.models.report import ReportStatusEnum


class DisciplineListItem(BaseModel):
    id: int
    name: str
    code: str
    program_name: str
    program_id: int
    teacher_primary_name: str
    teacher_secondary_name: str
    report_status: ReportStatusEnum | None
    report_status_label: str

    model_config = {"from_attributes": True}


class DisciplineDetail(DisciplineListItem):
    goals: str | None
    objectives: str | None
    outcomes: str | None
    department_name: str
