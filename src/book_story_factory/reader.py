"""Read locally supplied books and index text with source positions."""
from __future__ import annotations

import hashlib
import json
import posixpath
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET


HEADING = re.compile(
    r"(?m)^(?:第[一二三四五六七八九十百千零〇0-9]+[章节篇回卷]|序章|楔子|尾声|Chapter\s+\d+)\s*[^\n]{0,65}$",
    re.IGNORECASE,
)


class _XhtmlText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"p", "h1", "h2", "h3", "div", "br", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _read_epub(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        container = ET.fromstring(archive.read("META-INF/container.xml"))
        rootfile = next(x for x in container.iter() if x.tag.endswith("rootfile"))
        opf_path = rootfile.attrib["full-path"]
        package = ET.fromstring(archive.read(opf_path))
        manifest = {
            x.attrib["id"]: x.attrib.get("href", "")
            for x in package.iter() if x.tag.endswith("item") and "id" in x.attrib
        }
        spine = [
            x.attrib["idref"]
            for x in package.iter() if x.tag.endswith("itemref") and "idref" in x.attrib
        ]
        sections: list[str] = []
        for item_id in spine:
            href = manifest.get(item_id, "")
            if not href.lower().split("#")[0].endswith((".html", ".xhtml", ".htm")):
                continue
            member = posixpath.normpath(posixpath.join(
                posixpath.dirname(opf_path), unquote(href.split("#")[0])
            ))
            parser = _XhtmlText()
            parser.feed(archive.read(member).decode("utf-8-sig", errors="replace"))
            sections.append("".join(parser.parts))
        return "\n\n".join(sections)


def read_book(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        text = path.read_text(encoding="utf-8-sig")
    elif suffix == ".epub":
        text = _read_epub(path)
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("Install PDF support with pip install -e '.[pdf]'") from exc
        text = "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    else:
        raise ValueError(f"Unsupported book type: {suffix}")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        raise ValueError("No readable text found. Scanned PDFs require OCR separately.")
    return text


def build_index(path: Path, max_chars: int = 6000) -> dict:
    if max_chars < 500:
        raise ValueError("max_chars must be >= 500")
    raw = read_book(path)
    chapters: list[tuple[int, str]] = [(0, "全文开头")]
    offset = 0
    for line in raw.splitlines(keepends=True):
        if HEADING.fullmatch(line.strip()):
            if offset == 0:
                chapters[0] = (0, line.strip())
            elif offset > chapters[-1][0]:
                chapters.append((offset, line.strip()))
        offset += len(line)
    chapters.append((len(raw), "END"))
    chunks: list[dict] = []
    for i in range(len(chapters) - 1):
        start, title = chapters[i]
        stop = chapters[i + 1][0]
        while start < stop:
            end = min(start + max_chars, stop)
            if end < stop:
                split_at = raw.rfind("\n", start + max_chars // 2, end)
                if split_at > start:
                    end = split_at + 1
            body = raw[start:end]
            if body.strip():
                chunks.append({
                    "id": f"chunk-{len(chunks)+1:04d}",
                    "chapter": title,
                    "start_char": start,
                    "end_char": end,
                    "text": body,
                })
            start = end
    return {
        "source_name": path.name,
        "source_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "total_chars": len(raw),
        "chunks": chunks,
        "index_version": 1,
    }


def prepare_book(source: Path, out: Path, max_chars: int = 6000) -> dict:
    index = build_index(source, max_chars=max_chars)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    return index
