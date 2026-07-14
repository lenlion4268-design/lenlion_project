from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.config import settings as env_settings

if TYPE_CHECKING:
    from app.domains.settings.models import WorkspaceSettings


@dataclass
class EffectiveAISettings:
    ai_provider: str
    ai_model: str
    openai_api_key: str | None
    openai_base_url: str
    ai_request_timeout_seconds: float
    ai_batch_max_chapters: int
    ai_model_outline: str | None
    ai_model_volume: str | None
    ai_model_chapter: str | None
    ai_model_profile_fast: str | None
    ai_model_profile_quality: str | None
    default_model_profile: str

    @classmethod
    def from_env(cls) -> EffectiveAISettings:
        return cls(
            ai_provider=env_settings.ai_provider,
            ai_model=env_settings.ai_model,
            openai_api_key=env_settings.openai_api_key,
            openai_base_url=env_settings.openai_base_url,
            ai_request_timeout_seconds=env_settings.ai_request_timeout_seconds,
            ai_batch_max_chapters=env_settings.ai_batch_max_chapters,
            ai_model_outline=env_settings.ai_model_outline,
            ai_model_volume=env_settings.ai_model_volume,
            ai_model_chapter=env_settings.ai_model_chapter,
            ai_model_profile_fast=env_settings.ai_model_profile_fast,
            ai_model_profile_quality=env_settings.ai_model_profile_quality,
            default_model_profile="default",
        )

    @classmethod
    def from_row(cls, row: WorkspaceSettings) -> EffectiveAISettings:
        return cls(
            ai_provider=row.ai_provider,
            ai_model=row.ai_model,
            openai_api_key=row.openai_api_key,
            openai_base_url=row.openai_base_url,
            ai_request_timeout_seconds=row.ai_request_timeout_seconds,
            ai_batch_max_chapters=row.ai_batch_max_chapters,
            ai_model_outline=row.ai_model_outline,
            ai_model_volume=row.ai_model_volume,
            ai_model_chapter=row.ai_model_chapter,
            ai_model_profile_fast=row.ai_model_profile_fast,
            ai_model_profile_quality=row.ai_model_profile_quality,
            default_model_profile=row.default_model_profile,
        )


_effective: EffectiveAISettings | None = None


def get_effective_settings() -> EffectiveAISettings:
    global _effective
    if _effective is None:
        _effective = EffectiveAISettings.from_env()
    return _effective


def refresh_effective_settings(row: WorkspaceSettings | None) -> EffectiveAISettings:
    global _effective
    _effective = EffectiveAISettings.from_row(row) if row else EffectiveAISettings.from_env()
    return _effective


def reset_effective_settings() -> None:
    global _effective
    _effective = None
