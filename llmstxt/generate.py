"""Assemble and render ``llms.txt`` and ``llms-full.txt`` documents.

The ``llms.txt`` structure produced here follows the emerging convention:

    # Site name
    > Short blockquote summary
    Optional prose.
    ## Section
    - [Title](url): description

``llms-full.txt`` is the fuller variant: the same header followed by the full
plain-text content of every page concatenated with source markers.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .models import Document, Page, Section


def assemble(
    pages: List[Page],
    name: Optional[str] = None,
    summary: Optional[str] = None,
    prose: str = "",
) -> Document:
    """Group pages into an ordered :class:`Document`.

    The index page (if any) supplies the default ``name`` and ``summary`` and is
    excluded from the section link lists. Remaining pages are grouped by their
    ``section`` and both sections and pages are sorted for deterministic output.
    """
    index = next((page for page in pages if page.is_index), None)

    if name is None:
        name = index.title if index else "Site"
    if summary is None:
        summary = index.description if index else ""

    body = [page for page in pages if not page.is_index]

    grouped: dict[str, List[Page]] = {}
    for page in body:
        grouped.setdefault(page.section, []).append(page)

    sections = [
        Section(
            title=section_title,
            pages=sorted(grouped[section_title], key=lambda page: page.title.lower()),
        )
        for section_title in sorted(grouped)
    ]

    return Document(name=name, summary=summary, prose=prose, sections=sections)


def _escape_link_text(text: str) -> str:
    """Escape characters that would break a Markdown link label.

    Backslashes are escaped first, then the brackets that delimit ``[label]`` --
    an unescaped ``]`` truncates the link text, producing invalid Markdown.
    Newlines are collapsed so the list item stays on a single line.
    """
    text = text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
    return " ".join(text.split())


def _single_line(text: str) -> str:
    """Collapse whitespace so a note stays part of its ``- [..](..):`` item."""
    return " ".join(text.split())


def _link_line(page: Page) -> str:
    """Render a single Markdown list item for a page link."""
    title = _escape_link_text(page.title)
    if page.description:
        return f"- [{title}]({page.url}): {_single_line(page.description)}"
    return f"- [{title}]({page.url})"


def render_llms_txt(document: Document) -> str:
    """Render a :class:`Document` as ``llms.txt`` text."""
    lines: List[str] = [f"# {document.name}", ""]

    if document.summary:
        lines += [f"> {document.summary}", ""]
    if document.prose:
        lines += [document.prose.strip(), ""]

    for section in document.sections:
        lines.append(f"## {section.title}")
        lines.append("")
        for page in section.pages:
            lines.append(_link_line(page))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_llms_full_txt(document: Document, pages: List[Page]) -> str:
    """Render the fuller ``llms-full.txt`` with concatenated page content."""
    lines: List[str] = [f"# {document.name}", ""]
    if document.summary:
        lines += [f"> {document.summary}", ""]

    for page in pages:
        lines.append(f"## {page.title}")
        lines.append(f"Source: {page.url}")
        lines.append("")
        if page.content.strip():
            lines.append(page.content.strip())
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def generate(
    pages: List[Page],
    name: Optional[str] = None,
    summary: Optional[str] = None,
    prose: str = "",
) -> Tuple[str, str]:
    """Convenience wrapper returning ``(llms_txt, llms_full_txt)`` strings."""
    document = assemble(pages, name=name, summary=summary, prose=prose)
    return render_llms_txt(document), render_llms_full_txt(document, pages)
