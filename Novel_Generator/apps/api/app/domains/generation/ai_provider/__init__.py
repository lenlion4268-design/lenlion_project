from app.core.errors import AppError
from app.domains.generation.ai_provider.mock import MockAiProvider
from app.domains.generation.ai_provider.openai import OpenAiCompatibleProvider
from app.domains.generation.ai_provider.protocol import AiProvider
from app.domains.settings.effective import get_effective_settings


def get_ai_provider(name: str | None = None, *, model: str | None = None) -> AiProvider:
    provider_name = name or get_effective_settings().ai_provider
    if provider_name == "mock":
        return MockAiProvider()
    if provider_name == "openai":
        return OpenAiCompatibleProvider(model=model)
    raise AppError(400, f"Unsupported AI provider: {provider_name}")
