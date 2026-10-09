"""Gera o PDF da especificacao de planejamento de missoes Litchi."""

from pathlib import Path

import markdown
from weasyprint import HTML


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/analise/requisitos_planejamento_missoes_litchi.md"
TARGET = SOURCE.with_suffix(".pdf")

CSS = """
@page { size: A4; margin: 16mm 14mm 18mm 14mm;
  @bottom-right { content: "Ortomapas | " counter(page); font-size: 8pt; color: #64748b; }
}
body { font-family: Arial, sans-serif; font-size: 9.5pt; line-height: 1.38; color: #1e293b; }
h1 { color: #0f3d5e; font-size: 21pt; margin: 0 0 8pt; page-break-after: avoid; }
h2 { color: #0f3d5e; font-size: 15pt; margin: 18pt 0 7pt; page-break-after: avoid; border-bottom: 1px solid #cbd5e1; padding-bottom: 3pt; }
h3 { color: #155e75; font-size: 11.5pt; margin: 12pt 0 5pt; page-break-after: avoid; }
p { margin: 5pt 0; }
ul, ol { margin-top: 3pt; }
li { margin: 2pt 0; }
table { width: 100%; border-collapse: collapse; margin: 8pt 0 12pt; font-size: 8.4pt; page-break-inside: auto; }
thead { display: table-header-group; }
tr { page-break-inside: avoid; }
th { background: #e2e8f0; color: #0f172a; text-align: left; font-weight: bold; }
th, td { border: 0.5pt solid #cbd5e1; padding: 4pt 5pt; vertical-align: top; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 8.4pt; background: #f1f5f9; padding: 1pt 2pt; }
pre { background: #f1f5f9; border-left: 3pt solid #0f3d5e; padding: 7pt; white-space: pre-wrap; font-size: 8pt; }
blockquote { margin: 8pt 0; padding: 5pt 9pt; border-left: 3pt solid #94a3b8; background: #f8fafc; }
a { color: #075985; }
"""


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    body = markdown.markdown(
        source,
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html5",
    )
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
    HTML(string=html, base_url=str(ROOT)).write_pdf(TARGET)
    print(f"PDF gerado: {TARGET} ({TARGET.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
