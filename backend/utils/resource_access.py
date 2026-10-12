"""Project-scoped access to rasters, generated files and short-lived media links."""

from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.responses import FileResponse

from backend.config import AUTH_SECRET, DATA_DIR
from backend.database.connection import get_connection
from backend.routers.auth import active_user, current_user, require_project_role

READ_ROLES = {"proprietario", "editor", "visualizador"}
tool_context = ContextVar("tool_project_context", default=None)


def data_path(value: str) -> Path:
    root = Path(DATA_DIR).resolve()
    raw = Path(value[5:] if value.startswith("data/") else value)
    path = (raw if raw.is_absolute() else root / raw).resolve()
    if not path.is_relative_to(root):
        raise HTTPException(status_code=403, detail="Arquivo fora do diretorio de dados")
    return path


def file_projects(value: str, user: dict) -> set:
    path = data_path(value)
    relative = path.relative_to(Path(DATA_DIR).resolve()).parts
    if len(relative) >= 4 and relative[:2] == ("analises", "projetos"):
        try:
            project_id = int(relative[2])
        except ValueError:
            raise HTTPException(status_code=403, detail="Diretorio de resultado invalido")
        require_project_role(project_id, user, READ_ROLES)
        return {project_id}
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT projeto_id, caminho_arquivo AS caminho FROM ortomapas
            UNION ALL SELECT projeto_id, caminho_thumbnail FROM ortomapas
            UNION ALL SELECT projeto_id, resultado_path FROM analises
            UNION ALL SELECT projeto_id, resultado_thumbnail FROM analises
            UNION ALL SELECT j.projeto_id, p.caminho FROM produtos_processamento p
              JOIN processamentos_odm j ON j.id=p.processamento_id
            UNION ALL SELECT v.projeto_id, f.caminho FROM voo_fotos f JOIN voos v ON v.id=f.voo_id""")
        matches = set()
        for row in cur.fetchall():
            try:
                if row["caminho"] and data_path(row["caminho"]) == path:
                    matches.add(row["projeto_id"])
            except HTTPException:
                continue
    permitted = set()
    for project_id in matches:
        try:
            require_project_role(project_id, user, READ_ROLES)
            permitted.add(project_id)
        except HTTPException as exc:
            if exc.status_code != 403:
                raise
    if not permitted:
        raise HTTPException(status_code=403, detail="Arquivo sem acesso autorizado neste projeto")
    return permitted


def media_ticket(user: dict, scope: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user["id"]), "purpose": "media", "scope": scope, "iat": now, "exp": now + timedelta(minutes=5)}, AUTH_SECRET, algorithm="HS256")


async def media_user(request: Request) -> dict:
    if request.headers.get("authorization"):
        return current_user(request.headers["authorization"])
    try:
        payload = jwt.decode(request.query_params.get("ticket", ""), AUTH_SECRET, algorithms=["HS256"])
        scope = payload["scope"]
        path = request.url.path
        if payload.get("purpose") != "media" or not (scope == path or (scope.endswith("/tile/") and path.startswith(scope))):
            raise ValueError("Escopo invalido")
        return active_user(int(payload["sub"]))
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Autenticacao de midia necessaria")


async def secure_file(path: str, user: dict = Depends(media_user)):
    file_projects(path, user)
    target = data_path(path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado")
    return FileResponse(target, headers={"Cache-Control": "private, no-store"})


async def file_access(data: dict, user: dict = Depends(current_user)):
    path = data_path(str(data.get("path", "")))
    file_projects(str(path), user)
    scope = "/data/" + path.relative_to(Path(DATA_DIR).resolve()).as_posix()
    return {"url": quote(scope, safe="/") + "?ticket=" + media_ticket(user, scope), "expires_in": 300}


async def authorize_tools(request: Request, user: dict = Depends(current_user)):
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="Corpo deve ser um objeto JSON")
    paths = []
    for key, value in body.items():
        if key.endswith("_path") and isinstance(value, str):
            paths.append(value)
        if key == "input_paths":
            paths.extend(value.values() if isinstance(value, dict) else value)
    name = body.get("output_name")
    if name and (not isinstance(name, str) or Path(name).name != name or "\\" in name or name in {".", ".."}):
        raise HTTPException(status_code=422, detail="Nome de saida deve ser apenas um nome de arquivo")
    projects = None
    for path in paths:
        permitted = file_projects(path, user)
        projects = permitted if projects is None else projects & permitted
    if not projects:
        raise HTTPException(status_code=403, detail="Entradas devem pertencer a um projeto autorizado comum")
    if body.get("projeto_id") is not None:
        try:
            projects &= {int(body["projeto_id"])}
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="projeto_id invalido")
    if request.url.path != "/api/tools/statistics" and not (request.url.path == "/api/tools/volume" and not name and not body.get('ortomapa_id')):
        editable = set()
        for project_id in projects:
            try:
                require_project_role(project_id, user, {"proprietario", "editor"})
                editable.add(project_id)
            except HTTPException as exc:
                if exc.status_code != 403:
                    raise
        projects = editable
    if not projects:
        raise HTTPException(status_code=403, detail="Projeto sem permissao para esta operacao")
    tool_context.set((user["id"], min(projects)))
