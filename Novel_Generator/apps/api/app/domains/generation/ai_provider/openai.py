import httpx

from app.core.errors import AppError
from app.domains.generation.context import GenerationContext
from app.domains.generation.prompt_builder import (
    build_chapter_prompt,
    build_outline_prompt,
    build_volume_prompt,
    parse_json_response,
)
from app.domains.generation.schemas import ChapterDraft, OutlineDraft, VolumeDraft
from app.domains.settings.effective import get_effective_settings


class OpenAiCompatibleProvider:
    """OpenAI-compatible chat completions provider."""

    def __init__(self, model: str | None = None) -> None:
        effective = get_effective_settings()
        if not effective.openai_api_key:
            raise AppError(
                503,
                "OPENAI_API_KEY is required when AI_PROVIDER=openai",
            )
        self.effective = effective
        self.model = model or effective.ai_model

    def generate_outline(self, ctx: GenerationContext) -> OutlineDraft:
        payload = self._chat_json(
            system=(
                "你是资深小说策划，请根据创作资产生成大纲草案。"
                "只返回 JSON，不要 markdown 说明。"
            ),
            user=build_outline_prompt(ctx),
        )
        return OutlineDraft(
            title=str(payload.get("title", f"{ctx.project.title} · AI 大纲")),
            summary=str(payload.get("summary", "")),
            plot_nodes_json=list(payload.get("plot_nodes_json", [])),
            character_arcs_json=list(payload.get("character_arcs_json", [])),
            ending_direction=str(payload.get("ending_direction", "")),
        )

    def generate_volume(self, ctx: GenerationContext) -> VolumeDraft:
        payload = self._chat_json(
            system=(
                "你是资深小说编辑，请根据大纲生成故事卷草案。"
                "只返回 JSON，不要 markdown 说明。"
            ),
            user=build_volume_prompt(ctx),
        )
        volume_no = max(1, ctx.existing_chapter_count + 1)
        involved = payload.get("involved_characters")
        if not isinstance(involved, list):
            involved = [card.name for card in ctx.characters[:4]]
        return VolumeDraft(
            volume_no=volume_no,
            title=str(payload.get("title", f"第 {volume_no} 卷")),
            stage_goal=str(payload.get("stage_goal", "")),
            main_conflict=str(payload.get("main_conflict", "")),
            key_events_json=list(payload.get("key_events_json", [])),
            involved_characters=[str(name) for name in involved],
            emotional_rhythm=str(payload.get("emotional_rhythm", "")),
            previous_relation=str(payload.get("previous_relation", "")),
            next_relation=str(payload.get("next_relation", "")),
            outline_id=ctx.outline.id if ctx.outline else None,
        )

    def generate_chapter(self, ctx: GenerationContext) -> ChapterDraft:
        payload = self._chat_json(
            system=(
                "你是中文网文作者，请根据故事卷设定撰写章节正文。"
                "只返回 JSON，字段 title 与 content。"
            ),
            user=build_chapter_prompt(ctx),
        )
        chapter_no = ctx.existing_chapter_count + 1
        return ChapterDraft(
            chapter_no=chapter_no,
            title=str(payload.get("title", f"第 {chapter_no} 章")),
            content=str(payload.get("content", "")),
        )

    def _chat_json(self, *, system: str, user: str) -> dict:
        try:
            response = httpx.post(
                f"{self.effective.openai_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.effective.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"},
                },
                timeout=self.effective.ai_request_timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            return parse_json_response(str(content))
        except httpx.HTTPError as exc:
            raise AppError(502, f"LLM request failed: {exc}") from exc
        except (KeyError, IndexError, ValueError) as exc:
            raise AppError(502, f"Invalid LLM response: {exc}") from exc
