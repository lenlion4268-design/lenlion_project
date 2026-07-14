from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.enums import ReferenceFormat, ReferenceWorkStatus
from app.domains.style.epub_reader import count_cjk_chars, extract_text_from_file
from app.domains.style.models import ReferenceSample, ReferenceWork
from app.domains.style.sampler import build_samples


@dataclass
class IngestResult:
    text: str
    word_count: int
    samples: list[tuple[str, str, int]]


def ingest_reference(reference: ReferenceWork) -> IngestResult:
    path = Path(reference.storage_path)
    text = extract_text_from_file(path, reference.format)
    word_count = count_cjk_chars(text)
    sample_tuples = build_samples(text, max_chars=settings.style_sample_max_chars)
    return IngestResult(text=text, word_count=word_count, samples=sample_tuples)


def persist_samples(
    db,
    reference_id: str,
    samples: list[tuple[str, str, int]],
) -> list[ReferenceSample]:
    created: list[ReferenceSample] = []
    for label, content, char_offset in samples:
        sample = ReferenceSample(
            reference_work_id=reference_id,
            label=label,
            content=content,
            char_offset=char_offset,
        )
        db.add(sample)
        created.append(sample)
    db.commit()
    for sample in created:
        db.refresh(sample)
    return created


def normalize_format(filename: str) -> str | None:
    lower = filename.lower()
    if lower.endswith(".txt"):
        return ReferenceFormat.TXT.value
    if lower.endswith(".md"):
        return ReferenceFormat.MD.value
    if lower.endswith(".epub"):
        return ReferenceFormat.EPUB.value
    return None


def mark_reference_ingested(reference: ReferenceWork, word_count: int) -> None:
    reference.word_count = word_count
    reference.status = ReferenceWorkStatus.INGESTED.value
