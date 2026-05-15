from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Discipline(Base):
    __tablename__ = "disciplines"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)

    goals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objectives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcomes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    program_id: Mapped[int] = mapped_column(ForeignKey("educational_programs.id"), nullable=False)
    # Кафедра, которая ВЕДЁТ дисциплину
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    teacher_primary_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    teacher_secondary_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    program: Mapped["EducationalProgram"] = relationship("EducationalProgram", back_populates="disciplines")
    department: Mapped["Department"] = relationship("Department", back_populates="disciplines")
    teacher_primary: Mapped["User"] = relationship(
        "User", back_populates="primary_disciplines", foreign_keys=[teacher_primary_id]
    )
    teacher_secondary: Mapped["User"] = relationship(
        "User", back_populates="secondary_disciplines", foreign_keys=[teacher_secondary_id]
    )
    checklist_categories: Mapped[list["ChecklistCategory"]] = relationship(
        "ChecklistCategory", back_populates="discipline", cascade="all, delete-orphan"
    )
    report_status: Mapped[Optional["ReportStatus"]] = relationship(
        "ReportStatus", back_populates="discipline", uselist=False, cascade="all, delete-orphan"
    )
    report_files: Mapped[list["ReportFile"]] = relationship(
        "ReportFile", back_populates="discipline", cascade="all, delete-orphan"
    )
