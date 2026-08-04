"""Tests for loading and extracting pages from the example site."""

from __future__ import annotations

from llmstxt.sources import (
    extract_html,
    extract_markdown,
    humanize,
    load_from_directory,
    load_from_sitemap,
    load_pages,
)


def test_humanize_slug():
    assert humanize("getting-started") == "Getting Started"
    assert humanize("api_overview") == "Api Overview"


def test_extract_html_title_description():
    html = (
        "<html><head><title>Hello</title>"
        '<meta name="description" content="A short summary."></head>'
        "<body><h1>Hi</h1><p>Body text.</p></body></html>"
    )
    title, description, content = extract_html(html)
    assert title == "Hello"
    assert description == "A short summary."
    assert "Body text." in content


def test_extract_markdown_title_description():
    md = "# My Page\n\nThe first paragraph is the description.\n\n## Section\n"
    title, description, content = extract_markdown(md)
    assert title == "My Page"
    assert description == "The first paragraph is the description."
    assert content == md


def test_load_from_directory_finds_all_pages(example_site, base_url):
    pages = load_from_directory(example_site, base_url=base_url)
    urls = {page.url for page in pages}
    assert f"{base_url}/index.html" in urls
    assert f"{base_url}/guides/getting-started.html" in urls
    assert f"{base_url}/api/notebooks.md" in urls
    assert len(pages) == 5


def test_index_page_is_flagged(example_site, base_url):
    pages = load_from_directory(example_site, base_url=base_url)
    index = next(page for page in pages if page.is_index)
    assert index.title == "Nimbus Notes"
    assert index.section == "Docs"


def test_sections_derived_from_directories(example_site, base_url):
    pages = load_from_directory(example_site, base_url=base_url)
    sections = {page.section for page in pages if not page.is_index}
    assert sections == {"Api", "Guides"}


def test_load_from_sitemap_resolves_local_files(example_sitemap, example_site):
    pages = load_from_sitemap(example_sitemap, base_dir=example_site)
    titles = {page.title for page in pages}
    assert "Getting Started" in titles
    assert "Notebooks API" in titles
    assert len(pages) == 5


def test_load_pages_auto_detects_directory(example_site, base_url):
    pages = load_pages(example_site, base_url=base_url)
    assert len(pages) == 5
