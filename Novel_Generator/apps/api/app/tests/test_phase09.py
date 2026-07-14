import io
import zipfile

from app.core.config import settings
from app.domains.generation.prompt_builder import build_chapter_prompt
from app.domains.generation.context import GenerationContext
from app.domains.style.epub_reader import extract_epub_metadata, extract_epub_text
from app.domains.style.models import StyleProfile
from app.domains.style.sampler import build_samples
from app.tests.test_export import _setup_locked_chapter
from app.tests.test_generation import _create_project


def _upload_reference(client, *, author: str, title: str, content: str, ext: str = "txt"):
    files = {"file": (f"ref.{ext}", content.encode("utf-8"), "text/plain")}
    data = {"author": author, "title": title}
    return client.post(
        f"{settings.api_prefix}/materials/references/upload",
        data=data,
        files=files,
    )


def test_upload_requires_author(client) -> None:
    files = {"file": ("ref.txt", b"hello", "text/plain")}
    response = client.post(
        f"{settings.api_prefix}/materials/references/upload",
        data={"author": "  "},
        files=files,
    )
    assert response.status_code == 400


def test_upload_without_project(client) -> None:
    content = "开篇内容。\n\n" + ("中间段落内容。" * 50) + "\n\n「对话一」\n「对话二」"
    response = _upload_reference(
        client,
        author="刘慈欣",
        title="三体",
        content=content,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["author"] == "刘慈欣"
    assert data["title"] == "三体"
    assert data["status"] == "ingested"
    assert data["project_id"] is None

    listing = client.get(f"{settings.api_prefix}/materials/references")
    assert listing.status_code == 200
    assert listing.json()["items"][0]["author"] == "刘慈欣"


def test_sampler_respects_max_chars() -> None:
    text = "段落。\n\n" * 500
    samples = build_samples(text, max_chars=3000)
    total = sum(len(item[1]) for item in samples)
    assert total <= 3000
    assert samples[0][0] == "opening"


def test_analyze_creates_style_profile(client) -> None:
    upload = _upload_reference(
        client,
        author="村上春树",
        title="挪威的森林",
        content="「你好，」他说。\n\n" + ("独白段落。" * 80),
    )
    reference_id = upload.json()["id"]

    analyze = client.post(
        f"{settings.api_prefix}/materials/references/{reference_id}/analyze",
    )
    assert analyze.status_code == 201
    job = analyze.json()
    assert job["status"] == "succeeded"
    assert job["style_profile_id"]

    profiles = client.get(f"{settings.api_prefix}/materials/style-profiles")
    profile = profiles.json()["items"][0]
    assert profile["author"] == "村上春树"
    assert "村上春树 文风" in profile["name"]
    assert profile["project_id"] is None


def test_bind_requires_locked_profile(client) -> None:
    project_id = _create_project(client)
    upload = _upload_reference(client, author="作者A", title="作品A", content="正文" * 100)
    reference_id = upload.json()["id"]
    client.post(f"{settings.api_prefix}/materials/references/{reference_id}/analyze")
    profile_id = client.get(f"{settings.api_prefix}/materials/style-profiles").json()["items"][0]["id"]

    bind = client.post(
        f"{settings.api_prefix}/projects/{project_id}/materials/style-profiles/{profile_id}/bind",
    )
    assert bind.status_code == 403

    client.post(f"{settings.api_prefix}/materials/style-profiles/{profile_id}/lock")
    bind = client.post(
        f"{settings.api_prefix}/projects/{project_id}/materials/style-profiles/{profile_id}/bind",
    )
    assert bind.status_code == 200
    assert bind.json()["author"] == "作者A"


def test_chapter_prompt_includes_author_style(client, db_session) -> None:
    project_id = _create_project(client, title="注入测试")
    upload = _upload_reference(client, author="余华", title="活着", content="开头。" * 200)
    reference_id = upload.json()["id"]
    client.post(f"{settings.api_prefix}/materials/references/{reference_id}/analyze")
    profile_id = client.get(f"{settings.api_prefix}/materials/style-profiles").json()["items"][0]["id"]
    client.post(f"{settings.api_prefix}/materials/style-profiles/{profile_id}/lock")
    client.post(f"{settings.api_prefix}/projects/{project_id}/materials/style-profiles/{profile_id}/bind")

    volume_id, _ = _setup_locked_chapter(client, project_id)
    from app.domains.projects.models import NovelProject
    from app.domains.assets.models import Volume

    project = db_session.get(NovelProject, project_id)
    volume = db_session.get(Volume, volume_id)
    profile = db_session.get(StyleProfile, profile_id)
    prompt = build_chapter_prompt(
        GenerationContext(project=project, volume=volume, style_profile=profile)  # type: ignore[arg-type]
    )
    assert "模仿作者：余华" in prompt
    assert "【文风约束】" in prompt


def test_skill_export_has_author_frontmatter(client) -> None:
    upload = _upload_reference(client, author="鲁迅", title="呐喊", content="文本" * 100)
    reference_id = upload.json()["id"]
    client.post(f"{settings.api_prefix}/materials/references/{reference_id}/analyze")
    profile_id = client.get(f"{settings.api_prefix}/materials/style-profiles").json()["items"][0]["id"]

    download = client.get(
        f"{settings.api_prefix}/materials/style-profiles/{profile_id}/export/skill",
    )
    assert download.status_code == 200
    with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
        skill = archive.read("SKILL.md").decode("utf-8")
    assert "name: style-" in skill
    assert "鲁迅" in skill
    assert "按 鲁迅" in skill


def test_epub_metadata_extraction(tmp_path) -> None:
    from app.domains.generation.epub_builder import build_epub

    class FakeChapter:
        title = "第一章"
        chapter_no = 1
        content = "正文"

    epub_bytes = build_epub("测试书名", [FakeChapter()])  # type: ignore[list-item]
    path = tmp_path / "test.epub"
    path.write_bytes(epub_bytes)
    author, title = extract_epub_metadata(path)
    assert title == "测试书名"
    text = extract_epub_text(path)
    assert "正文" in text
