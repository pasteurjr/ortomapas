"""Render one or more Markdown validation reports with local figures to PDF.

Usage: python scripts/gerar_pdf_relatorio_validacao.py path/to/report.md [...]
The PDF is written next to each Markdown source.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright


CSS = """<style>
@page { size: A4; margin: 14mm 13mm 16mm; }
body { font: 9pt/1.4 Arial, sans-serif; color: #1c2930 }
h1 { color: #0c5264; font-size: 20pt; line-height: 1.15 }
h2 { color: #17677b; border-bottom: 1px solid #b8cbd0; padding-bottom: 1mm; margin-top: 6mm; break-after: avoid }
h3 { color: #30556a; margin-top: 5mm; break-after: avoid }
p { orphans: 3; widows: 3 }
table { border-collapse: collapse; width: 100%; font-size: 7.5pt; margin: 3mm 0 }
th,td { border: 1px solid #bdcbd0; padding: 3px 4px; vertical-align: top; overflow-wrap: anywhere }
th { background: #e8f2f3; color: #164e63 }
tr { break-inside: avoid }
img { display: block; max-width: 100%; max-height: 150mm; object-fit: contain; margin: 3mm auto 5mm; break-inside: avoid }
li { margin-bottom: 1mm }
a { color: #12627b; overflow-wrap: anywhere }
code { overflow-wrap: anywhere }
</style>"""


def render(source: Path) -> Path:
    source = source.resolve()
    target = source.with_suffix(".pdf")
    html = source.with_name(f".{source.stem}.render.html")
    header = source.with_name(f".{source.stem}.style.html")
    header.write_text(CSS, encoding="utf-8")
    try:
        subprocess.run([
            shutil.which("pandoc") or "pandoc", str(source), "--from=gfm", "--standalone",
            "--metadata", f"pagetitle={source.stem.replace('_', ' ')}",
            f"--include-in-header={header}", "--output", str(html),
        ], check=True)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, executable_path=shutil.which("google-chrome"), args=["--no-sandbox"]
            )
            page = browser.new_page()
            page.goto(html.as_uri(), wait_until="load")
            page.pdf(path=str(target), format="A4", print_background=True,
                     margin={"top": "14mm", "right": "13mm", "bottom": "16mm", "left": "13mm"})
            browser.close()
    finally:
        html.unlink(missing_ok=True)
        header.unlink(missing_ok=True)
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()
    for report in args.reports:
        print(render(report))


if __name__ == "__main__":
    main()
