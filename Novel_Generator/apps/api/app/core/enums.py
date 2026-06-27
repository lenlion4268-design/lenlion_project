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
    OWN_COMPLETED = "own_completed"
    AI_SUGGESTED = "ai_suggested"


class ReviewTargetType(StrEnum):
    CHARACTER_CARD = "character_card"
    THEME_PROFILE = "theme_profile"
    WORLD_SETTING = "world_setting"
    OUTLINE = "outline"
    VOLUME = "volume"
    CHAPTER = "chapter"


class ReviewAction(StrEnum):
    CONFIRM = "confirm"
    LOCK = "lock"
    REJECT = "reject"
    UNLOCK = "unlock"


class ReadinessStage(StrEnum):
    OUTLINE = "outline"
    VOLUMES = "volumes"
    CHAPTERS = "chapters"


class ModelProfile(StrEnum):
    DEFAULT = "default"
    FAST = "fast"
    QUALITY = "quality"


class ExecutionMode(StrEnum):
    SYNC = "sync"
    ASYNC = "async"


class PublicationStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PublishChannel(StrEnum):
    LOCAL = "local"
    WEBHOOK = "webhook"
    PLATFORM = "platform"


class ExportFormat(StrEnum):
    MARKDOWN = "markdown"
    TEXT = "text"
    EPUB = "epub"


class DeliveryStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class QueueBackend(StrEnum):
    THREAD = "thread"
    REDIS = "redis"
    CELERY = "celery"


class PlatformPayloadPreset(StrEnum):
    DEFAULT = "default"
    MINIMAL = "minimal"
    FULL = "full"


class ReferenceWorkStatus(StrEnum):
    UPLOADED = "uploaded"
    INGESTED = "ingested"
    FAILED = "failed"


class ReferenceFormat(StrEnum):
    TXT = "txt"
    MD = "md"
    EPUB = "epub"


class StyleAnalysisJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
