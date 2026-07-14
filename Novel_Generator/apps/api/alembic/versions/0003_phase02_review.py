"""Phase 2: review records."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_phase02_review"
down_revision: str | Sequence[str] | None = "0002_phase01_assets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "review_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("target_type", sa.String(length=30), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("operator_id", sa.String(length=36), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("before_status", sa.String(length=30), nullable=False),
        sa.Column("after_status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_records_project_id", "review_records", ["project_id"])
    op.create_index("ix_review_records_target_id", "review_records", ["target_id"])


def downgrade() -> None:
    op.drop_index("ix_review_records_target_id", table_name="review_records")
    op.drop_index("ix_review_records_project_id", table_name="review_records")
    op.drop_table("review_records")
