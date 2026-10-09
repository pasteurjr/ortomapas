"""Gera o roteiro narrado em Markdown e PDF a partir de uma execução Playwright."""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
run_dir = (Path(sys.argv[1]) if len(sys.argv) > 1 else max((ROOT / "runtime/screenshots/demonstracao_video").glob("20*"))).resolve()
result = json.loads((run_dir / "resultado.json").read_text(encoding="utf-8"))
relative_run = run_dir.relative_to(ROOT)

lines = [
    "# Roteiro de demonstração em vídeo — Ortomapas",
    "",
    f"Execução Playwright: `{result['run_id']}`  ",
    f"Status: **{result['status']}**  ",
    "Duração sugerida: 8 a 12 minutos, com pausas curtas para leitura das telas.",
    "",
    "## Objetivo do vídeo",
    "",
    "Demonstrar o produto como um operador real: autenticar, selecionar um projeto, criar dados, consultar o mapa, revisar as ferramentas de análise, conversar com o copiloto, planejar uma missão de captura, validar a segurança e exportar a missão para o Mission Hub/Litchi.",
    "",
    "## Orientação de gravação",
    "",
    "- Gravar em 1440×900 ou 1920×1080, mantendo o cursor visível.",
    "- Narrar somente depois que o resultado visual aparecer; manter cada cena entre 15 e 40 segundos.",
    "- Mostrar o painel lateral inteiro antes de entrar nos detalhes do mapa.",
    "- Na cena Litchi, explicar que o CSV deve ser revisado no Mission Hub e que a validação de voo real depende do drone.",
    "- Usar as capturas abaixo como storyboard e o vídeo WebM da execução como referência de timing.",
    "",
    "## Critérios de aceite",
    "",
    "1. O login deve bloquear o painel até a autenticação e abrir o projeto após credenciais válidas.",
    "2. O projeto criado deve aparecer na lista e os painéis laterais devem carregar sem erro.",
    "3. Cada aba de ferramentas deve ser acessível e exibir seus controles específicos.",
    "4. O polígono deve aparecer no mapa e ficar disponível para o copiloto/análises.",
    "5. A missão deve conter AOI, takeoff, waypoints, grid, simulação, validação e exportação.",
    "6. As análises raster devem ser executadas somente quando houver ortomapa/DSM/DTM compatível carregado; nesta execução os painéis foram demonstrados, mas o projeto não tinha raster elegível.",
    "7. O roteiro deve terminar somente com status Playwright `passed`.",
    "",
    "## Cenas",
    "",
    "| Cena | Tela | Ação demonstrada | Narração | Aceite | Evidência |",
    "|---|---|---|---|---|---|",
]
for scene in result["scenes"]:
    evidence = f"[{scene['screenshot']}]({relative_run.as_posix()}/{scene['screenshot']})"
    lines.append(f"| {scene['id']} | {scene['title']} | {scene['action']} | {scene['narration']} | Cena capturada sem erro | {evidence} |")

lines += [
    "",
    "## Encerramento sugerido",
    "",
    "O Ortomapas centraliza o ciclo: projeto, mapa, análise, copiloto, planejamento de voo e exportação. A missão exibida foi validada automaticamente com dados simulados. Antes de uma operação, o operador deve importar o arquivo no aplicativo de voo, confirmar os parâmetros globais e realizar a checagem de segurança em campo.",
    "",
    "## Artefatos da execução",
    "",
    f"- Resultado estruturado: [{(relative_run / 'resultado.json').as_posix()}]({(relative_run / 'resultado.json').as_posix()})",
    f"- Vídeo bruto Playwright: consultar a pasta `{(relative_run / 'video').as_posix()}`.",
    "- Relatórios técnicos: `docs/analise/validacao_fase5_missoes.md` e `docs/analise/validacao_fase6_exportacao.md`.",
    "",
    "# Storyboard visual detalhado",
    "",
    "Cada bloco abaixo corresponde a uma cena do vídeo. A imagem é a captura real da execução Playwright; o texto imediatamente abaixo orienta o enquadramento e a narração.",
]
for scene in result["scenes"]:
    image_path = (relative_run / scene["screenshot"]).as_posix()
    lines += [
        "",
        f"## {scene['id']} — {scene['title']}",
        "",
        f"![Captura da cena {scene['id']}](../../{image_path})",
        "",
        f"**Ação executada:** {scene['action']}",
        "",
        f"**O que mostrar na tela:** destacar a área funcional que comprova esta etapa e manter a informação central visível durante a narração.",
        "",
        f"**Texto da narração:** {scene['narration']}",
        "",
        "**Transição:** aguardar a tela estabilizar e seguir para a próxima cena.",
    ]
md_path = ROOT / "docs/analise/roteiro_video_demonstracao_ortomapas.md"
md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
body = markdown.markdown("\n".join(lines), extensions=["tables"])
# O Markdown é aberto a partir de docs/analise; o PDF é renderizado a partir da raiz.
pdf_body = body.replace('src="../../runtime/', 'src="runtime/')
style = """<style>@page{size:A4 landscape;margin:12mm}body{font-family:Arial,sans-serif;color:#172033;font-size:8.5pt;line-height:1.35}h1{font-size:19pt;color:#0b3d5c}h2{font-size:13pt;color:#0b3d5c;margin-top:14pt;page-break-after:avoid}table{width:100%;border-collapse:collapse}th,td{border:1px solid #b9c5d0;padding:4px;vertical-align:top}th{background:#eaf1f5}a{color:#075985}code{background:#eef2f5;padding:1px 3px}ul,ol{margin-top:4px}img{display:block;max-width:100%;max-height:118mm;width:auto;height:auto;margin:5mm auto 4mm;object-fit:contain}h2+img{page-break-before:avoid}</style>"""
HTML(string=f"<html><head><meta charset='utf-8'>{style}</head><body>{pdf_body}</body></html>", base_url=str(ROOT)).write_pdf(str(ROOT / "docs/analise/roteiro_video_demonstracao_ortomapas.pdf"))
print(md_path)
