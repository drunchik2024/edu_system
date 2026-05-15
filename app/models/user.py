from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"), nullable=True)

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="users")

    # Программы, которыми руководит
    directed_programs: Mapped[list["EducationalProgram"]] = relationship(
        "EducationalProgram", back_populates="director", foreign_keys="EducationalProgram.director_id"
    )
    # Дисциплины как основной преподаватель
    primary_disciplines: Mapped[list["Discipline"]] = relationship(
        "Discipline", back_populates="teacher_primary", foreign_keys="Discipline.teacher_primary_id"
    )
    # Дисциплины как второй преподаватель
    secondary_disciplines: Mapped[list["Discipline"]] = relationship(
        "Discipline", back_populates="teacher_secondary", foreign_keys="Discipline.teacher_secondary_id"
    )
    # Утверждённые отчёты
    approved_reports: Mapped[list["ReportStatus"]] = relationship(
        "ReportStatus", back_populates="approved_by_user", foreign_keys="ReportStatus.approved_by_id"
    )
