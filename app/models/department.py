from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="department")
    disciplines: Mapped[list["Discipline"]] = relationship("Discipline", back_populates="department")
    programs: Mapped[list["EducationalProgram"]] = relationship("EducationalProgram", back_populates="department")
