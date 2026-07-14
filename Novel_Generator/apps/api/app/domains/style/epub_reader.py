import re
import zipfile
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)


def extract_epub_metadata(path: Path) -> tuple[str | None, str | None]:
    author: str | None = None
    title: str | None = None
    try:
        with zipfile.ZipFile(path) as archive:
            opf_path = _find_opf_path(archive)
            if opf_path is None:
                return None, None
            root = ElementTree.fromstring(archive.read(opf_path))
            ns = {"dc": "http://purl.org/dc/elements/1.1/"}
            creator = root.find(".//dc:creator", ns)
            dc_title = root.find(".//dc:title", ns)
            if creator is not None and creator.text:
                author = creator.text.strip()
            if dc_title is not None and dc_title.text:
                title = dc_title.text.strip()
    except (OSError, zipfile.BadZipFile, ElementTree.ParseError):
        return None, None
    return author, title


def _find_opf_path(archive: zipfile.ZipFile) -> str | None:
    try:
        container = ElementTree.fromstring(archive.read("META-INF/container.xml"))
    except KeyError:
        return None
    rootfile = container.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
    if rootfile is None:
        return None
    return rootfile.attrib.get("full-path")


def extract_epub_text(path: Path) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.lower().endswith((".xhtml", ".html", ".htm")):
                raw = archive.read(name).decode("utf-8", errors="ignore")
                parser = _TextExtractor()
                parser.feed(raw)
                if parser.parts:
                    chunks.append("\n".join(parser.parts))
    return "\n\n".join(chunks)


def extract_text_from_file(path: Path, fmt: str) -> str:
    if fmt == "epub":
        return extract_epub_text(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def count_cjk_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text)) or len(text.split())
