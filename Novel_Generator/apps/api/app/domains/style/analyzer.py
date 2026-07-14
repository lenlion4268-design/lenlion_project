from typing import Any

from app.core.enums import ReferenceWorkStatus
from app.domains.generation.prompt_builder import parse_json_response
from app.domains.settings.effective import get_effective_settings
from app.domains.style.models import ReferenceSample, ReferenceWork
from app.domains.style.prompts import MACRO_PROMPT, SYNTHESIS_PROMPT, TECHNIQUE_PROMPT
from app.domains.style.schemas import StyleProfileJson
from app.domains.style.skill_exporter import build_skill_markdown, default_profile_name


def _format_samples(samples: list[ReferenceSample]) -> str:
    parts: list[str] = []
    for sample in samples:
        parts.append(f"[{sample.label}]\n{sample.content[:2000]}")
    return "\n\n---\n\n".join(parts)


class MockStyleAnalyzer:
    def analyze(self, reference: ReferenceWork, samples: list[ReferenceSample]) -> dict[str, Any]:
        excerpt = samples[0].content[:120] if samples else "（无采样）"
        profile_json = StyleProfileJson(
            pov="第三人称限知",
            sentence_rhythm="短句为主，节奏紧凑",
            dialogue_ratio="约30%",
            pacing="快节奏推进",
            emotional_tone="克制冷静",
            vocabulary={"register": "偏口语化", "taboo": ["过度书面排比", "冗长环境铺陈"]},
            techniques=["以动作开篇", "对话推动情节", "章末留悬念"],
            hooks=["章末 unanswered 问句"],
            example_excerpts=[excerpt],
        )
        voice_summary = f"{reference.author} 式冷峻紧凑叙事，对话驱动，留白克制。"
        skill_markdown = (
            f"# 文风：{reference.author}\n"
            f"> 参考作品：《{reference.title}》\n\n"
            "## 核心规则\n"
            f"- {voice_summary}\n"
            "- 短句为主，每段推进一个信息点\n"
            "- 对话简洁，少用「他说道」\n\n"
            "## 禁止事项\n"
            "- 避免大段环境描写\n"
            "- 避免过度形容词堆砌\n"
        )
        return {
            "voice_summary": voice_summary,
            "profile_json": profile_json.model_dump(),
            "skill_markdown": skill_markdown,
            "name": default_profile_name(reference.author, voice_summary),
        }


class OpenAiStyleAnalyzer:
    def __init__(self) -> None:
        import httpx

        effective = get_effective_settings()
        if not effective.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY required")
        self._httpx = httpx
        self.effective = effective
        self.model = effective.ai_model

    def analyze(self, reference: ReferenceWork, samples: list[ReferenceSample]) -> dict[str, Any]:
        sample_text = _format_samples(samples)
        macro = self._chat_json(
            MACRO_PROMPT.format(
                author=reference.author,
                title=reference.title,
                word_count=reference.word_count,
                samples=sample_text,
            )
        )
        technique = self._chat_json(
            TECHNIQUE_PROMPT.format(author=reference.author, samples=sample_text)
        )
        synthesis = self._chat_json(
            SYNTHESIS_PROMPT.format(
                author=reference.author,
                title=reference.title,
                macro=macro,
                technique=technique,
            )
        )
        profile_json = synthesis.get("profile_json", {})
        if isinstance(profile_json, dict):
            merged = {**macro, **technique, **profile_json}
            profile_json = StyleProfileJson.model_validate(merged).model_dump()
        voice_summary = str(synthesis.get("voice_summary", ""))
        skill_markdown = str(synthesis.get("skill_markdown", "")) or build_skill_markdown_from_parts(
            reference, voice_summary, profile_json
        )
        return {
            "voice_summary": voice_summary,
            "profile_json": profile_json,
            "skill_markdown": skill_markdown,
            "name": default_profile_name(reference.author, voice_summary),
        }

    def _chat_json(self, user: str) -> dict[str, Any]:
        response = self._httpx.post(
            f"{self.effective.openai_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.effective.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是文学风格分析专家，只返回 JSON。"},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.4,
                "response_format": {"type": "json_object"},
            },
            timeout=self.effective.ai_request_timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        parsed = parse_json_response(str(content))
        return parsed if isinstance(parsed, dict) else {}


def build_skill_markdown_from_parts(reference: ReferenceWork, voice_summary: str, profile_json: dict) -> str:
    profile = StyleProfileJson.model_validate(profile_json)
    lines = [
        f"# 文风：{reference.author}",
        f"> 参考作品：《{reference.title}》",
        "",
        "## 核心规则",
        voice_summary,
    ]
    if profile.techniques:
        lines.extend(["", *[f"- {item}" for item in profile.techniques]])
    if profile.vocabulary.taboo:
        lines.extend(["", "## 禁止事项", *[f"- {item}" for item in profile.vocabulary.taboo]])
    return "\n".join(lines)


def get_style_analyzer():
    if get_effective_settings().ai_provider == "openai":
        return OpenAiStyleAnalyzer()
    return MockStyleAnalyzer()
