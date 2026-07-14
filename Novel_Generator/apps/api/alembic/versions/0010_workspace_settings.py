"""Phase 10: workspace settings singleton for personal info and AI config."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_workspace_settings"
down_revision: str | Sequence[str] | None = "0009_library_materials"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspace_settings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("pen_name", sa.String(length=255), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("ai_provider", sa.String(length=30), nullable=False, server_default="mock"),
        sa.Column("ai_model", sa.String(length=100), nullable=False, server_default="mock-writer"),
        sa.Column("openai_base_url", sa.String(length=500), nullable=False, server_default="https://api.openai.com/v1"),
        sa.Column("openai_api_key", sa.Text(), nullable=True),
        sa.Column("ai_model_outline", sa.String(length=100), nullable=True),
        sa.Column("ai_model_volume", sa.String(length=100), nullable=True),
        sa.Column("ai_model_chapter", sa.String(length=100), nullable=True),
        sa.Column("ai_model_profile_fast", sa.String(length=100), nullable=True),
        sa.Column("ai_model_profile_quality", sa.String(length=100), nullable=True),
        sa.Column("ai_request_timeout_seconds", sa.Float(), nullable=False, server_default="120"),
        sa.Column("ai_batch_max_chapters", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("default_model_profile", sa.String(length=20), nullable=False, server_default="default"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("workspace_settings")
