"""Render the phase-one report, including actual screenshots and comparison data."""

from pathlib import Path
import sys

import markdown
from weasyprint import HTML

from gerar_pdf_plano_melhorias import CSS

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "docs/validacao/relatorio_correcao_mapa_fase1_2026-10-10.md"


def main():
    body = markdown.markdown(SOURCE.read_text(encoding="utf-8"), extensions=["tables", "fenced_code", "sane_lists", "toc"])
    css = CSS.replace("Plano de melhorias", "Validacao mapa 2D")
    if "revisao_fase1_inicio_fase2" in SOURCE.stem:
        css = css.replace("Validacao mapa 2D", "Revisao fases 1 e 2")
    elif "medidas_espaciais_fase2" in SOURCE.stem:
        css = css.replace("Validacao mapa 2D", "Fase 2 - medidas espaciais")
    elif "usabilidade_gis_fase2" in SOURCE.stem:
        css = css.replace("Validacao mapa 2D", "Fase 2 - usabilidade GIS")
        css = css.replace("10/10/2026", "11/10/2026")
    elif "derivadas_terreno_fase2" in SOURCE.stem:
        css = css.replace("Validacao mapa 2D", "Fase 2 - derivadas de terreno")
        css = css.replace("10/10/2026", "11/10/2026")
    elif "publicacao_terreno_fase3" in SOURCE.stem:
        css = css.replace("Validacao mapa 2D", "Fase 3 - mapas de terreno")
        css = css.replace("10/10/2026", "11/10/2026")
    elif "aoi_terreno_fase3" in SOURCE.stem:
        css = css.replace("Validacao mapa 2D", "Fase 3 - analise por area")
        css = css.replace("10/10/2026", "11/10/2026")
    elif "curvas_nivel_fase3" in SOURCE.stem:
        css = css.replace("Validacao mapa 2D", "Fase 3 - curvas de nivel")
        css = css.replace("10/10/2026", "11/10/2026")
    elif "volume_aoi_fase3" in SOURCE.stem:
        css = css.replace("Validacao mapa 2D", "Fase 3 - volume por area")
        css = css.replace("10/10/2026", "12/10/2026")
    # Diagnostic tiles remain readable without being enlarged to a whole page.
    css += "img[src*='tile_'] { width: 66mm; height: 66mm; margin-inline: auto; }"
    css += "pre { white-space: pre-wrap; overflow-wrap: anywhere; } h3[id^='cena-'] { break-before: page; }"
    html = f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Ortomapas: validacao funcional</title><style>{css}</style></head><body>{body}</body></html>'
    target = SOURCE.with_suffix(".pdf")
    HTML(string=html, base_url=str(SOURCE.parent)).write_pdf(target)
    print(f"PDF gerado: {target} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
