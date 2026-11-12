"""
Task queue orchestrator. Polls tarefas_agentes table and dispatches to agents.
Can run as standalone process: python -m backend.agents.orchestrator
"""
import time
import json
import logging
import traceback
from datetime import datetime
import sys
import os
from threading import Event

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.connection import get_connection, execute_query
from backend.agents.vegetation_agent import VegetationAgent
from backend.agents.detection_agent import DetectionAgent
from backend.agents.classification_agent import ClassificationAgent
from backend.agents.change_agent import ChangeAgent
from backend.agents.report_agent import ReportAgent
from backend.agents.classification_queue_agent import QueuedClassificationAgent
from backend.agents.raster_queue_agent import QueuedRasterAnalysisAgent
from backend.agents.terrain_queue_agent import QueuedTerrainAnalysisAgent
from backend.agents.hydrology_queue_agent import QueuedHydrologyAnalysisAgent
from psycopg2.extras import Json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("orchestrator")

AGENTS = {
    "agente_vegetacao": VegetationAgent,
    "agente_deteccao": DetectionAgent,
    "agente_classificacao": QueuedClassificationAgent,
    "agente_analise_raster": QueuedRasterAnalysisAgent,
    "agente_analise_terreno": QueuedTerrainAnalysisAgent,
    "agente_analise_hidrologia": QueuedHydrologyAnalysisAgent,
    "agente_mudanca": ChangeAgent,
    "agente_relatorio": ReportAgent,
}


class Orchestrator:
    """Polls the tarefas_agentes table and dispatches work to the appropriate agent."""

    # ------------------------------------------------------------------
    # Fetch the next pending task
    # ------------------------------------------------------------------
    def fetch_next_task(self):
        """
        SELECT the highest-priority pending task, atomically mark it
        'em_execucao', and return it as a dict.  Returns None when the
        queue is empty.
        """
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                # Lock the row so no other orchestrator grabs it
                cursor.execute(
                    """
                    SELECT *
                      FROM tarefas_agentes
                     WHERE status = 'pendente'
                     ORDER BY prioridade ASC, criado_em ASC
                     LIMIT 1
                     FOR UPDATE SKIP LOCKED
                    """,
                )
                task = cursor.fetchone()
                if task is None:
                    conn.rollback()
                    return None

                cursor.execute(
                    """
                    UPDATE tarefas_agentes
                       SET status          = 'em_execucao',
                           inicio_execucao = %s
                     WHERE id = %s
                    """,
                    (datetime.now(), task["id"]),
                )
                params=task.get("parametros") or {}
                if isinstance(params,str):
                    try: params=json.loads(params)
                    except ValueError: params={}
                analysis_id=params.get("_analysis_id") if isinstance(params,dict) else None
                if analysis_id:
                    cursor.execute("UPDATE analises SET status='processando',observacoes=NULL,atualizado_em=now() WHERE id=%s",(analysis_id,))
                conn.commit()
                return task
            finally:
                cursor.close()

    # ------------------------------------------------------------------
    # Execute a task by dispatching to the right agent
    # ------------------------------------------------------------------
    def execute_task(self, task):
        """Instantiate the correct agent and run it.  Handle success/failure."""
        agente_key = task["agente"]
        agent_cls = AGENTS.get(agente_key)

        if agent_cls is None:
            self._mark_error(
                task, f"Unknown agent type: {agente_key}"
            )
            return

        agent = agent_cls()
        try:
            logger.info(
                "Agent %s executing task %d (type=%s)",
                agente_key,
                task["id"],
                task["tipo_tarefa"],
            )
            result = agent.execute(task)
            self._mark_success(task, result)
            logger.info("Task %d completed successfully.", task["id"])
        except Exception as exc:
            tb = traceback.format_exc()
            logger.error("Task %d failed: %s\n%s", task["id"], exc, tb)
            self._mark_failure(task, str(exc))

    # ------------------------------------------------------------------
    # Helpers to update task status
    # ------------------------------------------------------------------
    def _mark_success(self, task, result):
        execute_query(
            """
            UPDATE tarefas_agentes
               SET status        = 'concluido',
                   resultado     = %s,
                   fim_execucao  = %s
             WHERE id = %s
            """,
            (Json(result,dumps=lambda value: json.dumps(value,ensure_ascii=False,default=str)), datetime.now(), task["id"]),
            commit=True,
        )

    def _mark_failure(self, task, error_msg):
        tentativas = (task.get("tentativas") or 0) + 1
        max_tentativas = task.get("max_tentativas") or 3
        new_status = "erro" if tentativas >= max_tentativas else "pendente"

        execute_query(
            """
            UPDATE tarefas_agentes
               SET status        = %s,
                   erro_msg      = %s,
                   tentativas    = %s,
                   fim_execucao  = %s
             WHERE id = %s
            """,
            (new_status, error_msg, tentativas, datetime.now(), task["id"]),
            commit=True,
        )
        params=task.get("parametros") or {}
        if isinstance(params,str):
            try: params=json.loads(params)
            except ValueError: params={}
        analysis_id=params.get("_analysis_id") if isinstance(params,dict) else None
        if analysis_id:
            status="em_fila" if new_status=="pendente" else "erro"
            execute_query("UPDATE analises SET status=%s,observacoes=%s,atualizado_em=now() WHERE id=%s",
                          (status,error_msg,analysis_id),commit=True)

    def _mark_error(self, task, error_msg):
        execute_query(
            """
            UPDATE tarefas_agentes
               SET status   = 'erro',
                   erro_msg = %s,
                   fim_execucao = %s
             WHERE id = %s
            """,
            (error_msg, datetime.now(), task["id"]),
            commit=True,
        )
        params=task.get("parametros") or {}
        if isinstance(params,str):
            try: params=json.loads(params)
            except ValueError: params={}
        analysis_id=params.get("_analysis_id") if isinstance(params,dict) else None
        if analysis_id:
            execute_query("UPDATE analises SET status='erro',observacoes=%s,atualizado_em=now() WHERE id=%s",
                          (error_msg,analysis_id),commit=True)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self, poll_interval=10, stop_event: Event | None = None):
        """Poll forever, dispatching tasks as they appear."""
        logger.info("Orchestrator started. Polling every %ds", poll_interval)
        logger.info("Registered agents: %s", ", ".join(sorted(AGENTS)))
        while stop_event is None or not stop_event.is_set():
            try:
                task = self.fetch_next_task()
                if task:
                    logger.info(
                        "Processing task %d: %s", task["id"], task["tipo_tarefa"]
                    )
                    self.execute_task(task)
                elif stop_event is None:
                    time.sleep(poll_interval)
                else:
                    stop_event.wait(poll_interval)
            except KeyboardInterrupt:
                logger.info("Orchestrator stopped by user.")
                break
            except Exception:
                logger.exception("Unexpected error in orchestrator loop")
                if stop_event is None:
                    time.sleep(poll_interval)
                else:
                    stop_event.wait(poll_interval)


if __name__ == "__main__":
    Orchestrator().run()
