from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReportFile(Base):
    __tablename__ = "report_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    discipline_id: Mapped[int] = mapped_column(ForeignKey("disciplines.id"), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("checklist_categories.id", ondelete="SET NULL"), nullable=True
    )

    discipline: Mapped["Discipline"] = relationship("Discipline", back_populates="report_files")
    uploaded_by: Mapped["User"] = relationship("User", foreign_keys=[uploaded_by_id])
    category: Mapped[Optional["ChecklistCategory"]] = relationship(
        "ChecklistCategory", back_populates="files"
    )
