"""End-to-end tests for the Click CLI entrypoint."""

from __future__ import annotations

from click.testing import CliRunner

from llmstxt.cli import main


def test_cli_writes_llms_txt_files(tmp_path, example_site, base_url):
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            str(example_site),
            "--source-type",
            "dir",
            "--base-url",
            base_url,
            "--output",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    llms_txt = (tmp_path / "llms.txt").read_text(encoding="utf-8")
    llms_full = (tmp_path / "llms-full.txt").read_text(encoding="utf-8")

    assert llms_txt.startswith("# Nimbus Notes")
    assert "## Guides" in llms_txt
    assert f"- [Getting Started]({base_url}/guides/getting-started.html):" in llms_txt
    assert "Source: " in llms_full


def test_cli_no_full_skips_full_file(tmp_path, example_site, base_url):
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(example_site), "--base-url", base_url, "--output", str(tmp_path), "--no-full"],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "llms.txt").exists()
    assert not (tmp_path / "llms-full.txt").exists()
