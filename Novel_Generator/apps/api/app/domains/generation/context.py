from dataclasses import dataclass, field

from app.domains.assets.models import CharacterCard, Outline, ThemeProfile, Volume, WorldSetting
from app.domains.projects.models import NovelProject
from app.domains.style.models import StyleProfile


@dataclass
class GenerationContext:
    project: NovelProject
    theme: ThemeProfile | None = None
    world: WorldSetting | None = None
    characters: list[CharacterCard] = field(default_factory=list)
    outline: Outline | None = None
    volume: Volume | None = None
    existing_chapter_count: int = 0
    style_profile: StyleProfile | None = None
