import re


def _split_paragraphs(text: str) -> list[tuple[str, int]]:
    paragraphs: list[tuple[str, int]] = []
    offset = 0
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            offset += 1
            continue
        paragraphs.append((block, offset))
        offset += len(block) + 2
    return paragraphs


def _quote_density(paragraph: str) -> float:
    if not paragraph:
        return 0.0
    quotes = paragraph.count("\u201c") + paragraph.count("\u201d") + paragraph.count('"') + paragraph.count("\u300c") + paragraph.count("\u300d")
    return quotes / max(len(paragraph), 1)


def build_samples(text: str, *, max_chars: int) -> list[tuple[str, str, int]]:
    cleaned = text.strip()
    if not cleaned:
        return [("empty", "（无正文）", 0)]

    samples: list[tuple[str, str, int]] = []
    used = 0

    opening = cleaned[:2500]
    samples.append(("opening", opening, 0))
    used += len(opening)

    paragraphs = _split_paragraphs(cleaned)
    if len(paragraphs) >= 2:
        mid_indices = [len(paragraphs) // 3, (2 * len(paragraphs)) // 3]
        for index, pos in enumerate(mid_indices):
            para, offset = paragraphs[min(pos, len(paragraphs) - 1)]
            label = f"middle_{index + 1}"
            if used + len(para) <= max_chars:
                samples.append((label, para, offset))
                used += len(para)

    dialogue_candidates = sorted(paragraphs, key=lambda item: _quote_density(item[0]), reverse=True)
    dialogue_count = 0
    for para, offset in dialogue_candidates:
        if dialogue_count >= 2:
            break
        if _quote_density(para) < 0.01:
            continue
        if used + len(para) > max_chars:
            break
        samples.append((f"dialogue_{dialogue_count + 1}", para, offset))
        used += len(para)
        dialogue_count += 1

    return samples
