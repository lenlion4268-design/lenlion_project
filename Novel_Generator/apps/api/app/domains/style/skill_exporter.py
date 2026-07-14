import re
import unicodedata
import zipfile
from io import BytesIO

from app.domains.style.models import StyleProfile
from app.domains.style.schemas import StyleProfileJson


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "author"


def default_profile_name(author: str, voice_summary: str) -> str:
    short = voice_summary[:20].strip() if voice_summary else ""
    if short:
        return f"{author} 文风 · {short}"
    return f"{author} 文风"


def build_skill_frontmatter(profile: StyleProfile) -> str:
    author_slug = slugify(profile.author)
    name = f"style-{author_slug}"
    description = (
        f"按 {profile.author}（《{profile.reference_title}》）文风写作；"
        "章节生成或用户要求模仿该作者风格时使用"
    )
    return f"---\nname: {name}\ndescription: {description}\n---"


def build_skill_markdown(profile: StyleProfile) -> str:
    body = profile.skill_markdown.strip()
    if body:
        return body
    data = StyleProfileJson.model_validate(profile.profile_json or {})
    lines = [
        f"# 文风：{profile.author}",
        f"> 参考作品：《{profile.reference_title}》",
        "",
        "## 核心规则",
        profile.voice_summary or "（待补充）",
    ]
    if data.techniques:
        lines.extend(["", "### 写作手法", *[f"- {item}" for item in data.techniques]])
    if data.vocabulary.taboo:
        lines.extend(["", "## 禁止事项", *[f"- {item}" for item in data.vocabulary.taboo]])
    if data.example_excerpts:
        lines.extend(["", "## 参考摘录", *[f"> {item[:300]}" for item in data.example_excerpts[:3]]])
    return "\n".join(lines)


def build_reference_markdown(profile: StyleProfile) -> str:
    return (
        f"# 文风参考\n\n"
        f"作者：{profile.author}\n"
        f"作品：《{profile.reference_title}》\n\n"
        f"## Voice Summary\n\n{profile.voice_summary}\n\n"
        f"## Profile JSON\n\n```json\n{profile.profile_json}\n```\n"
    )


def build_examples_markdown(profile: StyleProfile) -> str:
    data = StyleProfileJson.model_validate(profile.profile_json or {})
    lines = [f"# {profile.author} 文风摘录", ""]
    for index, excerpt in enumerate(data.example_excerpts[:5], start=1):
        lines.extend([f"## 摘录 {index}", "", excerpt, ""])
    return "\n".join(lines).strip() + "\n"


def export_skill_zip(profile: StyleProfile) -> bytes:
    buffer = BytesIO()
    frontmatter = build_skill_frontmatter(profile)
    skill_body = build_skill_markdown(profile)
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("SKILL.md", f"{frontmatter}\n\n{skill_body}\n")
        archive.writestr("reference.md", build_reference_markdown(profile))
        archive.writestr("examples.md", build_examples_markdown(profile))
    return buffer.getvalue()
