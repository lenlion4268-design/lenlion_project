from enum import StrEnum


class ProjectMode(StrEnum):
    LONG = "long"
    SHORT = "short"


class ConfirmStatus(StrEnum):
    DRAFT = "draft"
    PENDING_CONFIRM = "pending_confirm"
    CONFIRMED = "confirmed"
    LOCKED = "locked"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class LockStatus(StrEnum):
    UNLOCKED = "unlocked"
    LOCKED = "locked"


class GenerationJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
