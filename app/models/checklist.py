from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ChecklistCategory(Base):
    __tablename__ = "checklist_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    discipline_id: Mapped[int] = mapped_column(ForeignKey("disciplines.id"), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    discipline: Mapped["Discipline"] = relationship("Discipline", back_populates="checklist_categories")
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    items: Mapped[list["ChecklistItem"]] = relationship(
        "ChecklistItem", back_populates="category", cascade="all, delete-orphan", order_by="ChecklistItem.id"
    )
    files: Mapped[list["ReportFile"]] = relationship(
        "ReportFile", back_populates="category", order_by="ReportFile.id"
    )


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    category_id: Mapped[int] = mapped_column(ForeignKey("checklist_categories.id"), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    category: Mapped["ChecklistCategory"] = relationship("ChecklistCategory", back_populates="items")
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
