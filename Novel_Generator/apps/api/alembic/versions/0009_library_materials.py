"""Phase 10: library-scoped materials (independent of novel projects)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_library_materials"
down_revision: str | Sequence[str] | None = "0008_phase09_style"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("reference_works", "project_id", existing_type=sa.String(length=36), nullable=True)
    op.alter_column("style_profiles", "project_id", existing_type=sa.String(length=36), nullable=True)
    op.alter_column("style_analysis_jobs", "project_id", existing_type=sa.String(length=36), nullable=True)


def downgrade() -> None:
    op.alter_column("style_analysis_jobs", "project_id", existing_type=sa.String(length=36), nullable=False)
    op.alter_column("style_profiles", "project_id", existing_type=sa.String(length=36), nullable=False)
    op.alter_column("reference_works", "project_id", existing_type=sa.String(length=36), nullable=False)
