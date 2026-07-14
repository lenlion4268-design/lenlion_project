import json
from typing import Any

from app.domains.assets.models import CharacterCard
from app.domains.generation.context import GenerationContext


def _character_summary(cards: list[CharacterCard]) -> str:
    if not cards:
        return "（暂无已确认角色）"
    lines: list[str] = []
    for card in cards[:6]:
        profile = card.profile_json or {}
        goals = profile.get("goals", "")
        lines.append(f"- {card.name}：{goals or '待补充目标'}")
    return "\n".join(lines)


def build_outline_prompt(ctx: GenerationContext) -> str:
    theme = ctx.theme
    world = ctx.world
    return (
        f"项目：{ctx.project.title}\n"
        f"类型：{ctx.project.genre}\n"
        f"主题：{theme.theme if theme else ''}\n"
        f"叙事风格：{theme.narrative_style if theme else ''}\n"
        f"情感基调：{theme.emotional_tone if theme else ''}\n"
        f"世界观：{json.dumps(world.background_json if world else {}, ensure_ascii=False)}\n"
        f"核心角色：\n{_character_summary(ctx.characters)}\n"
        "请输出 JSON，字段：title, summary, plot_nodes_json, character_arcs_json, ending_direction。"
    )


def build_volume_prompt(ctx: GenerationContext) -> str:
    outline = ctx.outline
    return (
        f"项目：{ctx.project.title}\n"
        f"大纲标题：{outline.title if outline else ''}\n"
        f"大纲摘要：{outline.summary if outline else ''}\n"
        f"结局方向：{outline.ending_direction if outline else ''}\n"
        f"核心角色：\n{_character_summary(ctx.characters)}\n"
        f"本卷序号：{ctx.existing_chapter_count + 1}\n"
        "请输出 JSON，字段：title, stage_goal, main_conflict, key_events_json, "
        "involved_characters, emotional_rhythm, previous_relation, next_relation。"
    )


def _style_constraints(ctx: GenerationContext) -> str:
    profile = ctx.style_profile
    if profile is None:
        return ""
    data = profile.profile_json or {}
    techniques = data.get("techniques") or []
    taboo = (data.get("vocabulary") or {}).get("taboo") or []
    excerpts = data.get("example_excerpts") or []
    lines = [
        f"【文风约束】（模仿作者：{profile.author}，参考《{profile.reference_title}》）",
        f"- {profile.voice_summary}",
    ]
    for item in techniques[:6]:
        lines.append(f"- {item}")
    if taboo:
        lines.append(f"- 禁止：{'、'.join(str(item) for item in taboo[:5])}")
    for excerpt in excerpts[:2]:
        lines.append(f"- 参考摘录：{str(excerpt)[:300]}")
    return "\n".join(lines) + "\n"


def build_chapter_prompt(ctx: GenerationContext) -> str:
    volume = ctx.volume
    theme = ctx.theme
    style_block = _style_constraints(ctx)
    return (
        f"项目：{ctx.project.title}\n"
        f"主题：{theme.theme if theme else ''}\n"
        f"故事卷：{volume.title if volume else ''}\n"
        f"卷目标：{volume.stage_goal if volume else ''}\n"
        f"主要冲突：{volume.main_conflict if volume else ''}\n"
        f"关键事件：{json.dumps(volume.key_events_json if volume else [], ensure_ascii=False)}\n"
        f"涉及角色：{', '.join(volume.involved_characters if volume else [])}\n"
        f"章节序号：{ctx.existing_chapter_count + 1}\n"
        f"{style_block}"
        "请输出 JSON，字段：title, content。content 为完整章节正文，2000-4000 汉字。"
    )


def parse_json_response(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)
