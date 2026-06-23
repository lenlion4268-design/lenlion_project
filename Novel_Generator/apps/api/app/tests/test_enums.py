from app.core.enums import ConfirmStatus, GenerationJobStatus, LockStatus, ProjectMode


def test_project_mode_values() -> None:
    assert ProjectMode.LONG == "long"
    assert ProjectMode.SHORT == "short"


def test_confirm_status_values() -> None:
    assert ConfirmStatus.DRAFT == "draft"
    assert ConfirmStatus.PENDING_CONFIRM == "pending_confirm"
    assert ConfirmStatus.CONFIRMED == "confirmed"
    assert ConfirmStatus.LOCKED == "locked"
    assert ConfirmStatus.REJECTED == "rejected"
    assert ConfirmStatus.ARCHIVED == "archived"


def test_lock_status_values() -> None:
    assert LockStatus.UNLOCKED == "unlocked"
    assert LockStatus.LOCKED == "locked"


def test_generation_job_status_values() -> None:
    assert GenerationJobStatus.QUEUED == "queued"
    assert GenerationJobStatus.RUNNING == "running"
    assert GenerationJobStatus.SUCCEEDED == "succeeded"
    assert GenerationJobStatus.FAILED == "failed"
    assert GenerationJobStatus.CANCELLED == "cancelled"
