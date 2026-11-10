"""Remove the disposable app-side records/files for one real ODM acceptance run.

Guarded by the unique validation project-name prefix. The NodeODM task is also
removed through its documented task/remove endpoint and verified absent.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.config import DATA_DIR, NODEODM_URL
from backend.database.connection import get_connection


DATA_ROOT = Path(DATA_DIR).resolve()
ODM_UPLOADS = (DATA_ROOT / "odm_uploads").resolve()


def resolve_data_path(value: str) -> Path:
    raw = Path(value[5:] if value.startswith("data/") else value)
    path = (raw if raw.is_absolute() else DATA_ROOT / raw).resolve()
    if not path.is_relative_to(DATA_ROOT):
        raise RuntimeError(f"Recusando caminho fora de data/: {value}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    project_id = int(manifest["project_id"])
    project_name = str(manifest["project_name"])
    email = str(manifest["test_user_email"])
    task_ids = [str(value) for value in manifest.get("task_ids", [])]
    if manifest.get("task_id"):
        task_ids.append(str(manifest["task_id"]))
    task_ids = sorted(set(task_ids))
    processing_ids = [int(value) for value in manifest.get("processing_ids", [])]
    if manifest.get("processing_id"):
        processing_ids.append(int(manifest["processing_id"]))
    processing_ids = sorted(set(processing_ids))

    if not project_name.startswith("Aceite NodeODM Aukerman Fase3-"):
        raise RuntimeError("Nome do projeto não corresponde ao prefixo temporário da Fase 3")
    if not re.fullmatch(r"aceite-odm-Fase3-[A-Za-z0-9-]+@example\.test", email, re.IGNORECASE):
        raise RuntimeError("E-mail não corresponde ao padrão descartável desta validação")
    email = email.lower()
    if any(not re.fullmatch(r"[0-9a-f-]{36}", task_id) for task_id in task_ids):
        raise RuntimeError("UUID de tarefa inválido")

    # Read paths and verify ownership before deleting any database row.
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM projetos WHERE id=%s AND nome=%s", (project_id, project_name))
        if not cur.fetchone():
            raise RuntimeError("Projeto da validação não encontrado; nada foi removido")
        for processing_id in processing_ids:
            cur.execute("SELECT id, projeto_id, odm_task_id FROM processamentos_odm WHERE id=%s", (processing_id,))
            processing = cur.fetchone()
            if not processing or processing["projeto_id"] != project_id or processing["odm_task_id"] not in task_ids:
                raise RuntimeError("Vínculo de projeto/processamento/tarefa não confere; nada foi removido")

        paths: set[str] = set()
        for sql, params in (
            ("SELECT caminho_arquivo AS caminho FROM ortomapas WHERE projeto_id=%s UNION ALL SELECT caminho_thumbnail FROM ortomapas WHERE projeto_id=%s", (project_id, project_id)),
            ("SELECT resultado_path AS caminho FROM analises WHERE projeto_id=%s UNION ALL SELECT resultado_thumbnail FROM analises WHERE projeto_id=%s", (project_id, project_id)),
            ("SELECT p.caminho FROM produtos_processamento p JOIN processamentos_odm j ON j.id=p.processamento_id WHERE j.projeto_id=%s", (project_id,)),
            ("SELECT f.caminho FROM voo_fotos f JOIN voos v ON v.id=f.voo_id WHERE v.projeto_id=%s UNION ALL SELECT fotos_path FROM voos WHERE projeto_id=%s", (project_id, project_id)),
        ):
            cur.execute(sql, params)
            paths.update(str(row["caminho"]) for row in cur.fetchall() if row.get("caminho"))

    # Remove only this run's NodeODM task, then verify the UUID disappeared.
    removed_task_ids = []
    for task_id in task_ids:
        remove = requests.post(f"{NODEODM_URL}/task/remove", json={"uuid": task_id}, timeout=60)
        remove.raise_for_status()
        task_list = requests.get(f"{NODEODM_URL}/task/list", timeout=30)
        task_list.raise_for_status()
        if task_id in task_list.text:
            raise RuntimeError("NodeODM ainda lista a tarefa após task/remove")
        removed_task_ids.append(task_id)

    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("DELETE FROM projetos WHERE id=%s AND nome=%s", (project_id, project_name))
        if cur.rowcount != 1:
            raise RuntimeError("Não foi possível remover exatamente o projeto temporário")
        cur.execute("DELETE FROM usuarios WHERE email=%s", (email,))
        if cur.rowcount != 1:
            raise RuntimeError("Não foi possível remover exatamente a conta temporária")
        conn.commit()

        removed_files = []
        retained_referenced_files = []
        for value in sorted(paths):
            target = resolve_data_path(value)
            cur.execute(
                """SELECT
                  EXISTS(SELECT 1 FROM ortomapas WHERE caminho_arquivo=%s OR caminho_thumbnail=%s)
                  OR EXISTS(SELECT 1 FROM analises WHERE resultado_path=%s OR resultado_thumbnail=%s)
                  OR EXISTS(SELECT 1 FROM produtos_processamento WHERE caminho=%s)
                  OR EXISTS(SELECT 1 FROM voo_fotos WHERE caminho=%s) AS referenced""",
                (value, value, value, value, value, value),
            )
            if cur.fetchone()["referenced"]:
                retained_referenced_files.append(value)
                continue
            if target.is_file():
                target.unlink()
                removed_files.append(value)
            elif target.is_dir() and target.parent == ODM_UPLOADS:
                # fotos_path is a UUID directory created by the upload endpoint.
                if re.fullmatch(r"[0-9a-f-]{36}", target.name):
                    shutil.rmtree(target)
                    removed_files.append(value + "/ (diretório de fotos)")
        if retained_referenced_files:
            raise RuntimeError(f"Alguns caminhos continuam referenciados e foram preservados: {retained_referenced_files}")

        cur.execute("SELECT COUNT(*) AS n FROM projetos WHERE id=%s", (project_id,))
        project_remaining = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM usuarios WHERE email=%s", (email,))
        user_remaining = cur.fetchone()["n"]
    if project_remaining or user_remaining:
        raise RuntimeError("Verificação pós-limpeza encontrou registro temporário")

    manifest["cleanup"] = {
        "status": "completed",
        "nodeodm_task_removed_count": len(removed_task_ids),
        "project_removed": True,
        "temporary_user_removed": True,
        "temporary_file_count_removed": len(removed_files),
        "remaining_project_rows": project_remaining,
        "remaining_user_rows": user_remaining,
        "account_email_redacted": True,
    }
    manifest.pop("test_user_email", None)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(manifest["cleanup"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
