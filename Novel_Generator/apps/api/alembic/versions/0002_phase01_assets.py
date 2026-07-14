"""Phase 1: project shelf and creative assets."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_phase01_assets"
down_revision: str | Sequence[str] | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "novel_projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("genre", sa.String(length=100), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("current_stage", sa.String(length=30), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "character_cards",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("card_type", sa.String(length=30), nullable=False),
        sa.Column("profile_json", sa.JSON(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("confirm_status", sa.String(length=30), nullable=False),
        sa.Column("lock_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["novel_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_character_cards_project_id", "character_cards", ["project_id"])

    op.create_table(
        "theme_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("genre", sa.String(length=100), nullable=False),
        sa.Column("theme", sa.Text(), nullable=False),
        sa.Column("target_readers", sa.Text(), nullable=False),
        sa.Column("narrative_style", sa.Text(), nullable=False),
        sa.Column("emotional_tone", sa.Text(), nullable=False),
        sa.Column("pleasure_points", sa.Text(), nullable=False),
        sa.Column("forbidden_content", sa.Text(), nullable=False),
        sa.Column("confirm_status", sa.String(length=30), nullable=False),
        sa.Column("lock_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["novel_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index("ix_theme_profiles_project_id", "theme_profiles", ["project_id"])

    op.create_table(
        "world_settings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("background_json", sa.JSON(), nullable=False),
        sa.Column("confirm_status", sa.String(length=30), nullable=False),
        sa.Column("lock_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["novel_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index("ix_world_settings_project_id", "world_settings", ["project_id"])

    op.create_table(
        "outlines",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("plot_nodes_json", sa.JSON(), nullable=False),
        sa.Column("character_arcs_json", sa.JSON(), nullable=False),
        sa.Column("ending_direction", sa.Text(), nullable=False),
        sa.Column("confirm_status", sa.String(length=30), nullable=False),
        sa.Column("lock_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["novel_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outlines_project_id", "outlines", ["project_id"])

    op.create_table(
        "volumes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("outline_id", sa.String(length=36), nullable=True),
        sa.Column("volume_no", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("stage_goal", sa.Text(), nullable=False),
        sa.Column("main_conflict", sa.Text(), nullable=False),
        sa.Column("key_events_json", sa.JSON(), nullable=False),
        sa.Column("involved_characters", sa.JSON(), nullable=False),
        sa.Column("emotional_rhythm", sa.Text(), nullable=False),
        sa.Column("previous_relation", sa.Text(), nullable=False),
        sa.Column("next_relation", sa.Text(), nullable=False),
        sa.Column("confirm_status", sa.String(length=30), nullable=False),
        sa.Column("lock_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["outline_id"], ["outlines.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["novel_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_volumes_project_id", "volumes", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_volumes_project_id", table_name="volumes")
    op.drop_table("volumes")
    op.drop_index("ix_outlines_project_id", table_name="outlines")
    op.drop_table("outlines")
    op.drop_index("ix_world_settings_project_id", table_name="world_settings")
    op.drop_table("world_settings")
    op.drop_index("ix_theme_profiles_project_id", table_name="theme_profiles")
    op.drop_table("theme_profiles")
    op.drop_index("ix_character_cards_project_id", table_name="character_cards")
    op.drop_table("character_cards")
    op.drop_table("novel_projects")
