"""llms-txt-generator: build an ``llms.txt`` file from a set of pages.

The public surface is intentionally small so the package can be used either
through the ``llms-txt-generator`` console script or as a library::

    from llmstxt.sources import load_pages
    from llmstxt.generate import generate

    pages = load_pages("examples/site", source_type="dir", base_url="https://example.com")
    llms_txt, llms_full_txt = generate(pages, name="Nimbus Notes")
"""

from .models import Document, Page, Section

__all__ = ["Document", "Page", "Section", "__version__"]

__version__ = "0.1.0"
