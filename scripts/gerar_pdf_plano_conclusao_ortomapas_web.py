from pathlib import Path

import markdown
from weasyprint import HTML


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/analise/plano_conclusao_ortomapas_web.md"
TARGET = SOURCE.with_suffix(".pdf")

content = markdown.markdown(
    SOURCE.read_text(encoding="utf-8"),
    extensions=["tables", "fenced_code", "sane_lists"],
)
css = """<style>
@page { size: A4; margin: 15mm 14mm 17mm; @bottom-right { content: "Página " counter(page) " de " counter(pages); font: 8pt Arial; color: #60717a } }
body { font: 9pt/1.38 Arial, sans-serif; color: #1c2930 }
h1 { color: #0c5264; font-size: 21pt; line-height: 1.2; margin: 0 0 6mm }
h2 { color: #17677b; border-bottom: 1px solid #b8cbd0; padding-bottom: 1mm; margin-top: 7mm; page-break-after: avoid }
h3 { color: #30556a; margin-top: 5mm; page-break-after: avoid }
p { text-align: left; orphans: 3; widows: 3 }
table { border-collapse: collapse; width: 100%; font-size: 8pt; margin: 4mm 0; page-break-inside: auto }
tr { page-break-inside: avoid }
th, td { border: 1px solid #bdcbd0; padding: 4px 5px; vertical-align: top; overflow-wrap: anywhere }
th { background: #e8f2f3; color: #164e63 }
ul, ol { padding-left: 6mm }
li { margin-bottom: 1.2mm }
a { color: #12627b; overflow-wrap: anywhere }
strong { color: #193e4c }
</style>"""

HTML(
    string=f'<html><head><meta charset="utf-8">{css}</head><body>{content}</body></html>',
    base_url=str(SOURCE.parent),
).write_pdf(TARGET)
print(TARGET)
