import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.checklist import ChecklistCategory, ChecklistItem
from app.models.report import ReportStatus, ReportStatusEnum
from app.models.report_file import ReportFile

UPLOAD_DIR = Path("app/static/uploads")
# Разрешённые MIME-типы для загружаемых файлов
ALLOWED_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 МБ


async def get_checklist(db: AsyncSession, discipline_id: int) -> list[ChecklistCategory]:
    result = await db.execute(
        select(ChecklistCategory)
        .options(selectinload(ChecklistCategory.items), selectinload(ChecklistCategory.files))
        .where(ChecklistCategory.discipline_id == discipline_id)
        .order_by(ChecklistCategory.id)
    )
    return result.scalars().all()


async def create_category(
    db: AsyncSession, discipline_id: int, name: str, created_by_id: int
) -> ChecklistCategory:
    cat = ChecklistCategory(name=name, discipline_id=discipline_id, created_by_id=created_by_id)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


async def delete_category(db: AsyncSession, category_id: int) -> None:
    result = await db.execute(select(ChecklistCategory).where(ChecklistCategory.id == category_id))
    cat = result.scalar_one_or_none()
    if cat:
        await db.delete(cat)
        await db.commit()


async def create_item(
    db: AsyncSession, category_id: int, title: str, created_by_id: int
) -> ChecklistItem:
    item = ChecklistItem(category_id=category_id, title=title, created_by_id=created_by_id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_item(
    db: AsyncSession, item_id: int, is_done: bool | None, comment: str | None
) -> ChecklistItem:
    result = await db.execute(select(ChecklistItem).where(ChecklistItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Пункт не найден")
    if is_done is not None:
        item.is_done = is_done
    if comment is not None:
        item.comment = comment
    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item_id: int) -> None:
    result = await db.execute(select(ChecklistItem).where(ChecklistItem.id == item_id))
    item = result.scalar_one_or_none()
    if item:
        await db.delete(item)
        await db.commit()


async def get_or_create_report_status(db: AsyncSession, discipline_id: int) -> ReportStatus:
    result = await db.execute(
        select(ReportStatus).where(ReportStatus.discipline_id == discipline_id)
    )
    rs = result.scalar_one_or_none()
    if not rs:
        rs = ReportStatus(discipline_id=discipline_id, status=ReportStatusEnum.draft)
        db.add(rs)
        await db.commit()
        await db.refresh(rs)
    return rs


async def submit_report(
    db: AsyncSession,
    discipline_id: int,
    submitted_by_id: int,
    auto_approve: bool = False,
) -> ReportStatus:
    rs = await get_or_create_report_status(db, discipline_id)
    if rs.status == ReportStatusEnum.approved:
        raise HTTPException(status_code=400, detail="Отчёт уже утверждён")
    now = datetime.now(timezone.utc)
    rs.submitted_at = now
    rs.submitted_by_id = submitted_by_id
    if auto_approve:
        # Заведующий кафедры утверждает собственные отчёты без ожидания
        rs.status = ReportStatusEnum.approved
        rs.approved_at = now
        rs.approved_by_id = submitted_by_id
    else:
        rs.status = ReportStatusEnum.submitted
    await db.commit()
    await db.refresh(rs)
    return rs


async def approve_report(db: AsyncSession, discipline_id: int, approved_by_id: int) -> ReportStatus:
    rs = await get_or_create_report_status(db, discipline_id)
    if rs.status != ReportStatusEnum.submitted:
        raise HTTPException(status_code=400, detail="Отчёт должен быть отправлен на утверждение")
    # Запрет само-утверждения: заведующий не может утвердить отчёт, который сам подал
    if rs.submitted_by_id == approved_by_id:
        raise HTTPException(status_code=403, detail="Нельзя утвердить собственный отчёт")
    rs.status = ReportStatusEnum.approved
    rs.approved_at = datetime.now(timezone.utc)
    rs.approved_by_id = approved_by_id
    await db.commit()
    await db.refresh(rs)
    return rs


async def reset_report(db: AsyncSession, discipline_id: int) -> ReportStatus:
    rs = await get_or_create_report_status(db, discipline_id)
    rs.status = ReportStatusEnum.draft
    rs.submitted_at = None
    rs.submitted_by_id = None
    rs.approved_at = None
    rs.approved_by_id = None
    await db.commit()
    await db.refresh(rs)
    return rs


async def save_file_feedback(db: AsyncSession, file_id: int, feedback: str | None) -> ReportFile:
    result = await db.execute(select(ReportFile).where(ReportFile.id == file_id))
    rf = result.scalar_one_or_none()
    if not rf:
        raise HTTPException(status_code=404, detail="Файл не найден")
    rf.feedback = feedback or None
    await db.commit()
    await db.refresh(rf)
    return rf


async def get_report_files(db: AsyncSession, discipline_id: int) -> list[ReportFile]:
    result = await db.execute(
        select(ReportFile)
        .options(selectinload(ReportFile.uploaded_by))
        .where(ReportFile.discipline_id == discipline_id)
        .order_by(ReportFile.uploaded_at)
    )
    return result.scalars().all()


async def add_report_file(
    db: AsyncSession,
    discipline_id: int,
    uploaded_by_id: int,
    file: UploadFile,
    category_id: int | None = None,
) -> ReportFile:
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 20 МБ)")
    ct = file.content_type or ""
    if ct not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Разрешены только PDF, DOC, DOCX файлы")

    suffix = Path(file.filename or "file").suffix.lower() or ".bin"
    # UUID-имя исключает конфликты и делает невозможным path-traversal через оригинальное имя
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / stored_name).write_bytes(content)

    rf = ReportFile(
        discipline_id=discipline_id,
        original_name=file.filename or stored_name,
        stored_name=stored_name,
        content_type=ct,
        size=len(content),
        uploaded_by_id=uploaded_by_id,
        category_id=category_id,
    )
    db.add(rf)
    await db.commit()
    await db.refresh(rf)
    return rf


async def delete_report_file(db: AsyncSession, file_id: int) -> None:
    result = await db.execute(select(ReportFile).where(ReportFile.id == file_id))
    rf = result.scalar_one_or_none()
    if rf:
        path = UPLOAD_DIR / rf.stored_name
        if path.exists():
            path.unlink()
        await db.delete(rf)
        await db.commit()
