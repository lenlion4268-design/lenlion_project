from app.domains.settings.effective import get_effective_settings
from app.domains.generation.context import GenerationContext
from app.domains.generation.prompt_builder import build_outline_prompt, build_volume_prompt
from app.domains.generation.schemas import ChapterDraft, OutlineDraft, VolumeDraft


class MockAiProvider:
    """Deterministic mock generator for local development and tests."""

    def generate_outline(self, ctx: GenerationContext) -> OutlineDraft:
        theme = ctx.theme.theme if ctx.theme and ctx.theme.theme else "未命名主题"
        genre = ctx.project.genre or (ctx.theme.genre if ctx.theme else "")
        character_names = [card.name for card in ctx.characters[:3]]
        cast = "、".join(character_names) if character_names else "主角"

        return OutlineDraft(
            title=f"{ctx.project.title} · AI 大纲草案",
            summary=(
                f"【{genre}】围绕「{theme}」展开，{cast} 将在冲突与抉择中推动主线。"
                "本草案由 mock 提供方根据已确认的创作资产自动生成。"
            ),
            plot_nodes_json=[
                {"act": 1, "beat": "引入世界观与核心矛盾"},
                {"act": 2, "beat": "升级冲突并揭示隐藏动机"},
                {"act": 3, "beat": "高潮对决与主题收束"},
            ],
            character_arcs_json=[
                {"name": name, "arc": "从被动应对到主动承担"} for name in character_names
            ],
            ending_direction="主线矛盾得到阶段性解决，并为下一卷留下悬念。",
        )

    def generate_volume(self, ctx: GenerationContext) -> VolumeDraft:
        outline_title = ctx.outline.title if ctx.outline and ctx.outline.title else "主线"
        volume_no = max(1, ctx.existing_chapter_count + 1)
        involved = [card.name for card in ctx.characters[:4]]

        return VolumeDraft(
            volume_no=volume_no,
            title=f"第 {volume_no} 卷 · {outline_title}",
            stage_goal=f"推进「{outline_title}」的第一阶段目标，建立本卷核心矛盾。",
            main_conflict="主角与对立势力因利益与信念产生正面冲突。",
            key_events_json=[
                {"order": 1, "event": "触发事件：打破现状的意外"},
                {"order": 2, "event": "中点转折：代价与选择"},
                {"order": 3, "event": "卷末高潮：阶段性胜负"},
            ],
            involved_characters=involved,
            emotional_rhythm="压抑 → 爆发 → 余韵",
            previous_relation="承接大纲既定走向，开启新的阶段目标。",
            next_relation="为后续卷的冲突升级埋下伏笔。",
            outline_id=ctx.outline.id if ctx.outline else None,
        )

    def generate_chapter(self, ctx: GenerationContext) -> ChapterDraft:
        volume = ctx.volume
        chapter_no = ctx.existing_chapter_count + 1
        volume_title = volume.title if volume and volume.title else f"第 {volume.volume_no if volume else 1} 卷"
        theme = ctx.theme.theme if ctx.theme and ctx.theme.theme else "故事"

        content = (
            f"第 {chapter_no} 章\n\n"
            f"（mock 生成 · {get_effective_settings().ai_provider}）\n\n"
            f"在「{volume_title}」中，{theme} 的主线继续推进。"
            "主角面对新的局面，细节与对话可在编辑器中继续润色。\n\n"
            "—— 本章由 AI 生成流水线自动创建，状态为草稿，需作者确认后进入成稿。"
        )
        return ChapterDraft(
            chapter_no=chapter_no,
            title=f"第 {chapter_no} 章",
            content=content,
        )
