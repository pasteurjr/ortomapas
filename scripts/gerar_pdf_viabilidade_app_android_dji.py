from pathlib import Path

import markdown
from weasyprint import HTML


root = Path(__file__).resolve().parents[1]
source = root / 'docs/analise/viabilidade_app_android_dji_analise_tempo_real_2026-10-15.md'
target = source.with_suffix('.pdf')
body = markdown.markdown(source.read_text(encoding='utf-8'), extensions=['tables', 'fenced_code', 'sane_lists'])
css = '''<style>
@page { size:A4; margin:11mm 13mm 13mm; @bottom-right { content:"Pagina " counter(page) " de " counter(pages); font:8pt Arial; color:#60717a } }
body { font:8.8pt/1.31 Arial,sans-serif; color:#1c2930 }
h1 { color:#0c5264; font-size:19pt; line-height:1.2; margin:0 0 7mm }
h2 { color:#17677b; border-bottom:1px solid #b8cbd0; padding-bottom:1mm; margin-top:4mm }
h2:last-of-type { break-before:page }
h3 { color:#30556a; margin-top:3mm } p { text-align:justify }
table { border-collapse:collapse; width:100%; font-size:8pt; margin:4mm 0 }
tr { page-break-inside:avoid }
th,td { border:1px solid #bdcbd0; padding:4px 5px; vertical-align:top; overflow-wrap:anywhere }
th { background:#e8f2f3; color:#164e63 } pre { white-space:pre-wrap; font-size:7.5pt; background:#edf3f3; padding:3mm; page-break-inside:avoid }
code { overflow-wrap:anywhere; background:#edf3f3 } a { color:#12627b; overflow-wrap:anywhere }
ul,ol { padding-left:6mm } li { margin-bottom:1.3mm }
</style>'''
HTML(string=f'<html><head><meta charset="utf-8">{css}</head><body>{body}</body></html>', base_url=str(source.parent)).write_pdf(target)
print(target)
