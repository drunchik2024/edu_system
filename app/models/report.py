import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReportStatusEnum(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"

    @property
    def label(self) -> str:
        return {"draft": "Черновик", "submitted": "На утверждении", "approved": "Утверждено"}[self.value]


class ReportStatus(Base):
    __tablename__ = "report_statuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[ReportStatusEnum] = mapped_column(
        SAEnum(ReportStatusEnum), default=ReportStatusEnum.draft, nullable=False
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    discipline_id: Mapped[int] = mapped_column(
        ForeignKey("disciplines.id"), nullable=False, unique=True
    )
    submitted_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    discipline: Mapped["Discipline"] = relationship("Discipline", back_populates="report_status")
    submitted_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[submitted_by_id]
    )
    approved_by_user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="approved_reports", foreign_keys=[approved_by_id]
    )
