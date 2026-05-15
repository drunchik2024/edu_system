from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, get_head
from app.database import get_db
from app.models.report_file import ReportFile
from app.models.user import User
from app.services import disciplines as svc_disc
from app.services import reports as svc

router = APIRouter(prefix="/reports", tags=["reports"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/discipline/{discipline_id}", response_class=HTMLResponse)
async def checklist_page(
    discipline_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    discipline = await svc_disc.get_discipline_by_id(db, discipline_id)
    if not discipline:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")

    categories = await svc.get_checklist(db, discipline_id)
    report_status = await svc.get_or_create_report_status(db, discipline_id)
    report_files = await svc.get_report_files(db, discipline_id)

    return templates.TemplateResponse(
        "reports/checklist.html",
        {
            "request": request,
            "discipline": discipline,
            "categories": categories,
            "report_status": report_status,
            "report_files": report_files,
            "user": current_user,
        },
    )


@router.post("/discipline/{discipline_id}/category")
async def add_category(
    discipline_id: int,
    name: str = Form(...),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_head),
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Название категории обязательно")
    cat = await svc.create_category(db, discipline_id, name, current_user.id)
    if file and file.filename:
        await svc.add_report_file(db, discipline_id, current_user.id, file, category_id=cat.id)
    return RedirectResponse(url=f"/reports/discipline/{discipline_id}", status_code=303)


@router.post("/discipline/{discipline_id}/category/{category_id}/delete")
async def delete_category(
    discipline_id: int,
    category_id: int,
    current_user: User = Depends(get_head),
    db: AsyncSession = Depends(get_db),
):
    await svc.delete_category(db, category_id)
    return RedirectResponse(url=f"/reports/discipline/{discipline_id}", status_code=303)


@router.post("/discipline/{discipline_id}/item")
async def add_item(
    discipline_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_head),
):
    form = await request.form()
    title = form.get("title", "").strip()
    category_id = int(form.get("category_id", 0))
    if not title or not category_id:
        raise HTTPException(status_code=400, detail="Заполните все поля")
    await svc.create_item(db, category_id, title, current_user.id)
    return RedirectResponse(url=f"/reports/discipline/{discipline_id}", status_code=303)


@router.post("/item/{item_id}/toggle")
async def toggle_item(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_head),
):
    form = await request.form()
    discipline_id = int(form.get("discipline_id", 0))
    is_done = form.get("is_done") == "true"
    await svc.update_item(db, item_id, is_done=is_done, comment=None)
    return RedirectResponse(url=f"/reports/discipline/{discipline_id}", status_code=303)


@router.post("/item/{item_id}/comment")
async def update_comment(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_head),
):
    form = await request.form()
    discipline_id = int(form.get("discipline_id", 0))
    comment = form.get("comment", "").strip() or None
    await svc.update_item(db, item_id, is_done=None, comment=comment)
    return RedirectResponse(url=f"/reports/discipline/{discipline_id}", status_code=303)


@router.post("/item/{item_id}/delete")
async def delete_item(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_head),
):
    form = await request.form()
    discipline_id = int(form.get("discipline_id", 0))
    await svc.delete_item(db, item_id)
    return RedirectResponse(url=f"/reports/discipline/{discipline_id}", status_code=303)


@router.post("/discipline/{discipline_id}/submit")
async def submit_report(
    discipline_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Заведующий кафедры минует статус "на утверждении" — отчёт сразу утверждается
    auto_approve = current_user.role.name == "head_of_department"
    await svc.submit_report(db, discipline_id, current_user.id, auto_approve=auto_approve)
    return RedirectResponse(url=f"/reports/discipline/{discipline_id}", status_code=303)


@router.post("/discipline/{discipline_id}/approve")
async def approve_report(
    discipline_id: int,
    current_user: User = Depends(get_head),
    db: AsyncSession = Depends(get_db),
):
    await svc.approve_report(db, discipline_id, current_user.id)
    return RedirectResponse(url=f"/reports/discipline/{discipline_id}", status_code=303)


@router.post("/discipline/{discipline_id}/reset")
async def reset_report(
    discipline_id: int,
    current_user: User = Depends(get_head),
    db: AsyncSession = Depends(get_db),
):
    await svc.reset_report(db, discipline_id)
    return RedirectResponse(url=f"/reports/discipline/{discipline_id}", status_code=303)


@router.post("/files/{file_id}/feedback")
async def save_file_feedback(
    file_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_head),
):
    form = await request.form()
    feedback = form.get("feedback", "").strip() or None
    discipline_id = int(form.get("discipline_id", 0))
    await svc.save_file_feedback(db, file_id, feedback)
    return RedirectResponse(url=f"/reports/discipline/{discipline_id}", status_code=303)


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ReportFile).where(ReportFile.id == file_id))
    rf = result.scalar_one_or_none()
    if not rf:
        raise HTTPException(status_code=404, detail="Файл не найден")
    path = svc.UPLOAD_DIR / rf.stored_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден на диске")
    return FileResponse(
        path=str(path),
        filename=rf.original_name,
        media_type=rf.content_type,
    )


@router.post("/files/{file_id}/delete")
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_head),
):
    result = await db.execute(select(ReportFile).where(ReportFile.id == file_id))
    rf = result.scalar_one_or_none()
    discipline_id = rf.discipline_id if rf else 0
    await svc.delete_report_file(db, file_id)
    return RedirectResponse(url=f"/reports/discipline/{discipline_id}", status_code=303)
