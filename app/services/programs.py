from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.discipline import Discipline
from app.models.program import EducationalProgram, ProgramLevel
from app.models.user import User

_LEVEL_DURATION = {
    ProgramLevel.bachelor: 4,
    ProgramLevel.specialist: 5,
    ProgramLevel.master: 2,
    ProgramLevel.postgraduate: 3,
}


async def get_programs_for_department(db: AsyncSession, department_id: int) -> list[dict]:
    """Программы, у которых хотя бы одна дисциплина принадлежит данной кафедре,
    либо программа сама принадлежит кафедре."""
    result = await db.execute(
        select(EducationalProgram)
        .options(selectinload(EducationalProgram.director), selectinload(EducationalProgram.department))
        .distinct()
        .join(Discipline, Discipline.program_id == EducationalProgram.id)
        .where(Discipline.department_id == department_id)
        .order_by(EducationalProgram.name)
    )
    programs = result.scalars().all()
    out = []
    for p in programs:
        # Считаем дисциплины
        total_res = await db.execute(
            select(func.count()).where(Discipline.program_id == p.id)
        )
        own_res = await db.execute(
            select(func.count()).where(
                Discipline.program_id == p.id,
                Discipline.department_id == department_id,
            )
        )
        out.append({
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "level": p.level,
            "level_label": p.level.label,
            "start_year": p.start_year,
            "end_year": p.start_year + _LEVEL_DURATION.get(p.level, 4),
            "director_full_name": p.director.full_name,
            "description": p.description,
            "department_name": p.department.name,
            "discipline_count": total_res.scalar(),
            "own_discipline_count": own_res.scalar(),
        })
    return out


async def get_program_by_id(db: AsyncSession, program_id: int, department_id: int) -> dict | None:
    result = await db.execute(
        select(EducationalProgram)
        .options(selectinload(EducationalProgram.director), selectinload(EducationalProgram.department))
        .where(EducationalProgram.id == program_id)
    )
    p = result.scalar_one_or_none()
    if not p:
        return None
    total_res = await db.execute(select(func.count()).where(Discipline.program_id == p.id))
    own_res = await db.execute(
        select(func.count()).where(
            Discipline.program_id == p.id,
            Discipline.department_id == department_id,
        )
    )
    return {
        "id": p.id,
        "name": p.name,
        "code": p.code,
        "level": p.level,
        "level_label": p.level.label,
        "start_year": p.start_year,
        "end_year": p.start_year + _LEVEL_DURATION.get(p.level, 4),
        "director_full_name": p.director.full_name,
        "description": p.description,
        "department_name": p.department.name,
        "discipline_count": total_res.scalar(),
        "own_discipline_count": own_res.scalar(),
    }
