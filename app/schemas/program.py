from pydantic import BaseModel
from app.models.program import ProgramLevel


class ProgramListItem(BaseModel):
    id: int
    name: str
    code: str
    level: ProgramLevel
    level_label: str
    start_year: int
    director_full_name: str

    model_config = {"from_attributes": True}


class ProgramDetail(ProgramListItem):
    description: str | None
    department_name: str
    discipline_count: int
    own_discipline_count: int
