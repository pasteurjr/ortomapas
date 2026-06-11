"""
Report generation agent.

Gathers results from previous analyses, optionally uses the Anthropic API
for interpretive commentary, and produces a Markdown report.
"""

import json
import logging
import os
import time
from datetime import datetime

from backend.database.connection import execute_query
from backend.config import ANALISES_DIR

logger = logging.getLogger("agent.report")


class ReportAgent:
    """Generate a comprehensive Markdown report from analysis results."""

    def execute(self, task):
        """
        Parameters inside task['parametros'] (JSON):
            analise_ids – list of analise IDs to include
            projeto_id  – project ID (optional, derived from task if missing)
            language    – report language (default 'pt')
        """
        t0 = time.time()

        # --- 1. Parse params ---
        params = task.get("parametros")
        if isinstance(params, str):
            params = json.loads(params)
        params = params or {}

        analise_ids = params.get("analise_ids", [])
        projeto_id = params.get("projeto_id")
        language = params.get("language", "pt")

        if not analise_ids:
            raise ValueError("analise_ids list is required")

        # --- 2. Query analyses ---
        placeholders = ", ".join(["%s"] * len(analise_ids))
        analises = execute_query(
            f"SELECT * FROM analises WHERE id IN ({placeholders})",
            tuple(analise_ids),
        )
        if not analises:
            raise ValueError(f"No analyses found for ids: {analise_ids}")

        # --- 3. Query project info ---
        if projeto_id is None:
            projeto_id = analises[0].get("projeto_id")
        projeto = execute_query(
            "SELECT * FROM projetos WHERE id = %s", (projeto_id,), fetch_one=True
        )

        # --- 4. Build context ---
        context_parts = []
        context_parts.append("=== PROJECT INFO ===")
        if projeto:
            context_parts.append(f"Name: {projeto.get('nome', 'N/A')}")
            context_parts.append(f"Description: {projeto.get('descricao', 'N/A')}")
            context_parts.append(f"Area: {projeto.get('area_estudo', 'N/A')}")
            context_parts.append(f"Responsible: {projeto.get('responsavel', 'N/A')}")
            context_parts.append(f"Status: {projeto.get('status', 'N/A')}")
        else:
            context_parts.append(f"Project ID: {projeto_id} (details not found)")

        context_parts.append("\n=== ANALYSES ===")
        for an in analises:
            context_parts.append(f"\n--- Analysis ID {an['id']} ---")
            context_parts.append(f"Type: {an.get('tipo_analise', 'N/A')}")
            context_parts.append(f"Name: {an.get('nome', 'N/A')}")
            context_parts.append(f"Agent: {an.get('agente_ia', 'N/A')}")
            context_parts.append(f"Status: {an.get('status', 'N/A')}")
            context_parts.append(
                f"Processing time: {an.get('tempo_processamento_seg', 'N/A')}s"
            )
            resultado = an.get("resultado_json")
            if resultado:
                if isinstance(resultado, str):
                    try:
                        resultado = json.loads(resultado)
                    except json.JSONDecodeError:
                        pass
                context_parts.append(
                    f"Results: {json.dumps(resultado, indent=2, ensure_ascii=False, default=str)}"
                )

        context_str = "\n".join(context_parts)

        # --- 5. Try Anthropic API for interpretive report ---
        ai_report = None
        try:
            import anthropic

            client = anthropic.Anthropic()

            prompt = (
                "You are an expert remote sensing analyst. Based on the following "
                "analysis results from orthomosaic processing, generate a professional "
                "report in Portuguese (Brazil). Include sections: Resumo Executivo, "
                "Resultados das Analises, Observacoes, Recomendacoes. "
                "Be specific about numbers, areas, and percentages.\n\n"
                f"{context_str}"
            )

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            ai_report = message.content[0].text
            logger.info("AI report generated via Anthropic API")
        except ImportError:
            logger.info("anthropic SDK not available; using template report")
        except Exception as e:
            logger.warning("Anthropic API call failed: %s. Using template report.", e)

        # --- 6. Template-based fallback ---
        if ai_report is None:
            ai_report = self._generate_template_report(projeto, analises)

        # --- 7. Build final markdown ---
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        projeto_nome = projeto.get("nome", "N/A") if projeto else f"Projeto {projeto_id}"

        report_md = f"""# Relatorio de Analise - {projeto_nome}

**Data de geracao:** {now_str}
**Projeto:** {projeto_nome}
**Analises incluidas:** {', '.join(str(a['id']) for a in analises)}

---

{ai_report}

---

## Metadados

| Campo | Valor |
|-------|-------|
| Projeto ID | {projeto_id} |
| Total de analises | {len(analises)} |
| Data do relatorio | {now_str} |
| Gerado por | agente_relatorio |

"""

        # --- 8. Save as markdown ---
        os.makedirs(ANALISES_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"report_{projeto_id}_{ts}.md"
        report_path = os.path.join(ANALISES_DIR, report_filename)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)

        logger.info("Report saved: %s", report_path)

        elapsed = round(time.time() - t0, 2)

        # --- 9. Register in analises table ---
        result_json = {
            "report_path": report_path,
            "analise_ids": analise_ids,
            "projeto_id": projeto_id,
            "ai_generated": ai_report is not None,
            "sections": [
                "Resumo Executivo",
                "Resultados das Analises",
                "Observacoes",
                "Recomendacoes",
            ],
        }

        analise_id = execute_query(
            """
            INSERT INTO analises
                (ortomapa_id, projeto_id, tipo_analise, nome, descricao,
                 parametros, resultado_path, resultado_json,
                 agente_ia, status, tempo_processamento_seg)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                task["ortomapa_id"],
                projeto_id,
                "personalizada",
                f"Relatorio Projeto {projeto_nome}",
                f"Relatorio consolidado com {len(analises)} analises",
                json.dumps(params, ensure_ascii=False),
                report_path,
                json.dumps(result_json, ensure_ascii=False),
                "agente_relatorio",
                "concluido",
                elapsed,
            ),
            commit=True,
        )

        logger.info(
            "Report generation complete. analise_id=%s elapsed=%.1fs",
            analise_id,
            elapsed,
        )

        # --- 10. Return ---
        return {
            "analise_id": analise_id,
            "report_path": report_path,
            "elapsed_seconds": elapsed,
        }

    # ------------------------------------------------------------------
    # Template-based report (fallback when Anthropic is unavailable)
    # ------------------------------------------------------------------
    def _generate_template_report(self, projeto, analises):
        """Generate a structured report without AI assistance."""
        sections = []

        # --- Resumo ---
        sections.append("## Resumo Executivo\n")
        projeto_nome = projeto.get("nome", "N/A") if projeto else "N/A"
        sections.append(
            f"Este relatorio apresenta os resultados de {len(analises)} "
            f"analise(s) realizadas no ambito do projeto **{projeto_nome}**. "
            "As analises foram executadas por agentes autonomos de inteligencia "
            "artificial especializados em processamento de ortomapas.\n"
        )

        # --- Resultados ---
        sections.append("## Resultados das Analises\n")
        for an in analises:
            tipo = an.get("tipo_analise", "N/A")
            nome = an.get("nome", "N/A")
            status = an.get("status", "N/A")
            tempo = an.get("tempo_processamento_seg", "N/A")

            sections.append(f"### {nome} (ID: {an['id']})\n")
            sections.append(f"- **Tipo:** {tipo}")
            sections.append(f"- **Status:** {status}")
            sections.append(f"- **Tempo de processamento:** {tempo}s")

            resultado = an.get("resultado_json")
            if resultado:
                if isinstance(resultado, str):
                    try:
                        resultado = json.loads(resultado)
                    except json.JSONDecodeError:
                        resultado = None

            if isinstance(resultado, dict):
                # Vegetation analysis
                if "classes" in resultado and "index" in resultado:
                    sections.append(f"- **Indice utilizado:** {resultado.get('index')}")
                    sections.append(f"- **Media:** {resultado.get('mean')}")
                    sections.append(f"- **Desvio padrao:** {resultado.get('std')}")
                    classes = resultado.get("classes", {})
                    for cls_name, cls_data in classes.items():
                        sections.append(
                            f"  - {cls_name}: {cls_data.get('area_ha', 0)} ha "
                            f"({cls_data.get('pct', 0)}%)"
                        )

                # Detection analysis
                elif "total_detections" in resultado:
                    sections.append(
                        f"- **Total de deteccoes:** {resultado.get('total_detections')}"
                    )
                    cc = resultado.get("class_counts", {})
                    for cls_name, count in cc.items():
                        sections.append(f"  - {cls_name}: {count}")

                # Classification analysis
                elif "class_statistics" in resultado or "classes" in resultado:
                    cs = resultado.get("class_statistics") or resultado.get("classes", {})
                    sections.append(
                        f"- **Algoritmo:** {resultado.get('algorithm', 'N/A')}"
                    )
                    for cls_name, cls_data in cs.items():
                        sections.append(
                            f"  - {cls_name}: {cls_data.get('area_ha', 0)} ha "
                            f"({cls_data.get('pct', 0)}%)"
                        )

                # Change detection
                elif "area_changed_ha" in resultado:
                    sections.append(
                        f"- **Area alterada:** {resultado.get('area_changed_ha', 0)} ha "
                        f"({resultado.get('pct_changed', 0)}%)"
                    )
                    ccs = resultado.get("change_classes", {})
                    for cls_name, cls_data in ccs.items():
                        sections.append(
                            f"  - {cls_name}: {cls_data.get('area_ha', 0)} ha"
                        )

                else:
                    # Generic JSON dump for unrecognised structures
                    sections.append(
                        f"- **Resultado:** ```\n{json.dumps(resultado, indent=2, ensure_ascii=False, default=str)}\n```"
                    )

            sections.append("")  # blank line

        # --- Observacoes ---
        sections.append("## Observacoes\n")
        sections.append(
            "- Todas as analises foram executadas de forma automatizada por agentes de IA."
        )
        sections.append(
            "- Os resultados sao baseados em dados de sensoriamento remoto RGB "
            "e devem ser validados em campo quando necessario."
        )
        sections.append(
            "- As areas calculadas sao aproximadas e dependem da precisao do "
            "sistema de coordenadas do ortomapa.\n"
        )

        # --- Recomendacoes ---
        sections.append("## Recomendacoes\n")
        sections.append(
            "1. Validar resultados criticos com verificacao em campo."
        )
        sections.append(
            "2. Para analises de vegetacao, considerar complementar com dados "
            "de sensores multiespectrais (NIR) para calculo de NDVI."
        )
        sections.append(
            "3. Para deteccao de objetos, refinar o modelo com dados de treinamento "
            "especificos da regiao de estudo."
        )
        sections.append(
            "4. Realizar monitoramento temporal periodico para acompanhar "
            "a evolucao das mudancas identificadas."
        )

        return "\n".join(sections)
