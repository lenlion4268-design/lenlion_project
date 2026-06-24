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


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ProjectStage(StrEnum):
    CHARACTERS = "characters"
    THEME = "theme"
    WORLD = "world"
    OUTLINE = "outline"
    VOLUMES = "volumes"
    CHAPTERS = "chapters"


class CharacterCardType(StrEnum):
    PERSON = "person"
    ORGANIZATION = "organization"
    FORCE = "force"


class AssetSourceType(StrEnum):
    MANUAL = "manual"
    REFERENCE_PARSE = "reference_parse"
    AI_SUGGESTED = "ai_suggested"
