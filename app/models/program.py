import enum
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProgramLevel(str, enum.Enum):
    bachelor = "bachelor"
    specialist = "specialist"
    master = "master"
    postgraduate = "postgraduate"

    @property
    def label(self) -> str:
        labels = {
            "bachelor": "Бакалавриат",
            "specialist": "Специалитет",
            "master": "Магистратура",
            "postgraduate": "Аспирантура",
        }
        return labels[self.value]


class EducationFormEnum(str, enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    mixed = "mixed"

    @property
    def label(self) -> str:
        return {"full_time": "Очная", "part_time": "Заочная", "mixed": "Очно-заочная"}[self.value]


class EducationalProgram(Base):
    __tablename__ = "educational_programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    level: Mapped[ProgramLevel] = mapped_column(SAEnum(ProgramLevel), nullable=False)
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    director_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)

    # Поля модуля РОП — заполняются руководителем ОП
    education_form: Mapped[Optional[EducationFormEnum]] = mapped_column(
        SAEnum(EducationFormEnum), nullable=True
    )
    education_duration: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    standard_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    curriculum_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title_page_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    activity_types: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structure_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    practices: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    director: Mapped["User"] = relationship(
        "User", back_populates="directed_programs", foreign_keys=[director_id]
    )
    department: Mapped["Department"] = relationship("Department", back_populates="programs")
    disciplines: Mapped[list["Discipline"]] = relationship("Discipline", back_populates="program")

    # Связи модуля РОП
    competencies: Mapped[list["ProgramCompetency"]] = relationship(
        "ProgramCompetency", back_populates="program", cascade="all, delete-orphan"
    )
    discipline_items: Mapped[list["ProgramDisciplineItem"]] = relationship(
        "ProgramDisciplineItem", back_populates="program",
        cascade="all, delete-orphan", order_by="ProgramDisciplineItem.order_index"
    )
    reviews: Mapped[list["ProgramReview"]] = relationship(
        "ProgramReview", back_populates="program", cascade="all, delete-orphan"
    )
    professional_areas: Mapped[list["ProfessionalArea"]] = relationship(
        "ProfessionalArea", back_populates="program",
        cascade="all, delete-orphan", order_by="ProfessionalArea.id"
    )
