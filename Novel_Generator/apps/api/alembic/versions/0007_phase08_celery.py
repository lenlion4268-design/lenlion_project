"""Phase 8: Celery task id on generation jobs."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_phase08_celery"
down_revision: str | Sequence[str] | None = "0006_phase06_queue_publish"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "generation_jobs",
        sa.Column("queue_task_id", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("generation_jobs", "queue_task_id")
