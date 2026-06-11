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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.connection import get_connection, execute_query
from backend.agents.vegetation_agent import VegetationAgent
from backend.agents.detection_agent import DetectionAgent
from backend.agents.classification_agent import ClassificationAgent
from backend.agents.change_agent import ChangeAgent
from backend.agents.report_agent import ReportAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("orchestrator")

AGENTS = {
    "agente_vegetacao": VegetationAgent,
    "agente_deteccao": DetectionAgent,
    "agente_classificacao": ClassificationAgent,
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
                     ORDER BY prioridade ASC, created_at ASC
                     LIMIT 1
                     FOR UPDATE
                    """,
                )
                task = cursor.fetchone()
                if task is None:
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
            (json.dumps(result, ensure_ascii=False, default=str), datetime.now(), task["id"]),
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

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self, poll_interval=10):
        """Poll forever, dispatching tasks as they appear."""
        logger.info("Orchestrator started. Polling every %ds", poll_interval)
        while True:
            try:
                task = self.fetch_next_task()
                if task:
                    logger.info(
                        "Processing task %d: %s", task["id"], task["tipo_tarefa"]
                    )
                    self.execute_task(task)
                else:
                    time.sleep(poll_interval)
            except KeyboardInterrupt:
                logger.info("Orchestrator stopped by user.")
                break
            except Exception:
                logger.exception("Unexpected error in orchestrator loop")
                time.sleep(poll_interval)


if __name__ == "__main__":
    Orchestrator().run()
