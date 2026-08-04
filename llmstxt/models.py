"""Dataclasses describing the pieces of an ``llms.txt`` document.

These types are deliberately plain data holders: ``sources`` populates them and
``generate`` renders them. Keeping them free of behaviour makes the data flow
easy to follow and easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Page:
    """A single page discovered from a directory, sitemap, or URL list.

    Attributes:
        title: Human-readable page title used as the link text.
        url: The absolute or relative URL that the link points to.
        description: One-line summary shown after the link (may be empty).
        content: Full plain-text body, used only for ``llms-full.txt``.
        section: The H2 section this page belongs to (e.g. ``"Guides"``).
        source_path: Where the page was loaded from, for diagnostics.
        is_index: True when the page is the site homepage/index. The index
            supplies the document H1 name and blockquote summary rather than
            appearing as a link in a section.
    """

    title: str
    url: str
    description: str = ""
    content: str = ""
    section: str = "Docs"
    source_path: Optional[str] = None
    is_index: bool = False


@dataclass
class Section:
    """An H2 section: a titled group of :class:`Page` links."""

    title: str
    pages: List[Page] = field(default_factory=list)


@dataclass
class Document:
    """The assembled, render-ready ``llms.txt`` document.

    Attributes:
        name: The H1 site/project name.
        summary: Optional blockquote short summary.
        prose: Optional free-form Markdown that appears before the sections.
        sections: Ordered H2 sections, each holding a list of links.
    """

    name: str
    summary: str = ""
    prose: str = ""
    sections: List[Section] = field(default_factory=list)
