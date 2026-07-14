from app.core.enums import ModelProfile, ReadinessStage
from app.domains.settings.effective import get_effective_settings


def resolve_model_name(
    target_stage: ReadinessStage,
    profile: ModelProfile = ModelProfile.DEFAULT,
) -> str:
    effective = get_effective_settings()
    stage_models = {
        ReadinessStage.OUTLINE: effective.ai_model_outline,
        ReadinessStage.VOLUMES: effective.ai_model_volume,
        ReadinessStage.CHAPTERS: effective.ai_model_chapter,
    }
    stage_model = stage_models.get(target_stage)
    if stage_model:
        return stage_model

    if profile == ModelProfile.FAST and effective.ai_model_profile_fast:
        return effective.ai_model_profile_fast
    if profile == ModelProfile.QUALITY and effective.ai_model_profile_quality:
        return effective.ai_model_profile_quality

    if profile == ModelProfile.FAST:
        return effective.ai_model if effective.ai_model != "mock-writer" else "gpt-4o-mini"
    if profile == ModelProfile.QUALITY:
        return effective.ai_model if effective.ai_model != "mock-writer" else "gpt-4o"

    return effective.ai_model
