"""Render the Phase 8 Markdown report and its local screenshots to PDF."""
from pathlib import Path
import shutil
import subprocess
import tempfile
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/validacao/ortomapas_conclusao/etapa-08/relatorio.md"
TARGET = SOURCE.with_suffix(".pdf")
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
</style>"""

with tempfile.TemporaryDirectory(prefix="ortomapas-f8-pdf-") as temp:
    temp = Path(temp)
    html = SOURCE.with_name(".relatorio-fase8-render.html")
    header = temp / "style.html"
    header.write_text(CSS, encoding="utf-8")
    subprocess.run([
        shutil.which("pandoc") or "pandoc", str(SOURCE), "--from=gfm", "--standalone",
        "--metadata", "pagetitle=Relatório de validação da Fase 8 — Ortomapas", f"--include-in-header={header}", "--output", str(html),
    ], check=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, executable_path=shutil.which("google-chrome"), args=["--no-sandbox"]
        )
        page = browser.new_page()
        page.goto(html.as_uri(), wait_until="load")
        page.pdf(path=str(TARGET), format="A4", print_background=True,
                 margin={"top": "14mm", "right": "13mm", "bottom": "16mm", "left": "13mm"})
        browser.close()
    html.unlink(missing_ok=True)
print(TARGET)
