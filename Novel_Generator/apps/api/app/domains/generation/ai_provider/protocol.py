from typing import Protocol

from app.domains.generation.context import GenerationContext
from app.domains.generation.schemas import ChapterDraft, OutlineDraft, VolumeDraft


class AiProvider(Protocol):
    def generate_outline(self, ctx: GenerationContext) -> OutlineDraft: ...

    def generate_volume(self, ctx: GenerationContext) -> VolumeDraft: ...

    def generate_chapter(self, ctx: GenerationContext) -> ChapterDraft: ...
