"""Load pages from a local directory, a ``sitemap.xml`` file, or a URL list.

Everything here is fully offline: directory sources are read from disk, and
sitemap/URL-list sources parse the given file. When those sources point at
local files (via ``base_dir``), titles and descriptions are extracted from the
files; otherwise a title is derived from the URL slug.

Title/description extraction:
    * HTML  -- ``<title>`` (or first ``<h1>``), ``<meta name=description>``
      (or the first ``<p>``), via BeautifulSoup.
    * Markdown -- the first ``# `` heading and the first prose paragraph, via a
      small stdlib line scan.
"""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .models import Page

HTML_EXTENSIONS = {".html", ".htm"}
MARKDOWN_EXTENSIONS = {".md", ".markdown"}
INDEX_STEMS = {"index", "readme", "home"}
DESCRIPTION_MAX_CHARS = 200


# --------------------------------------------------------------------------- #
# Small text helpers
# --------------------------------------------------------------------------- #
def _collapse_whitespace(text: str) -> str:
    """Collapse all runs of whitespace into single spaces and strip ends."""
    return re.sub(r"\s+", " ", text or "").strip()


def _truncate(text: str, limit: int = DESCRIPTION_MAX_CHARS) -> str:
    """Truncate ``text`` to ``limit`` characters on a word boundary."""
    text = _collapse_whitespace(text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{cut}…"


def humanize(slug: str) -> str:
    """Turn a file stem or URL slug into a title-cased label.

    ``"getting-started"`` -> ``"Getting Started"``.
    """
    words = re.split(r"[-_\s]+", slug.strip())
    return " ".join(word.capitalize() for word in words if word) or slug


# --------------------------------------------------------------------------- #
# Content extraction
# --------------------------------------------------------------------------- #
def extract_html(html: str) -> Tuple[Optional[str], str, str]:
    """Return ``(title, description, plain_text_content)`` from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    title: Optional[str] = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title and soup.h1:
        title = soup.h1.get_text(strip=True)

    description = ""
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        description = meta["content"]
    if not description:
        paragraph = soup.find("p")
        if paragraph:
            description = paragraph.get_text(" ")

    for tag in soup(["script", "style"]):
        tag.decompose()
    content = soup.get_text("\n")
    content = "\n".join(line.strip() for line in content.splitlines() if line.strip())

    return title, _truncate(description), content


def extract_markdown(markdown: str) -> Tuple[Optional[str], str, str]:
    """Return ``(title, description, content)`` from Markdown text."""
    title: Optional[str] = None
    description = ""

    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if title is None and stripped.startswith("# "):
            title = stripped[2:].strip()
            continue
        if title is not None and not stripped.startswith("#"):
            # First prose paragraph after the H1 becomes the description.
            description = re.sub(r"[*_`]", "", stripped)
            break

    return title, _truncate(description), markdown


def _extract_file(path: Path) -> Optional[Tuple[Optional[str], str, str]]:
    """Extract from a supported file, or return ``None`` if unsupported."""
    ext = path.suffix.lower()
    if ext in HTML_EXTENSIONS:
        return extract_html(path.read_text(encoding="utf-8"))
    if ext in MARKDOWN_EXTENSIONS:
        return extract_markdown(path.read_text(encoding="utf-8"))
    return None


# --------------------------------------------------------------------------- #
# URL / section helpers
# --------------------------------------------------------------------------- #
def _make_url(base_url: str, relative: Path) -> str:
    """Join ``base_url`` with a POSIX-style relative path."""
    rel = relative.as_posix()
    if not base_url:
        return rel
    return f"{base_url.rstrip('/')}/{rel}"


def _section_for(relative: Path) -> str:
    """Derive a section title from the first path segment, if any."""
    parts = relative.parts
    if len(parts) > 1:
        return humanize(parts[0])
    return "Docs"


def _is_index(relative: Path) -> bool:
    """True when a top-level file looks like a homepage/index."""
    return relative.parent == Path(".") and relative.stem.lower() in INDEX_STEMS


# --------------------------------------------------------------------------- #
# Public loaders
# --------------------------------------------------------------------------- #
def load_from_directory(root: os.PathLike | str, base_url: str = "") -> List[Page]:
    """Load pages from every supported file under ``root`` (recursively).

    Files are returned sorted by path so output is deterministic.
    """
    root_path = Path(root)
    if not root_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {root_path}")

    pages: List[Page] = []
    for path in sorted(root_path.rglob("*")):
        if not path.is_file():
            continue
        extracted = _extract_file(path)
        if extracted is None:
            continue
        title, description, content = extracted
        relative = path.relative_to(root_path)
        if not title:
            title = humanize(path.stem)
        pages.append(
            Page(
                title=title,
                url=_make_url(base_url, relative),
                description=description,
                content=content,
                section=_section_for(relative),
                source_path=str(path),
                is_index=_is_index(relative),
            )
        )
    return pages


def _sitemap_locs(path: Path) -> List[str]:
    """Return all ``<loc>`` URLs from a sitemap.xml (namespace-agnostic)."""
    tree = ET.parse(path)
    return [
        element.text.strip()
        for element in tree.iter()
        if element.tag.endswith("loc") and element.text and element.text.strip()
    ]


def _page_from_url(url: str, base_dir: Optional[Path]) -> Page:
    """Build a :class:`Page` from a URL, extracting from a local file if found."""
    parsed = urlparse(url)
    path_part = parsed.path.rstrip("/")
    slug = path_part.split("/")[-1] or parsed.netloc
    stem = os.path.splitext(slug)[0]

    title = humanize(stem) if stem else parsed.netloc
    description = ""
    content = ""
    is_index = stem.lower() in INDEX_STEMS or path_part in ("", "/")

    if base_dir is not None and parsed.path:
        local = base_dir / parsed.path.lstrip("/")
        if local.is_file():
            extracted = _extract_file(local)
            if extracted is not None:
                extracted_title, description, content = extracted
                if extracted_title:
                    title = extracted_title

    trimmed = path_part.strip("/")
    section = humanize(trimmed.split("/")[0]) if "/" in trimmed else "Docs"

    return Page(
        title=title,
        url=url,
        description=description,
        content=content,
        section=section,
        source_path=url,
        is_index=is_index,
    )


def load_from_sitemap(
    path: os.PathLike | str, base_dir: Optional[os.PathLike | str] = None
) -> List[Page]:
    """Load pages from a ``sitemap.xml`` file.

    When ``base_dir`` is given, each ``<loc>`` path is resolved against it and,
    if the local file exists, its title/description/content are extracted.
    Otherwise a title is derived from the URL slug.
    """
    base = Path(base_dir) if base_dir is not None else None
    return [_page_from_url(loc, base) for loc in _sitemap_locs(Path(path))]


def load_from_urllist(
    path: os.PathLike | str, base_dir: Optional[os.PathLike | str] = None
) -> List[Page]:
    """Load pages from a plain-text file of one URL per line (``#`` comments)."""
    base = Path(base_dir) if base_dir is not None else None
    pages: List[Page] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        url = line.strip()
        if not url or url.startswith("#"):
            continue
        pages.append(_page_from_url(url, base))
    return pages


def load_pages(
    source: os.PathLike | str,
    source_type: str = "auto",
    base_url: str = "",
    base_dir: Optional[os.PathLike | str] = None,
) -> List[Page]:
    """Dispatch to the right loader based on ``source_type``.

    Args:
        source: A directory, a ``sitemap.xml`` file, or a URL-list file.
        source_type: ``"dir"``, ``"sitemap"``, ``"urllist"``, or ``"auto"``.
        base_url: Prefix applied to relative paths for directory sources.
        base_dir: Root used to resolve sitemap/URL-list entries to local files.
    """
    resolved = _resolve_source_type(source, source_type)
    if resolved == "dir":
        return load_from_directory(source, base_url=base_url)
    if resolved == "sitemap":
        return load_from_sitemap(source, base_dir=base_dir)
    if resolved == "urllist":
        return load_from_urllist(source, base_dir=base_dir)
    raise ValueError(f"Unknown source type: {source_type!r}")


def _resolve_source_type(source: os.PathLike | str, source_type: str) -> str:
    """Infer the source type from the path when ``source_type == 'auto'``."""
    if source_type != "auto":
        return source_type
    path = Path(source)
    if path.is_dir():
        return "dir"
    if path.suffix.lower() == ".xml":
        return "sitemap"
    return "urllist"
