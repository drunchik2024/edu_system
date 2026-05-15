"""add_rop_module

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-13 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Новые enum-типы
    education_form_enum = sa.Enum("full_time", "part_time", "mixed", name="educationformenum")
    education_form_enum.create(op.get_bind(), checkfirst=True)

    competency_type_enum = sa.Enum("uk", "opk", "pk", name="competencytype")
    competency_type_enum.create(op.get_bind(), checkfirst=True)

    # Новые поля в educational_programs
    op.add_column("educational_programs", sa.Column("education_form", education_form_enum, nullable=True))
    op.add_column("educational_programs", sa.Column("education_duration", sa.String(64), nullable=True))
    op.add_column("educational_programs", sa.Column("standard_file",    sa.String(255), nullable=True))
    op.add_column("educational_programs", sa.Column("curriculum_file",  sa.String(255), nullable=True))
    op.add_column("educational_programs", sa.Column("title_page_file",  sa.String(255), nullable=True))
    op.add_column("educational_programs", sa.Column("activity_types",   sa.Text,        nullable=True))
    op.add_column("educational_programs", sa.Column("structure_text",   sa.Text,        nullable=True))
    op.add_column("educational_programs", sa.Column("practices",        sa.Text,        nullable=True))

    # Справочник компетенций
    op.create_table(
        "competencies",
        sa.Column("id",          sa.Integer, primary_key=True),
        sa.Column("code",        sa.String(32), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("type",        competency_type_enum, nullable=False),
    )

    # Связь программа ↔ компетенция
    op.create_table(
        "program_competencies",
        sa.Column("id",            sa.Integer, primary_key=True),
        sa.Column("program_id",    sa.Integer, sa.ForeignKey("educational_programs.id"), nullable=False),
        sa.Column("competency_id", sa.Integer, sa.ForeignKey("competencies.id"),         nullable=False),
        sa.UniqueConstraint("program_id", "competency_id"),
    )

    # Текстовый список дисциплин программы
    op.create_table(
        "program_discipline_items",
        sa.Column("id",          sa.Integer, primary_key=True),
        sa.Column("program_id",  sa.Integer, sa.ForeignKey("educational_programs.id"), nullable=False),
        sa.Column("name",        sa.String(512), nullable=False),
        sa.Column("order_index", sa.Integer, default=0, nullable=False),
    )

    # Рецензии программы
    op.create_table(
        "program_reviews",
        sa.Column("id",            sa.Integer, primary_key=True),
        sa.Column("program_id",    sa.Integer, sa.ForeignKey("educational_programs.id"), nullable=False),
        sa.Column("name",          sa.String(512), nullable=False),
        sa.Column("stored_name",   sa.String(255), nullable=False, unique=True),
        sa.Column("original_name", sa.String(255), nullable=False),
    )

    # Области профессиональной деятельности
    op.create_table(
        "professional_areas",
        sa.Column("id",          sa.Integer, primary_key=True),
        sa.Column("program_id",  sa.Integer, sa.ForeignKey("educational_programs.id"), nullable=False),
        sa.Column("number",      sa.String(32), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("professional_areas")
    op.drop_table("program_reviews")
    op.drop_table("program_discipline_items")
    op.drop_table("program_competencies")
    op.drop_table("competencies")

    op.drop_column("educational_programs", "practices")
    op.drop_column("educational_programs", "structure_text")
    op.drop_column("educational_programs", "activity_types")
    op.drop_column("educational_programs", "title_page_file")
    op.drop_column("educational_programs", "curriculum_file")
    op.drop_column("educational_programs", "standard_file")
    op.drop_column("educational_programs", "education_duration")
    op.drop_column("educational_programs", "education_form")

    op.execute("DROP TYPE IF EXISTS educationformenum")
    op.execute("DROP TYPE IF EXISTS competencytype")
