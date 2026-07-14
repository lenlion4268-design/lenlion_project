"""Phase 9: reference works, style profiles, style analysis jobs."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_phase09_style"
down_revision: str | Sequence[str] | None = "0007_phase08_celery"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reference_works",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(length=36),
            sa.ForeignKey("novel_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_type", sa.String(length=30), nullable=False, server_default="reference_parse"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="uploaded"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reference_works_project_id", "reference_works", ["project_id"])

    op.create_table(
        "reference_samples",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "reference_work_id",
            sa.String(length=36),
            sa.ForeignKey("reference_works.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("char_offset", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reference_samples_reference_work_id", "reference_samples", ["reference_work_id"])

    op.create_table(
        "style_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(length=36),
            sa.ForeignKey("novel_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reference_work_id",
            sa.String(length=36),
            sa.ForeignKey("reference_works.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("reference_title", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("voice_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("profile_json", sa.JSON(), nullable=False),
        sa.Column("skill_markdown", sa.Text(), nullable=False, server_default=""),
        sa.Column("confirm_status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("lock_status", sa.String(length=20), nullable=False, server_default="unlocked"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_style_profiles_project_id", "style_profiles", ["project_id"])

    op.create_table(
        "style_analysis_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(length=36),
            sa.ForeignKey("novel_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reference_work_id",
            sa.String(length=36),
            sa.ForeignKey("reference_works.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "style_profile_id",
            sa.String(length=36),
            sa.ForeignKey("style_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("queue_task_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_style_analysis_jobs_project_id", "style_analysis_jobs", ["project_id"])

    op.add_column(
        "novel_projects",
        sa.Column("active_style_profile_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_novel_projects_active_style_profile",
        "novel_projects",
        "style_profiles",
        ["active_style_profile_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_novel_projects_active_style_profile", "novel_projects", type_="foreignkey")
    op.drop_column("novel_projects", "active_style_profile_id")
    op.drop_index("ix_style_analysis_jobs_project_id", table_name="style_analysis_jobs")
    op.drop_table("style_analysis_jobs")
    op.drop_index("ix_style_profiles_project_id", table_name="style_profiles")
    op.drop_table("style_profiles")
    op.drop_index("ix_reference_samples_reference_work_id", table_name="reference_samples")
    op.drop_table("reference_samples")
    op.drop_index("ix_reference_works_project_id", table_name="reference_works")
    op.drop_table("reference_works")
