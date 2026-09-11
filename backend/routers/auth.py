"""Authentication and user management for the Ortomapas API."""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Header

from backend.config import AUTH_SECRET
from backend.database.connection import get_connection

router = APIRouter()


def _token(user: dict) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user["id"]), "perfil": user["perfil"], "iat": now, "exp": now + timedelta(hours=8)}, AUTH_SECRET, algorithm="HS256")


def current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Autenticacao necessaria")
    try:
        payload = jwt.decode(authorization.split(" ", 1)[1], AUTH_SECRET, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (ValueError, KeyError, jwt.InvalidTokenError):
        raise HTTPException(status_code=401, detail="Token invalido ou expirado")
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, email, nome, perfil, ativo, ultimo_login, criado_em FROM usuarios WHERE id = %s", (user_id,))
        user = cur.fetchone()
    if not user or not user["ativo"]:
        raise HTTPException(status_code=401, detail="Usuario inativo ou inexistente")
    return dict(user)


@router.post("/auth/register", status_code=201)
async def register(data: dict):
    email = str(data.get("email", "")).strip().lower()
    nome = str(data.get("nome", "")).strip()
    senha = str(data.get("senha", ""))
    perfil = data.get("perfil", "pesquisador")
    if not email or not nome or len(senha) < 8:
        raise HTTPException(status_code=400, detail="email, nome e senha com no minimo 8 caracteres sao obrigatorios")
    if perfil not in {"admin", "pesquisador", "leitor"}:
        raise HTTPException(status_code=400, detail="perfil invalido")
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="Email ja cadastrado")
        hashed = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
        cur.execute("INSERT INTO usuarios (email, nome, senha_hash, perfil) VALUES (%s, %s, %s, %s) RETURNING id", (email, nome, hashed, perfil))
        user_id = cur.fetchone()["id"]
        conn.commit()
    return {"id": user_id, "email": email, "nome": nome, "perfil": perfil}


@router.post("/auth/login")
async def login(data: dict):
    email = str(data.get("email", "")).strip().lower()
    senha = str(data.get("senha", ""))
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        user = cur.fetchone()
        if not user or not user["ativo"] or not bcrypt.checkpw(senha.encode(), user["senha_hash"].encode()):
            raise HTTPException(status_code=401, detail="Credenciais invalidas")
        cur.execute("UPDATE usuarios SET ultimo_login = now() WHERE id = %s", (user["id"],))
        conn.commit()
    return {"access_token": _token(user), "token_type": "bearer", "usuario": {"id": user["id"], "email": user["email"], "nome": user["nome"], "perfil": user["perfil"]}}


@router.get("/auth/me")
async def me(user: dict = Depends(current_user)):
    return user
