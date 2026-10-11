"""Ensure metadata creation returns the PostgreSQL-generated product ID."""

import asyncio
from contextlib import contextmanager

from backend.routers import ortomapas


def test_create_returns_inserted_id_not_mysql_lastrowid(monkeypatch):
    class Cursor:
        lastrowid = 0  # PostgreSQL exposes an OID here, not the new row ID.

        def execute(self, sql, params):
            self.sql, self.params = sql, params
            if "INSERT INTO" in sql:
                assert "RETURNING id" in sql

        def fetchone(self):
            if "INSERT INTO" in self.sql:
                return {"id": 321}
            if "FROM ortomapas" in self.sql:
                assert self.params == (321,)
                return {"id": 321, "projeto_id": 9, "nome": "Teste"}
            return {"id": 9}

    class Connection:
        def cursor(self, dictionary=False):
            assert dictionary
            return Cursor()

        def commit(self):
            pass

    @contextmanager
    def connection():
        yield Connection()

    monkeypatch.setattr(ortomapas, "get_connection", connection)
    result = asyncio.run(ortomapas.create_ortomapa({"projeto_id": 9, "voo_id": 1, "nome": "Teste"}, {"id": 1, "perfil": "admin"}))
    assert result["id"] == 321


def test_invalid_tile_rejected_before_database_access(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    def no_database():
        raise AssertionError("Invalid coordinates must not query the database")

    monkeypatch.setattr(ortomapas, "get_connection", no_database)
    app = FastAPI()
    app.include_router(ortomapas.router)
    app.dependency_overrides[ortomapas.media_user] = lambda: {"id": 1, "perfil": "admin"}
    with TestClient(app) as client:
        assert client.get("/ortomapas/1/tile/23/0/0.png").status_code == 422
        assert client.get("/ortomapas/1/tile/2/4/0.png").status_code == 422
