"""Regression tests for project-scoped project and flight access."""

import asyncio
from contextlib import contextmanager

import pytest
from fastapi import HTTPException

from backend.routers import projetos, voos


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor

    def cursor(self, dictionary=False):
        assert dictionary
        return self.fake_cursor


@contextmanager
def fake_connection(cursor):
    yield FakeConnection(cursor)


class MemberCursor:
    rowcount = 1

    def __init__(self, membership=None):
        self.membership = membership
        self.statements = []
        self.current_sql = ""

    def execute(self, sql, params=None):
        self.current_sql = sql
        self.statements.append((sql, params))

    def fetchone(self):
        if "SELECT id FROM projetos" in self.current_sql:
            return {"id": 9}
        if "SELECT papel FROM projeto_usuarios" in self.current_sql:
            return self.membership
        return None

    def fetchall(self):
        return [{"id": 10, "email": "member@example.test", "nome": "Membro", "perfil": "pesquisador", "papel": "proprietario", "criado_em": None}]


def test_global_reader_profile_without_project_membership_cannot_list_members(monkeypatch):
    cursor = MemberCursor(membership=None)
    monkeypatch.setattr(projetos, "get_connection", lambda: fake_connection(cursor))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(projetos.list_project_users(9, {"id": 22, "perfil": "leitor"}))

    assert exc.value.status_code == 403
    assert len(cursor.statements) == 2
    assert "JOIN usuarios" not in cursor.statements[-1][0]


def test_project_viewer_can_list_members_of_own_project(monkeypatch):
    cursor = MemberCursor(membership={"papel": "visualizador"})
    monkeypatch.setattr(projetos, "get_connection", lambda: fake_connection(cursor))

    result = asyncio.run(projetos.list_project_users(9, {"id": 22, "perfil": "leitor"}))

    assert result["total"] == 1
    assert result["usuarios"][0]["papel"] == "proprietario"
    assert "JOIN usuarios" in cursor.statements[-1][0]


class FlightCursor:
    def __init__(self):
        self.sql = ""
        self.params = None

    def execute(self, sql, params=None):
        self.sql, self.params = sql, params

    def fetchall(self):
        return []


def test_unfiltered_flight_list_is_scoped_to_membership(monkeypatch):
    cursor = FlightCursor()
    monkeypatch.setattr(voos, "get_connection", lambda: fake_connection(cursor))

    asyncio.run(voos.list_voos(None, {"id": 22, "perfil": "pesquisador"}))

    assert "projeto_id IN (SELECT projeto_id FROM projeto_usuarios WHERE usuario_id = %s)" in cursor.sql
    assert cursor.params == [22]


def test_admin_can_list_flights_across_projects(monkeypatch):
    cursor = FlightCursor()
    monkeypatch.setattr(voos, "get_connection", lambda: fake_connection(cursor))

    asyncio.run(voos.list_voos(None, {"id": 1, "perfil": "admin"}))

    assert "projeto_id IN (SELECT projeto_id FROM projeto_usuarios" not in cursor.sql
    assert cursor.params == []
