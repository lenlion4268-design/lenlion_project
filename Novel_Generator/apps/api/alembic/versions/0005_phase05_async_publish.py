"""Phase 5: async metadata, publications."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_phase05_async_publish"
down_revision: str | Sequence[str] | None = "0004_phase03_generation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "generation_jobs",
        sa.Column("model_profile", sa.String(length=20), nullable=False, server_default="default"),
    )
    op.add_column(
        "generation_jobs",
        sa.Column("model_name", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "generation_jobs",
        sa.Column("execution_mode", sa.String(length=10), nullable=False, server_default="sync"),
    )

    op.create_table(
        "publications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("volume_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("chapter_count", sa.Integer(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["novel_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["volume_id"], ["volumes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_publications_project_id", "publications", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_publications_project_id", table_name="publications")
    op.drop_table("publications")
    op.drop_column("generation_jobs", "execution_mode")
    op.drop_column("generation_jobs", "model_name")
    op.drop_column("generation_jobs", "model_profile")
