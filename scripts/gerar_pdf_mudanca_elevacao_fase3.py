from pathlib import Path

import markdown
from weasyprint import HTML

root = Path(__file__).resolve().parents[1]
source = root / 'docs/validacao/mudanca_elevacao_fase3_2026-10-13.md'
target = source.with_suffix('.pdf')
body = markdown.markdown(source.read_text(encoding='utf-8'), extensions=['tables', 'fenced_code', 'sane_lists'])
css = '''<style>
@page { size:A4; margin:15mm 14mm 16mm; @bottom-right { content:"Pagina " counter(page) " de " counter(pages); font:8pt Arial; color:#64748b } }
body { font:9.5pt/1.42 Arial, sans-serif; color:#17242c }
h1 { color:#0b5563; font-size:20pt; margin:0 0 10mm } h2 { color:#155e75; border-bottom:1px solid #b8c8cf; padding-bottom:3px; margin-top:8mm }
h3 { color:#334e68 } p { text-align:justify } img { max-width:100%; max-height:160mm; display:block; margin:5mm auto 2mm; page-break-inside:avoid }
table { width:100%; border-collapse:collapse; margin:4mm 0; font-size:8.5pt; page-break-inside:avoid } th,td { border:1px solid #bcc9cf; padding:4px 6px } th { background:#e7f2f3; color:#164e63 }
code { background:#edf2f4; padding:1px 3px } ul { padding-left:5mm } a { color:#0b7285 }
</style>'''
HTML(string=f'<html><head><meta charset="utf-8">{css}</head><body>{body}</body></html>', base_url=str(source.parent)).write_pdf(target)
print(target)
