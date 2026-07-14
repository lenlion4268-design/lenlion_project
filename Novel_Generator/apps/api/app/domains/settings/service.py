import httpx
from sqlalchemy.orm import Session

from app.core.enums import ModelProfile, ReadinessStage
from app.core.errors import AppError
from app.domains.generation.model_router import resolve_model_name
from app.domains.settings.effective import get_effective_settings, refresh_effective_settings
from app.domains.settings.models import WorkspaceSettings
from app.domains.settings.repository import SettingsRepository
from app.domains.settings.schemas import (
    EffectiveModelRow,
    EffectiveModelsResponse,
    ModelSettings,
    ModelSettingsUpdate,
    ModelTestResponse,
    PersonalSettings,
    PersonalSettingsUpdate,
    SettingsResponse,
)


def mask_api_key(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "***"
    return f"{value[:3]}***{value[-4:]}"


class SettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SettingsRepository(db)

    def bootstrap(self) -> WorkspaceSettings:
        row = self.repo.ensure_singleton()
        refresh_effective_settings(row)
        return row

    def get_settings(self) -> SettingsResponse:
        row = self.repo.ensure_singleton()
        refresh_effective_settings(row)
        return SettingsResponse(
            personal=PersonalSettings(
                display_name=row.display_name,
                pen_name=row.pen_name,
                bio=row.bio,
            ),
            models=self._model_settings_from_row(row),
        )

    def patch_personal(self, data: PersonalSettingsUpdate) -> SettingsResponse:
        row = self.repo.ensure_singleton()
        updates = data.model_dump(exclude_unset=True)
        if updates:
            row = self.repo.update(row, **updates)
        return SettingsResponse(
            personal=PersonalSettings(
                display_name=row.display_name,
                pen_name=row.pen_name,
                bio=row.bio,
            ),
            models=self._model_settings_from_row(row),
        )

    def patch_models(self, data: ModelSettingsUpdate) -> SettingsResponse:
        row = self.repo.ensure_singleton()
        updates = data.model_dump(exclude_unset=True)
        if "openai_api_key" in updates and updates["openai_api_key"] == "":
            updates["openai_api_key"] = None
        if "openai_api_key" in updates and updates["openai_api_key"] is None:
            updates.pop("openai_api_key")
        if updates.get("ai_provider") and updates["ai_provider"] not in ("mock", "openai"):
            raise AppError(400, "ai_provider must be mock or openai")
        if updates.get("default_model_profile") and updates["default_model_profile"] not in (
            "default",
            "fast",
            "quality",
        ):
            raise AppError(400, "default_model_profile must be default, fast, or quality")
        if updates:
            row = self.repo.update(row, **updates)
            refresh_effective_settings(row)
        return SettingsResponse(
            personal=PersonalSettings(
                display_name=row.display_name,
                pen_name=row.pen_name,
                bio=row.bio,
            ),
            models=self._model_settings_from_row(row),
        )

    def test_connection(self) -> ModelTestResponse:
        effective = get_effective_settings()
        if effective.ai_provider == "mock":
            return ModelTestResponse(ok=True, message="Mock 模式无需连接", provider="mock")
        if not effective.openai_api_key:
            return ModelTestResponse(ok=False, message="未配置 API Key", provider="openai")
        try:
            response = httpx.post(
                f"{effective.openai_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {effective.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": effective.ai_model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 5,
                },
                timeout=min(effective.ai_request_timeout_seconds, 30.0),
            )
            response.raise_for_status()
            return ModelTestResponse(ok=True, message="连接成功", provider="openai")
        except httpx.HTTPError as exc:
            return ModelTestResponse(ok=False, message=f"连接失败: {exc}", provider="openai")

    def effective_models(self) -> EffectiveModelsResponse:
        effective = get_effective_settings()
        rows: list[EffectiveModelRow] = []
        for stage in (ReadinessStage.OUTLINE, ReadinessStage.VOLUMES, ReadinessStage.CHAPTERS):
            for profile in (ModelProfile.DEFAULT, ModelProfile.FAST, ModelProfile.QUALITY):
                rows.append(
                    EffectiveModelRow(
                        target_stage=stage.value,
                        model_profile=profile.value,
                        model_name=resolve_model_name(stage, profile),
                    )
                )
        return EffectiveModelsResponse(provider=effective.ai_provider, rows=rows)

    def _model_settings_from_row(self, row: WorkspaceSettings) -> ModelSettings:
        return ModelSettings(
            ai_provider=row.ai_provider,
            ai_model=row.ai_model,
            openai_base_url=row.openai_base_url,
            openai_api_key_masked=mask_api_key(row.openai_api_key),
            ai_model_outline=row.ai_model_outline,
            ai_model_volume=row.ai_model_volume,
            ai_model_chapter=row.ai_model_chapter,
            ai_model_profile_fast=row.ai_model_profile_fast,
            ai_model_profile_quality=row.ai_model_profile_quality,
            ai_request_timeout_seconds=row.ai_request_timeout_seconds,
            ai_batch_max_chapters=row.ai_batch_max_chapters,
            default_model_profile=row.default_model_profile,
        )
