"""Tests asserting the generated llms.txt conforms to the expected structure."""

from __future__ import annotations

from llmstxt.generate import generate
from llmstxt.models import Page
from llmstxt.sources import load_from_directory


def test_generated_llms_txt_has_h1_and_summary(example_site, base_url):
    pages = load_from_directory(example_site, base_url=base_url)
    llms_txt, _ = generate(pages)

    lines = llms_txt.splitlines()
    assert lines[0] == "# Nimbus Notes"
    assert any(line.startswith("> ") for line in lines), "expected a blockquote summary"


def test_generated_llms_txt_has_sections(example_site, base_url):
    pages = load_from_directory(example_site, base_url=base_url)
    llms_txt, _ = generate(pages)

    assert "## Guides" in llms_txt
    assert "## Api" in llms_txt


def test_generated_llms_txt_has_correct_link_lines(example_site, base_url):
    pages = load_from_directory(example_site, base_url=base_url)
    llms_txt, _ = generate(pages)

    expected = (
        f"- [Getting Started]({base_url}/guides/getting-started.html): "
        "Install Nimbus Notes and create your first notebook in under two minutes."
    )
    assert expected in llms_txt
    assert (
        f"- [API Overview]({base_url}/api/overview.html): "
        "The Nimbus Notes HTTP API lets you read, write, and search notebooks "
        "programmatically." in llms_txt
    )


def test_index_is_not_listed_as_a_link(example_site, base_url):
    pages = load_from_directory(example_site, base_url=base_url)
    llms_txt, _ = generate(pages)
    assert f"- [Nimbus Notes]({base_url}/index.html)" not in llms_txt


def test_llms_full_txt_contains_page_content(example_site, base_url):
    pages = load_from_directory(example_site, base_url=base_url)
    _, llms_full_txt = generate(pages)
    assert "Source: " in llms_full_txt
    assert "Create, list, and delete notebooks" in llms_full_txt


def test_render_is_deterministic():
    pages = [
        Page(title="Beta", url="/b", description="second", section="Docs"),
        Page(title="Alpha", url="/a", description="first", section="Docs"),
    ]
    out_a, _ = generate(pages, name="X")
    out_b, _ = generate(pages, name="X")
    assert out_a == out_b
    # Alpha sorts before Beta within the section.
    assert out_a.index("Alpha") < out_a.index("Beta")


def test_ends_with_single_trailing_newline(example_site, base_url):
    pages = load_from_directory(example_site, base_url=base_url)
    llms_txt, _ = generate(pages)
    assert llms_txt.endswith("\n")
    assert not llms_txt.endswith("\n\n")
