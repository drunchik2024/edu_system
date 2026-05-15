"""
Seed teacher report submissions for testing head-of-department approval flow.

Result:
  disc 1  — draft, no file       → head sees disabled "Submit" button
  disc 2  — submitted by teacher2 → head can approve
  disc 3  — submitted by teacher1 → head can approve
  disc 4  — submitted by teacher2 → head can approve
  disc 5  — submitted by teacher1 → head can approve
"""

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import ReportStatus, ReportFile
from app.models.checklist import ChecklistCategory, ChecklistItem
from app.models.report import ReportStatusEnum

UPLOAD_DIR = Path("app/static/uploads")

TEACHER1_ID = 4  # teacher1@vgtu.ru — primary on discs 1, 3, 5
TEACHER2_ID = 5  # teacher2@vgtu.ru — primary on discs 2, 4

# (discipline_id, submitted_by_id, category_name, file_original_name, file_content)
SUBMISSIONS = [
    (
        2,
        TEACHER2_ID,
        "Рабочая программа дисциплины",
        "РПД_Алгоритмы_и_СД.pdf",
        b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\n%%EOF\n",
    ),
    (
        3,
        TEACHER1_ID,
        "Методические материалы",
        "Метод_материалы_Веб.pdf",
        b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\n%%EOF\n",
    ),
    (
        4,
        TEACHER2_ID,
        "Рабочая программа дисциплины",
        "РПД_Машинное_обучение.pdf",
        b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\n%%EOF\n",
    ),
    (
        5,
        TEACHER1_ID,
        "Учебно-методический комплекс",
        "УМК_Проектирование_ИС.pdf",
        b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\n%%EOF\n",
    ),
]


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    async with async_session() as db:
        # ── 1. Reset all report statuses and delete all files/categories ──────
        print("Resetting report statuses…")
        result = await db.execute(select(ReportStatus))
        for rs in result.scalars().all():
            rs.status = ReportStatusEnum.draft
            rs.submitted_at = None
            rs.submitted_by_id = None
            rs.approved_at = None
            rs.approved_by_id = None
        await db.commit()

        print("Deleting existing report files (DB + disk)…")
        result = await db.execute(select(ReportFile))
        for rf in result.scalars().all():
            p = UPLOAD_DIR / rf.stored_name
            if p.exists():
                p.unlink()
            await db.delete(rf)
        await db.commit()

        print("Deleting existing checklist categories…")
        result = await db.execute(select(ChecklistCategory))
        for cat in result.scalars().all():
            await db.delete(cat)
        await db.commit()

        # ── 2. Create submissions ─────────────────────────────────────────────
        for disc_id, teacher_id, cat_name, filename, content in SUBMISSIONS:
            print(f"  disc {disc_id}: creating category + file + submit…")

            # Category
            cat = ChecklistCategory(
                name=cat_name,
                discipline_id=disc_id,
                created_by_id=teacher_id,
            )
            db.add(cat)
            await db.flush()

            # Default checklist item
            item = ChecklistItem(
                title="Документ загружен и проверен",
                category_id=cat.id,
                created_by_id=teacher_id,
                is_done=True,
            )
            db.add(item)

            # Write file to disk
            stored_name = f"{uuid.uuid4().hex}.pdf"
            (UPLOAD_DIR / stored_name).write_bytes(content)

            # File record — linked to the category created above
            rf = ReportFile(
                discipline_id=disc_id,
                original_name=filename,
                stored_name=stored_name,
                content_type="application/pdf",
                size=len(content),
                uploaded_by_id=teacher_id,
                category_id=cat.id,
            )
            db.add(rf)

            # ReportStatus — submitted
            result = await db.execute(
                select(ReportStatus).where(ReportStatus.discipline_id == disc_id)
            )
            rs = result.scalar_one_or_none()
            if not rs:
                rs = ReportStatus(discipline_id=disc_id)
                db.add(rs)
            rs.status = ReportStatusEnum.submitted
            rs.submitted_at = datetime.now(timezone.utc)
            rs.submitted_by_id = teacher_id

            await db.commit()

        print("Done. Summary:")
        print("  disc 1 — draft, no files  → head sees DISABLED submit button")
        for disc_id, teacher_id, *_ in SUBMISSIONS:
            print(f"  disc {disc_id} — submitted by user {teacher_id} → head CAN approve")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
