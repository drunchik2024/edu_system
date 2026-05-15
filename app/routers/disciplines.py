from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.services import disciplines as svc

router = APIRouter(prefix="/disciplines", tags=["disciplines"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def disciplines_list(
    request: Request,
    program_id: int | None = None,
    sort_by: Literal["name", "code"] = "name",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    disciplines = await svc.get_disciplines_for_department(
        db, current_user.department_id, program_id=program_id, sort_by=sort_by
    )
    return templates.TemplateResponse(
        "disciplines/list.html",
        {
            "request": request,
            "disciplines": disciplines,
            "sort_by": sort_by,
            "program_id": program_id,
            "user": current_user,
        },
    )


@router.get("/{discipline_id}", response_class=HTMLResponse)
async def discipline_detail(
    discipline_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    discipline = await svc.get_discipline_by_id(db, discipline_id)
    if not discipline:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")
    return templates.TemplateResponse(
        "disciplines/detail.html",
        {"request": request, "discipline": discipline, "user": current_user},
    )
