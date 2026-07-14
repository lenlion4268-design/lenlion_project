import io
import uuid
import zipfile
from html import escape

from app.domains.generation.models import Chapter


def _xhtml_chapter(chapter_id: str, title: str, body: str) -> str:
    paragraphs = "".join(
        f"<p>{escape(line)}</p>" for line in body.splitlines() if line.strip()
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{escape(title)}</title></head>
<body>
  <h1>{escape(title)}</h1>
  {paragraphs or "<p></p>"}
</body>
</html>"""


def build_epub(book_title: str, chapters: list[Chapter]) -> bytes:
    book_id = str(uuid.uuid4())
    buffer = io.BytesIO()

    chapter_items: list[tuple[str, str, str]] = []
    for index, chapter in enumerate(chapters, start=1):
        chapter_id = f"chapter-{index:03d}"
        title = chapter.title or f"第 {chapter.chapter_no} 章"
        chapter_items.append((chapter_id, title, chapter.content))

    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
        )

        manifest_items = ['<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>']
        spine_items = []
        nav_points = []

        for index, (chapter_id, title, body) in enumerate(chapter_items, start=1):
            archive.writestr(
                f"OEBPS/{chapter_id}.xhtml",
                _xhtml_chapter(chapter_id, title, body),
            )
            manifest_items.append(
                f'<item id="{chapter_id}" href="{chapter_id}.xhtml" media-type="application/xhtml+xml"/>'
            )
            spine_items.append(f'<itemref idref="{chapter_id}"/>')
            nav_points.append(
                f"""<navPoint id="navPoint-{index}" playOrder="{index}">
      <navLabel><text>{escape(title)}</text></navLabel>
      <content src="{chapter_id}.xhtml"/>
    </navPoint>"""
            )

        archive.writestr(
            "OEBPS/content.opf",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{escape(book_title)}</dc:title>
    <dc:language>zh-CN</dc:language>
    <dc:identifier id="BookId">urn:uuid:{book_id}</dc:identifier>
  </metadata>
  <manifest>
    {''.join(manifest_items)}
  </manifest>
  <spine toc="ncx">
    {''.join(spine_items)}
  </spine>
</package>""",
        )
        archive.writestr(
            "OEBPS/toc.ncx",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:{book_id}"/>
    <meta name="dtb:depth" content="1"/>
  </head>
  <docTitle><text>{escape(book_title)}</text></docTitle>
  <navMap>
    {''.join(nav_points)}
  </navMap>
</ncx>""",
        )

    return buffer.getvalue()
