import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, get_rop
from app.database import get_db
from app.models.user import User
from app.services import rop as svc

router = APIRouter(prefix="/programs", tags=["rop"])
api_router = APIRouter(prefix="/api", tags=["rop-api"])
templates = Jinja2Templates(directory="app/templates")

_LEVELS = [
    ("bachelor",    "Бакалавриат"),
    ("specialist",  "Специалитет"),
    ("master",      "Магистратура"),
    ("postgraduate","Аспирантура"),
]
_ED_FORMS = [
    ("full_time", "Очная"),
    ("part_time", "Заочная"),
    ("mixed",     "Очно-заочная"),
]


# ─── Форма создания программы ──────────────────────────────────────────────────

@router.get("/new", response_class=HTMLResponse)
async def create_program_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_rop),
):
    competencies = await svc.get_all_competencies(db)
    return templates.TemplateResponse("rop/form.html", {
        "request": request,
        "user": current_user,
        "program": None,
        "levels": _LEVELS,
        "ed_forms": _ED_FORMS,
        "competencies_json": json.dumps(competencies, ensure_ascii=False),
    })


@router.post("/create")
async def create_program(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_rop),
):
    form = await request.form()
    data = _extract_program_data(form, current_user)

    # Файлы программы
    standard_file   = form.get("standard_file")
    curriculum_file = form.get("curriculum_file")
    title_page_file = form.get("title_page_file")

    p = await svc.create_program(db, data, current_user.id)

    # Загружаем PDF-файлы если переданы
    for field_name, file_field in [
        ("standard", standard_file),
        ("curriculum", curriculum_file),
        ("title_page", title_page_file),
    ]:
        if isinstance(file_field, UploadFile) and file_field.filename:
            await svc.upload_program_pdf(db, p.id, current_user.id, field_name, file_field)

    # Компетенции
    comp_ids = _parse_ids(form.get("competency_ids", ""))
    if comp_ids:
        await svc.set_program_competencies(db, p.id, comp_ids)

    # Дисциплины (текстовый список)
    disc_names = form.getlist("discipline_names")
    if disc_names:
        await svc.set_program_disciplines(db, p.id, disc_names)

    # Области профессиональной деятельности
    areas = _parse_areas(form)
    if areas:
        await svc.set_professional_areas(db, p.id, areas)

    return RedirectResponse(url=f"/programs/{p.id}/edit", status_code=303)


# ─── Форма редактирования программы ───────────────────────────────────────────

@router.get("/{program_id}/edit", response_class=HTMLResponse)
async def edit_program_page(
    program_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_rop),
):
    program = await svc.get_program_for_rop(db, program_id, current_user.id)
    if not program:
        raise HTTPException(status_code=404, detail="Программа не найдена")

    competencies = await svc.get_all_competencies(db)
    return templates.TemplateResponse("rop/form.html", {
        "request": request,
        "user": current_user,
        "program": program,
        "levels": _LEVELS,
        "ed_forms": _ED_FORMS,
        "competencies_json": json.dumps(competencies, ensure_ascii=False),
    })


@router.post("/{program_id}/update")
async def update_program(
    program_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_rop),
):
    form = await request.form()
    data = _extract_program_data(form, current_user)

    await svc.update_program(db, program_id, current_user.id, data)

    # Новые PDF-файлы (если пользователь выбрал новый файл)
    for field_name, form_field in [
        ("standard",   form.get("standard_file")),
        ("curriculum", form.get("curriculum_file")),
        ("title_page", form.get("title_page_file")),
    ]:
        if isinstance(form_field, UploadFile) and form_field.filename:
            await svc.upload_program_pdf(db, program_id, current_user.id, field_name, form_field)

    # Компетенции
    comp_ids = _parse_ids(form.get("competency_ids", ""))
    await svc.set_program_competencies(db, program_id, comp_ids)

    # Дисциплины
    disc_names = form.getlist("discipline_names")
    await svc.set_program_disciplines(db, program_id, disc_names)

    # Области профессиональной деятельности
    areas = _parse_areas(form)
    await svc.set_professional_areas(db, program_id, areas)

    return RedirectResponse(url=f"/programs/{program_id}/edit", status_code=303)


@router.post("/{program_id}/delete")
async def delete_program(
    program_id: int,
    current_user: User = Depends(get_rop),
    db: AsyncSession = Depends(get_db),
):
    await svc.delete_program(db, program_id, current_user.id)
    return RedirectResponse(url="/programs", status_code=303)


# ─── Загрузка PDF-файлов программы ────────────────────────────────────────────

@router.post("/{program_id}/upload/{file_type}")
async def upload_pdf(
    program_id: int,
    file_type: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_rop),
):
    await svc.upload_program_pdf(db, program_id, current_user.id, file_type, file)
    return RedirectResponse(url=f"/programs/{program_id}/edit", status_code=303)


# ─── Рецензии ─────────────────────────────────────────────────────────────────

@router.post("/{program_id}/reviews")
async def add_review(
    program_id: int,
    name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_rop),
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Название рецензии обязательно")
    await svc.add_review(db, program_id, current_user.id, name, file)
    return RedirectResponse(url=f"/programs/{program_id}/edit", status_code=303)


@router.post("/reviews/{review_id}/delete")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_rop),
):
    program_id = await svc.delete_review(db, review_id, current_user.id)
    return RedirectResponse(url=f"/programs/{program_id}/edit", status_code=303)


# ─── Скачивание файла программы ───────────────────────────────────────────────

@router.get("/files/{stored_name}/download")
async def download_program_file(
    stored_name: str,
    current_user: User = Depends(get_current_user),
):
    from app.services.rop import UPLOAD_DIR
    path = UPLOAD_DIR / stored_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(path=str(path), filename=stored_name, media_type="application/pdf")


# ─── API компетенций (JSON) ───────────────────────────────────────────────────

@api_router.get("/competencies", response_class=JSONResponse)
async def list_competencies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_rop),
):
    return await svc.get_all_competencies(db)


@api_router.post("/competencies", response_class=JSONResponse)
async def create_competency(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_rop),
):
    body = await request.json()
    code = (body.get("code") or "").strip()
    description = (body.get("description") or "").strip()
    ctype = (body.get("type") or "").strip()
    if not code or not description or ctype not in ("uk", "opk", "pk"):
        raise HTTPException(status_code=400, detail="Заполните все поля (code, description, type)")
    c = await svc.create_competency(db, code, description, ctype)
    return {"id": c.id, "code": c.code, "description": c.description, "type": c.type.value}


# ─── Вспомогательные функции ──────────────────────────────────────────────────

def _extract_program_data(form, current_user: User) -> dict:
    return {
        "name":               (form.get("name") or "").strip(),
        "code":               (form.get("code") or "").strip(),
        "level":              form.get("level", "bachelor"),
        "start_year":         form.get("start_year", "2024"),
        "description":        (form.get("description") or "").strip(),
        "department_id":      current_user.department_id,
        "education_form":     form.get("education_form") or None,
        "education_duration": (form.get("education_duration") or "").strip() or None,
        "activity_types":     (form.get("activity_types") or "").strip() or None,
        "structure_text":     (form.get("structure_text") or "").strip() or None,
        "practices":          (form.get("practices") or "").strip() or None,
    }


def _parse_ids(raw: str) -> list[int]:
    """Парсит строку вида '1,2,3' или JSON-массив в список int."""
    raw = (raw or "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [int(x) for x in parsed]
    except (ValueError, TypeError):
        pass
    return [int(x) for x in raw.split(",") if x.strip().isdigit()]


def _parse_areas(form) -> list[dict]:
    """Собирает области деятельности из form-полей area_number[] и area_description[]."""
    numbers = form.getlist("area_number")
    descriptions = form.getlist("area_description")
    result = []
    for num, desc in zip(numbers, descriptions):
        num = (num or "").strip()
        if num:
            result.append({"number": num, "description": desc or ""})
    return result
