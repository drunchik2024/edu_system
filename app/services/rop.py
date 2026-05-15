import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.program import EducationalProgram, ProgramLevel, EducationFormEnum
from app.models.rop import (
    Competency, CompetencyType,
    ProgramCompetency, ProgramDisciplineItem,
    ProgramReview, ProfessionalArea,
)

UPLOAD_DIR = Path("app/static/uploads")
ALLOWED_PDF = {"application/pdf"}
MAX_SIZE = 20 * 1024 * 1024  # 20 МБ


# ─── Список программ РОП ──────────────────────────────────────────────────────

async def get_programs_for_rop(db: AsyncSession, director_id: int) -> list[dict]:
    result = await db.execute(
        select(EducationalProgram)
        .options(selectinload(EducationalProgram.director), selectinload(EducationalProgram.department))
        .where(EducationalProgram.director_id == director_id)
        .order_by(EducationalProgram.name)
    )
    return [_program_to_dict(p) for p in result.scalars().all()]


async def get_program_for_rop(
    db: AsyncSession, program_id: int, director_id: int
) -> dict | None:
    result = await db.execute(
        select(EducationalProgram)
        .options(
            selectinload(EducationalProgram.director),
            selectinload(EducationalProgram.department),
            selectinload(EducationalProgram.competencies).selectinload(ProgramCompetency.competency),
            selectinload(EducationalProgram.discipline_items),
            selectinload(EducationalProgram.reviews),
            selectinload(EducationalProgram.professional_areas),
        )
        .where(EducationalProgram.id == program_id, EducationalProgram.director_id == director_id)
    )
    p = result.scalar_one_or_none()
    return _program_to_dict(p, full=True) if p else None


def _program_to_dict(p: EducationalProgram, full: bool = False) -> dict:
    base = {
        "id": p.id,
        "name": p.name,
        "code": p.code,
        "level": p.level,
        "level_label": p.level.label,
        "start_year": p.start_year,
        "director_full_name": p.director.full_name,
        "department_name": p.department.name,
        "education_form": p.education_form,
        "education_form_label": p.education_form.label if p.education_form else "",
        "education_duration": p.education_duration or "",
        "description": p.description or "",
        "standard_file": p.standard_file,
        "curriculum_file": p.curriculum_file,
        "title_page_file": p.title_page_file,
        "activity_types": p.activity_types or "",
        "structure_text": p.structure_text or "",
        "practices": p.practices or "",
    }
    if full:
        base["competencies"] = [
            {
                "id": pc.competency.id,
                "code": pc.competency.code,
                "description": pc.competency.description,
                "type": pc.competency.type.value,
                "type_label": pc.competency.type.label,
            }
            for pc in p.competencies
        ]
        base["discipline_items"] = [
            {"id": di.id, "name": di.name, "order_index": di.order_index}
            for di in p.discipline_items
        ]
        base["reviews"] = [
            {"id": r.id, "name": r.name, "stored_name": r.stored_name, "original_name": r.original_name}
            for r in p.reviews
        ]
        base["professional_areas"] = [
            {"id": pa.id, "number": pa.number, "description": pa.description or ""}
            for pa in p.professional_areas
        ]
    return base


# ─── CRUD программы ────────────────────────────────────────────────────────────

async def create_program(db: AsyncSession, data: dict, director_id: int) -> EducationalProgram:
    p = EducationalProgram(
        name=data["name"],
        code=data["code"],
        level=ProgramLevel(data["level"]),
        start_year=int(data["start_year"]),
        description=data.get("description") or None,
        director_id=director_id,
        department_id=int(data["department_id"]),
        education_form=EducationFormEnum(data["education_form"]) if data.get("education_form") else None,
        education_duration=data.get("education_duration") or None,
        activity_types=data.get("activity_types") or None,
        structure_text=data.get("structure_text") or None,
        practices=data.get("practices") or None,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def update_program(db: AsyncSession, program_id: int, director_id: int, data: dict) -> EducationalProgram:
    result = await db.execute(
        select(EducationalProgram).where(
            EducationalProgram.id == program_id,
            EducationalProgram.director_id == director_id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Программа не найдена")

    p.name = data["name"]
    p.code = data["code"]
    p.level = ProgramLevel(data["level"])
    p.start_year = int(data["start_year"])
    p.description = data.get("description") or None
    p.education_form = EducationFormEnum(data["education_form"]) if data.get("education_form") else None
    p.education_duration = data.get("education_duration") or None
    p.activity_types = data.get("activity_types") or None
    p.structure_text = data.get("structure_text") or None
    p.practices = data.get("practices") or None
    await db.commit()
    await db.refresh(p)
    return p


async def delete_program(db: AsyncSession, program_id: int, director_id: int) -> None:
    result = await db.execute(
        select(EducationalProgram).where(
            EducationalProgram.id == program_id,
            EducationalProgram.director_id == director_id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Программа не найдена")
    # Удаляем файлы с диска
    for fname in [p.standard_file, p.curriculum_file, p.title_page_file]:
        if fname:
            _delete_file(fname)
    await db.delete(p)
    await db.commit()


# ─── Загрузка PDF-файлов программы ────────────────────────────────────────────

async def upload_program_pdf(
    db: AsyncSession, program_id: int, director_id: int,
    file_type: str, file: UploadFile,
) -> str:
    """Загружает PDF и обновляет соответствующее поле программы."""
    if file_type not in ("standard", "curriculum", "title_page"):
        raise HTTPException(status_code=400, detail="Неизвестный тип файла")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 20 МБ)")
    ct = file.content_type or ""
    if ct not in ALLOWED_PDF:
        raise HTTPException(status_code=400, detail="Разрешены только PDF-файлы")

    result = await db.execute(
        select(EducationalProgram).where(
            EducationalProgram.id == program_id,
            EducationalProgram.director_id == director_id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Программа не найдена")

    # Удаляем старый файл если есть
    old = getattr(p, f"{file_type}_file")
    if old:
        _delete_file(old)

    stored_name = f"{uuid.uuid4().hex}.pdf"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / stored_name).write_bytes(content)

    setattr(p, f"{file_type}_file", stored_name)
    await db.commit()
    return stored_name


# ─── Рецензии ─────────────────────────────────────────────────────────────────

async def add_review(
    db: AsyncSession, program_id: int, director_id: int,
    name: str, file: UploadFile,
) -> ProgramReview:
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 20 МБ)")
    if (file.content_type or "") not in ALLOWED_PDF:
        raise HTTPException(status_code=400, detail="Разрешены только PDF-файлы")

    # Проверяем права
    res = await db.execute(
        select(EducationalProgram).where(
            EducationalProgram.id == program_id,
            EducationalProgram.director_id == director_id,
        )
    )
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Программа не найдена")

    stored_name = f"{uuid.uuid4().hex}.pdf"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / stored_name).write_bytes(content)

    rv = ProgramReview(
        program_id=program_id,
        name=name,
        stored_name=stored_name,
        original_name=file.filename or stored_name,
    )
    db.add(rv)
    await db.commit()
    await db.refresh(rv)
    return rv


async def delete_review(db: AsyncSession, review_id: int, director_id: int) -> int:
    result = await db.execute(
        select(ProgramReview)
        .options(selectinload(ProgramReview.program))
        .where(ProgramReview.id == review_id)
    )
    rv = result.scalar_one_or_none()
    if not rv or rv.program.director_id != director_id:
        raise HTTPException(status_code=404, detail="Рецензия не найдена")
    program_id = rv.program_id
    _delete_file(rv.stored_name)
    await db.delete(rv)
    await db.commit()
    return program_id


# ─── Компетенции ──────────────────────────────────────────────────────────────

async def get_all_competencies(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Competency).order_by(Competency.type, Competency.code))
    return [
        {"id": c.id, "code": c.code, "description": c.description, "type": c.type.value}
        for c in result.scalars().all()
    ]


async def create_competency(db: AsyncSession, code: str, description: str, ctype: str) -> Competency:
    # Проверка дубликата по коду
    existing = await db.execute(select(Competency).where(Competency.code == code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Компетенция {code} уже существует")
    c = Competency(code=code, description=description, type=CompetencyType(ctype))
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


async def set_program_competencies(
    db: AsyncSession, program_id: int, competency_ids: list[int]
) -> None:
    """Полностью заменяет список компетенций программы."""
    await db.execute(
        delete(ProgramCompetency).where(ProgramCompetency.program_id == program_id)
    )
    for cid in competency_ids:
        db.add(ProgramCompetency(program_id=program_id, competency_id=cid))
    await db.commit()


# ─── Дисциплины (текстовый список) ────────────────────────────────────────────

async def set_program_disciplines(
    db: AsyncSession, program_id: int, names: list[str]
) -> None:
    """Полностью заменяет текстовый список дисциплин программы."""
    await db.execute(
        delete(ProgramDisciplineItem).where(ProgramDisciplineItem.program_id == program_id)
    )
    for idx, name in enumerate(names):
        name = name.strip()
        if name:
            db.add(ProgramDisciplineItem(program_id=program_id, name=name, order_index=idx))
    await db.commit()


# ─── Области профессиональной деятельности ────────────────────────────────────

async def set_professional_areas(
    db: AsyncSession, program_id: int, areas: list[dict]
) -> None:
    """Полностью заменяет список областей профессиональной деятельности."""
    await db.execute(
        delete(ProfessionalArea).where(ProfessionalArea.program_id == program_id)
    )
    for area in areas:
        number = (area.get("number") or "").strip()
        desc = (area.get("description") or "").strip()
        if number:
            db.add(ProfessionalArea(program_id=program_id, number=number, description=desc or None))
    await db.commit()


# ─── Утилиты ──────────────────────────────────────────────────────────────────

def _delete_file(stored_name: str) -> None:
    path = UPLOAD_DIR / stored_name
    if path.exists():
        path.unlink()
