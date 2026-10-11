from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.config import AUTH_SECRET
from backend.utils import resource_access


def test_media_tickets_scope_expiry_and_purpose(monkeypatch):
    monkeypatch.setattr(resource_access, "active_user", lambda uid: {"id": uid, "perfil": "pesquisador"})
    app = FastAPI()
    @app.get("/api/ortomapas/{id}/tile/{z}/{x}/{y}.png")
    def tile(user=Depends(resource_access.media_user)):
        return {"user": user["id"]}
    ticket = resource_access.media_ticket({"id": 10}, "/api/ortomapas/30/tile/")
    path = "/api/ortomapas/30/tile/1/0/0.png"
    with TestClient(app) as client:
        assert client.get(path, params={"ticket": ticket}).status_code == 200
        assert client.get(path.replace("/30/", "/31/"), params={"ticket": ticket}).status_code == 401
        expired = jwt.encode({"sub": "10", "purpose": "media", "scope": "/api/ortomapas/30/tile/", "exp": datetime.now(timezone.utc)-timedelta(seconds=1)}, AUTH_SECRET, algorithm="HS256")
        assert client.get(path, params={"ticket": expired}).status_code == 401
        assert client.get(path, params={"ticket": ticket + "corrompido"}).status_code == 401


def test_data_directory_escape_rejected():
    import pytest
    from fastapi import HTTPException
    for path in ("/etc/passwd", "../.env", "ortomapas/../../.env"):
        with pytest.raises(HTTPException) as exc:
            resource_access.data_path(path)
        assert exc.value.status_code == 403
