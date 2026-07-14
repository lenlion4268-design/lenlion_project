from app.core.enums import ModelProfile, ReadinessStage
from app.domains.generation.model_router import resolve_model_name
from app.domains.settings.effective import get_effective_settings


def test_resolve_model_name_uses_stage_override() -> None:
    effective = get_effective_settings()
    effective.ai_model = "default-model"
    effective.ai_model_chapter = "chapter-model"
    assert resolve_model_name(ReadinessStage.CHAPTERS, ModelProfile.DEFAULT) == "chapter-model"


def test_resolve_model_name_uses_fast_profile() -> None:
    effective = get_effective_settings()
    effective.ai_model = "default-model"
    effective.ai_model_chapter = None
    effective.ai_model_profile_fast = "fast-model"
    assert resolve_model_name(ReadinessStage.CHAPTERS, ModelProfile.FAST) == "fast-model"
