from pydantic import BaseModel


class ChecklistItemOut(BaseModel):
    id: int
    title: str
    is_done: bool
    comment: str | None
    model_config = {"from_attributes": True}


class ChecklistItemCreate(BaseModel):
    title: str
    category_id: int


class ChecklistItemUpdate(BaseModel):
    is_done: bool | None = None
    comment: str | None = None


class ChecklistCategoryOut(BaseModel):
    id: int
    name: str
    items: list[ChecklistItemOut] = []
    model_config = {"from_attributes": True}


class ChecklistCategoryCreate(BaseModel):
    name: str
    discipline_id: int
