import enum
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CompetencyType(str, enum.Enum):
    uk = "uk"
    opk = "opk"
    pk = "pk"

    @property
    def label(self) -> str:
        return {"uk": "УК", "opk": "ОПК", "pk": "ПК"}[self.value]

    @property
    def full_label(self) -> str:
        return {
            "uk": "Универсальные компетенции (УК)",
            "opk": "Общепрофессиональные компетенции (ОПК)",
            "pk": "Профессиональные компетенции (ПК)",
        }[self.value]


class Competency(Base):
    __tablename__ = "competencies"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[CompetencyType] = mapped_column(SAEnum(CompetencyType), nullable=False)

    program_links: Mapped[list["ProgramCompetency"]] = relationship(
        "ProgramCompetency", back_populates="competency"
    )


class ProgramCompetency(Base):
    """Связь многие-ко-многим между программой и компетенцией."""
    __tablename__ = "program_competencies"
    __table_args__ = (UniqueConstraint("program_id", "competency_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("educational_programs.id"), nullable=False)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id"), nullable=False)

    program: Mapped["EducationalProgram"] = relationship(
        "EducationalProgram", back_populates="competencies"
    )
    competency: Mapped["Competency"] = relationship("Competency", back_populates="program_links")


class ProgramDisciplineItem(Base):
    """Простой текстовый список дисциплин программы для модуля РОП."""
    __tablename__ = "program_discipline_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("educational_programs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    program: Mapped["EducationalProgram"] = relationship(
        "EducationalProgram", back_populates="discipline_items"
    )


class ProgramReview(Base):
    """Рецензии программы (PDF-файлы с подписью)."""
    __tablename__ = "program_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("educational_programs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)

    program: Mapped["EducationalProgram"] = relationship(
        "EducationalProgram", back_populates="reviews"
    )


class ProfessionalArea(Base):
    """Области и сферы профессиональной деятельности программы."""
    __tablename__ = "professional_areas"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("educational_programs.id"), nullable=False)
    number: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    program: Mapped["EducationalProgram"] = relationship(
        "EducationalProgram", back_populates="professional_areas"
    )
