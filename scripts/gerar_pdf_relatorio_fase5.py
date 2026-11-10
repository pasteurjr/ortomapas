"""Render the incremental Phase 5 validation report and screenshots."""
from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/validacao/ortomapas_conclusao/etapa-05/relatorio.md"
TARGET = SOURCE.with_suffix(".pdf")
body = markdown.markdown(
    SOURCE.read_text(encoding="utf-8"),
    extensions=["tables", "fenced_code", "sane_lists"],
)
for heading in (
    "02 — Modelo texturizado GLB", "03 — DSM como superfície",
    "04 — DTM como terreno", "05 — Nuvem de pontos LAZ",
):
    body = body.replace(f"<h3>{heading}</h3>", f'<div class="evidence-page-break"></div><h3>{heading}</h3>')
css = """<style>
@page { size: A4; margin: 14mm 13mm 16mm; @bottom-right { content: "Página " counter(page) " de " counter(pages); font: 8pt Arial; color: #60717a } }
body { font: 8.7pt/1.35 Arial, sans-serif; color: #1c2930 }
h1 { color: #0c5264; font-size: 20pt; line-height: 1.15; margin: 0 0 5mm }
h2 { color: #17677b; border-bottom: 1px solid #b8cbd0; padding-bottom: 1mm; margin-top: 6mm; page-break-after: avoid }
h3 { color: #30556a; margin-top: 5mm; page-break-after: avoid }
p { text-align: left; orphans: 3; widows: 3 }
table { border-collapse: collapse; width: 100%; font-size: 7.2pt; margin: 3mm 0; page-break-inside: auto }
tr { page-break-inside: avoid }
th, td { border: 1px solid #bdcbd0; padding: 3px 4px; vertical-align: top; overflow-wrap: anywhere }
th { background: #e8f2f3; color: #164e63 }
ul, ol { padding-left: 6mm } li { margin-bottom: 1mm }
a { color: #12627b; overflow-wrap: anywhere }
strong { color: #193e4c }
img { display: block; width: 100%; max-height: 155mm; object-fit: contain; margin: 3mm auto 5mm; page-break-inside: avoid }
img + p { page-break-before: avoid }
.evidence-page-break { page-break-before: always; height: 0 }
pre { white-space: pre-wrap; font-size: 8pt }
</style>"""
HTML(
    string=f'<html><head><meta charset="utf-8">{css}</head><body>{body}</body></html>',
    base_url=str(SOURCE.parent),
).write_pdf(TARGET)
print(TARGET)
