from pathlib import Path
import markdown
from weasyprint import HTML

root = Path(__file__).resolve().parents[1]
source = root / 'docs/analise/relatorio_visual_guarajuba.md'
target = root / 'docs/analise/relatorio_visual_guarajuba.pdf'
body = markdown.markdown(source.read_text(encoding='utf-8'), extensions=['tables'])
css = '''<style>@page{size:A4;margin:16mm}body{font:10pt Arial;color:#17242c}h1{color:#0b5563}h2{color:#155e75;border-bottom:1px solid #b8c8cf;padding-bottom:4px}h3{color:#334e68}img{max-width:100%;display:block;margin:8px 0}a{color:#0b7285}</style>'''
HTML(string=f'<html><head><meta charset="utf-8">{css}</head><body>{body}</body></html>', base_url=str(root)).write_pdf(target)
print(target)
