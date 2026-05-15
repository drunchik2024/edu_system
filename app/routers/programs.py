from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.services import disciplines as svc_disciplines
from app.services import programs as svc_programs
from app.services import rop as svc_rop

router = APIRouter(prefix="/programs", tags=["programs"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def programs_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Руководитель ОП видит только свои программы в отдельном шаблоне
    if current_user.role.name == "program_director":
        programs = await svc_rop.get_programs_for_rop(db, current_user.id)
        return templates.TemplateResponse("rop/list.html", {
            "request": request,
            "programs": programs,
            "user": current_user,
        })

    programs = await svc_programs.get_programs_for_department(db, current_user.department_id)
    return templates.TemplateResponse(
        "programs/list.html",
        {
            "request": request,
            "programs": programs,
            "user": current_user,
        },
    )


@router.get("/{program_id}", response_class=HTMLResponse)
async def program_detail(
    program_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # РОП переходит на форму редактирования
    if current_user.role.name == "program_director":
        return RedirectResponse(url=f"/programs/{program_id}/edit")

    program = await svc_programs.get_program_by_id(db, program_id, current_user.department_id)
    if not program:
        raise HTTPException(status_code=404, detail="Программа не найдена")

    own_disciplines = await svc_disciplines.get_disciplines_for_department(
        db, current_user.department_id, program_id=program_id
    )
    external_disciplines = await svc_disciplines.get_external_disciplines(
        db, program_id, current_user.department_id
    )
    return templates.TemplateResponse(
        "programs/detail.html",
        {
            "request": request,
            "program": program,
            "own_disciplines": own_disciplines,
            "external_disciplines": external_disciplines,
            "user": current_user,
        },
    )
