"""Render the Ortomapas completion plan from Markdown using Pandoc and Chrome."""
from pathlib import Path
import shutil
import subprocess
import tempfile
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/analise/plano_conclusao_ortomapas_web.md"
TARGET = SOURCE.with_suffix(".pdf")
CSS = """<style>
@page { size: A4; margin: 15mm 14mm 17mm; }
body { font: 9pt/1.38 Arial,sans-serif; color:#1c2930 }
h1 { color:#0c5264; font-size:21pt; line-height:1.2 }
h2 { color:#17677b; border-bottom:1px solid #b8cbd0; padding-bottom:1mm; margin-top:7mm; break-after:avoid }
h3 { color:#30556a; margin-top:5mm; break-after:avoid }
table { border-collapse:collapse; width:100%; font-size:7.5pt; margin:3mm 0 }
th,td { border:1px solid #bdcbd0; padding:3px 4px; vertical-align:top; overflow-wrap:anywhere }
th { background:#e8f2f3; color:#164e63 }
tr { break-inside:avoid }
li { margin-bottom:1mm }
a { color:#12627b; overflow-wrap:anywhere }
</style>"""
with tempfile.TemporaryDirectory(prefix="ortomapas-plan-pdf-") as temp:
    temp = Path(temp)
    html = SOURCE.with_name(".plano-ortomapas-render.html")
    header = temp / "style.html"
    header.write_text(CSS, encoding="utf-8")
    subprocess.run([
        shutil.which("pandoc") or "pandoc", str(SOURCE), "--from=gfm", "--standalone",
        "--metadata", "pagetitle=Plano de conclusão do Ortomapas Web", f"--include-in-header={header}", "--output", str(html),
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
