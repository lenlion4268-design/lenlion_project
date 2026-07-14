from pydantic import BaseModel, Field


class PersonalSettings(BaseModel):
    display_name: str | None = None
    pen_name: str | None = None
    bio: str | None = None


class PersonalSettingsUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=255)
    pen_name: str | None = Field(default=None, max_length=255)
    bio: str | None = None


class ModelSettings(BaseModel):
    ai_provider: str
    ai_model: str
    openai_base_url: str
    openai_api_key_masked: str | None = None
    ai_model_outline: str | None = None
    ai_model_volume: str | None = None
    ai_model_chapter: str | None = None
    ai_model_profile_fast: str | None = None
    ai_model_profile_quality: str | None = None
    ai_request_timeout_seconds: float
    ai_batch_max_chapters: int
    default_model_profile: str


class ModelSettingsUpdate(BaseModel):
    ai_provider: str | None = None
    ai_model: str | None = Field(default=None, max_length=100)
    openai_base_url: str | None = Field(default=None, max_length=500)
    openai_api_key: str | None = None
    ai_model_outline: str | None = Field(default=None, max_length=100)
    ai_model_volume: str | None = Field(default=None, max_length=100)
    ai_model_chapter: str | None = Field(default=None, max_length=100)
    ai_model_profile_fast: str | None = Field(default=None, max_length=100)
    ai_model_profile_quality: str | None = Field(default=None, max_length=100)
    ai_request_timeout_seconds: float | None = None
    ai_batch_max_chapters: int | None = Field(default=None, ge=1, le=20)
    default_model_profile: str | None = None


class SettingsResponse(BaseModel):
    personal: PersonalSettings
    models: ModelSettings


class ModelTestResponse(BaseModel):
    ok: bool
    message: str
    provider: str


class EffectiveModelRow(BaseModel):
    target_stage: str
    model_profile: str
    model_name: str


class EffectiveModelsResponse(BaseModel):
    provider: str
    rows: list[EffectiveModelRow]
