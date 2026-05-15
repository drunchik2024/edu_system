from typing import Literal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.discipline import Discipline
from app.models.report import ReportStatus, ReportStatusEnum


async def get_disciplines_for_department(
    db: AsyncSession,
    department_id: int,
    program_id: int | None = None,
    sort_by: Literal["name", "code"] = "name",
) -> list[dict]:
    q = (
        select(Discipline)
        .options(
            selectinload(Discipline.program),
            selectinload(Discipline.teacher_primary),
            selectinload(Discipline.teacher_secondary),
            selectinload(Discipline.report_status),
            selectinload(Discipline.department),
        )
        .where(Discipline.department_id == department_id)
    )
    if program_id:
        q = q.where(Discipline.program_id == program_id)
    order_col = Discipline.name if sort_by == "name" else Discipline.code
    q = q.order_by(order_col)
    result = await db.execute(q)
    disciplines = result.scalars().all()
    return [_discipline_to_dict(d) for d in disciplines]


async def get_external_disciplines(db: AsyncSession, program_id: int, department_id: int) -> list[dict]:
    # Дисциплины программы, которые ведёт другая кафедра (вкладка "Другие кафедры")
    result = await db.execute(
        select(Discipline)
        .options(
            selectinload(Discipline.department),
            selectinload(Discipline.teacher_primary),
            selectinload(Discipline.teacher_secondary),
            selectinload(Discipline.report_status),
            selectinload(Discipline.program),
        )
        .where(Discipline.program_id == program_id, Discipline.department_id != department_id)
        .order_by(Discipline.name)
    )
    return [_discipline_to_dict(d) for d in result.scalars().all()]


async def get_discipline_by_id(db: AsyncSession, discipline_id: int) -> dict | None:
    result = await db.execute(
        select(Discipline)
        .options(
            selectinload(Discipline.program),
            selectinload(Discipline.department),
            selectinload(Discipline.teacher_primary),
            selectinload(Discipline.teacher_secondary),
            selectinload(Discipline.report_status),
        )
        .where(Discipline.id == discipline_id)
    )
    d = result.scalar_one_or_none()
    if not d:
        return None
    return _discipline_to_dict(d, full=True)


def _discipline_to_dict(d: Discipline, full: bool = False) -> dict:
    # full=True добавляет цели/задачи/результаты — нужно только на странице детали дисциплины
    rs = d.report_status
    status = rs.status if rs else None
    status_label = rs.status.label if rs else "Черновик"
    base = {
        "id": d.id,
        "name": d.name,
        "code": d.code,
        "program_name": d.program.name,
        "program_id": d.program_id,
        "department_name": d.department.name,
        "teacher_primary_name": d.teacher_primary.full_name,
        "teacher_secondary_name": d.teacher_secondary.full_name,
        "report_status": status,
        "report_status_label": status_label,
    }
    if full:
        base.update({
            "goals": d.goals,
            "objectives": d.objectives,
            "outcomes": d.outcomes,
        })
    return base
