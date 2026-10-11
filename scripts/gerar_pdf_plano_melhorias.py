"""Render the improvement plan with its reviewed screenshot evidence."""

from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/analise/plano_melhorias_funcionalidades_ui_2026-10-10.md"
TARGET = SOURCE.with_suffix(".pdf")

CSS = """
@page {
  size: A4;
  margin: 16mm 14mm 19mm;
  @bottom-left { content: 'Ortomapas | Plano de melhorias | 10/10/2026'; font-size: 8pt; color: #58656a; }
  @bottom-right { content: counter(page) ' / ' counter(pages); font-size: 8pt; color: #58656a; }
}
body { font-family: 'DejaVu Sans', sans-serif; font-size: 9.2pt; line-height: 1.45; color: #202b30; }
h1 { font-size: 22pt; line-height: 1.2; color: #155d50; margin: 0 0 12pt; }
h2 { font-size: 14pt; color: #155d50; margin: 18pt 0 8pt; padding-bottom: 4pt; border-bottom: 1pt solid #b9cec7; }
h3 { font-size: 11pt; color: #225f72; margin: 12pt 0 6pt; }
h1,h2,h3 { break-after: avoid; }
p { margin: 5pt 0; orphans: 3; widows: 3; }
ul,ol { padding-left: 17pt; margin: 6pt 0; }
li { margin: 3pt 0; }
table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 7.5pt; line-height: 1.35; margin: 8pt 0 12pt; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
th,td { border: .5pt solid #c7d3d1; padding: 5pt; vertical-align: top; overflow-wrap: anywhere; }
th { background: #e8f1ed; text-align: left; color: #174b40; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 7.5pt; overflow-wrap: anywhere; }
img { display: block; width: 100%; height: auto; margin: 8pt 0; border: .5pt solid #b9c6c8; }
a { color: #216978; text-decoration: none; }
strong { color: #172c33; }
"""


def main() -> None:
    body = markdown.markdown(
        SOURCE.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html5",
    )
    document = (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<title>Ortomapas: revisao tecnica e plano de melhorias</title>'
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )
    HTML(string=document, base_url=str(SOURCE.parent)).write_pdf(TARGET)
    print(f"PDF gerado: {TARGET} ({TARGET.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
