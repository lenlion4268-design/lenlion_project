from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import settings as env_settings
from app.domains.settings.models import WORKSPACE_SETTINGS_ID, WorkspaceSettings


class SettingsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_singleton(self) -> WorkspaceSettings | None:
        return self.db.get(WorkspaceSettings, WORKSPACE_SETTINGS_ID)

    def ensure_singleton(self) -> WorkspaceSettings:
        row = self.get_singleton()
        if row is not None:
            return row

        row = WorkspaceSettings(
            id=WORKSPACE_SETTINGS_ID,
            ai_provider=env_settings.ai_provider,
            ai_model=env_settings.ai_model,
            openai_base_url=env_settings.openai_base_url,
            openai_api_key=env_settings.openai_api_key,
            ai_model_outline=env_settings.ai_model_outline,
            ai_model_volume=env_settings.ai_model_volume,
            ai_model_chapter=env_settings.ai_model_chapter,
            ai_model_profile_fast=env_settings.ai_model_profile_fast,
            ai_model_profile_quality=env_settings.ai_model_profile_quality,
            ai_request_timeout_seconds=env_settings.ai_request_timeout_seconds,
            ai_batch_max_chapters=env_settings.ai_batch_max_chapters,
            default_model_profile="default",
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def update(self, row: WorkspaceSettings, **fields: object) -> WorkspaceSettings:
        for key, value in fields.items():
            setattr(row, key, value)
        row.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(row)
        return row
