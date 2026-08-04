"""Command-line interface for ``llms-txt-generator``.

Wires the :mod:`llmstxt.sources` loaders to the :mod:`llmstxt.generate`
renderers and writes ``llms.txt`` (and optionally ``llms-full.txt``) to disk.

Everything is offline: the tool only reads the local files you point it at.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from .generate import generate
from .sources import load_pages

SOURCE_TYPES = ["auto", "dir", "sitemap", "urllist"]


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=True, file_okay=True, path_type=Path),
)
@click.option(
    "-t",
    "--source-type",
    type=click.Choice(SOURCE_TYPES),
    default="auto",
    show_default=True,
    help="How to interpret SOURCE. 'auto' infers from the path.",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Directory to write llms.txt (and llms-full.txt) into.",
)
@click.option(
    "-b",
    "--base-url",
    default="",
    help="URL prefix applied to relative paths for directory sources.",
)
@click.option(
    "-d",
    "--base-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Root used to resolve sitemap/URL-list entries to local files.",
)
@click.option(
    "-n",
    "--name",
    default=None,
    help="Override the H1 site name (otherwise taken from the index page).",
)
@click.option(
    "-s",
    "--summary",
    default=None,
    help="Override the blockquote summary line.",
)
@click.option(
    "--full/--no-full",
    "write_full",
    default=True,
    show_default=True,
    help="Also write the concatenated llms-full.txt variant.",
)
def main(
    source: Path,
    source_type: str,
    output_dir: Path,
    base_url: str,
    base_dir: Optional[Path],
    name: Optional[str],
    summary: Optional[str],
    write_full: bool,
) -> None:
    """Generate an llms.txt file from SOURCE.

    SOURCE is a directory of .md/.html files, a sitemap.xml, or a text file
    listing one URL per line.
    """
    pages = load_pages(
        source,
        source_type=source_type,
        base_url=base_url,
        base_dir=base_dir,
    )
    if not pages:
        raise click.ClickException(f"No pages found in {source}")

    llms_txt, llms_full_txt = generate(pages, name=name, summary=summary)

    output_dir.mkdir(parents=True, exist_ok=True)
    llms_path = output_dir / "llms.txt"
    llms_path.write_text(llms_txt, encoding="utf-8")
    click.echo(f"Wrote {llms_path} ({len(pages)} pages)")

    if write_full:
        full_path = output_dir / "llms-full.txt"
        full_path.write_text(llms_full_txt, encoding="utf-8")
        click.echo(f"Wrote {full_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
