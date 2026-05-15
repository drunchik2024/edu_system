"""add_category_id_to_report_files

Revision ID: a1b2c3d4e5f6
Revises: 21559dd8427b
Create Date: 2026-05-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "21559dd8427b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "report_files",
        sa.Column("category_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_report_files_category_id",
        "report_files",
        "checklist_categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_report_files_category_id", "report_files", type_="foreignkey")
    op.drop_column("report_files", "category_id")
