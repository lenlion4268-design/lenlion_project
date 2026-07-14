"""Phase 6: publish channels and delivery metadata."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_phase06_queue_publish"
down_revision: str | Sequence[str] | None = "0005_phase05_async_publish"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "publications",
        sa.Column("channel", sa.String(length=20), nullable=False, server_default="local"),
    )
    op.add_column(
        "publications",
        sa.Column("delivery_status", sa.String(length=20), nullable=False, server_default="skipped"),
    )
    op.add_column("publications", sa.Column("delivery_error", sa.Text(), nullable=True))
    op.add_column("publications", sa.Column("external_ref", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("publications", "external_ref")
    op.drop_column("publications", "delivery_error")
    op.drop_column("publications", "delivery_status")
    op.drop_column("publications", "channel")
