import asyncio
from contextlib import contextmanager

import pytest
from fastapi import HTTPException

from backend.routers import copilot


class MemoryCursor:
    def __init__(self):
        self.query = ''
        self.params = ()
        self.executed = []
        self.row = {'id': 31, 'projeto_id': 4, 'chave': 'unidades_area', 'valor': 'hectares', 'origem': 'usuario'}
        self.rows = [self.row]

    def execute(self, query, params=()):
        self.query = query
        self.params = params
        self.executed.append((query, params))

    def fetchone(self):
        return self.row if 'SELECT id,projeto_id,chave FROM copilot_memorias' in self.query else self.row

    def fetchall(self):
        return self.rows


class MemoryConnection:
    def __init__(self):
        self.cursor_instance = MemoryCursor()
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def cursor(self, dictionary=False):
        return self.cursor_instance

    def commit(self):
        self.committed = True


def install_connection(monkeypatch, connection):
    @contextmanager
    def get_connection():
        yield connection
    monkeypatch.setattr(copilot, 'get_connection', get_connection)
    monkeypatch.setattr(copilot, 'require_project_role', lambda *_: None)


def test_list_memories_is_scoped_by_project_and_user(monkeypatch):
    connection = MemoryConnection()
    install_connection(monkeypatch, connection)

    result = asyncio.run(copilot.list_memories(4, {'id': 2, 'perfil': 'admin'}))

    assert result['memorias'][0]['chave'] == 'unidades_area'
    assert 'WHERE projeto_id=%s AND usuario_id=%s' in connection.cursor_instance.query
    assert connection.cursor_instance.params == (4, 2)


def test_save_memory_upserts_owned_value_and_audits_key_only(monkeypatch):
    connection = MemoryConnection()
    install_connection(monkeypatch, connection)

    result = asyncio.run(copilot.save_memory({
        'projeto_id': 4, 'chave': 'UNIDADES_AREA', 'valor': 'hectares'
    }, {'id': 2, 'perfil': 'admin'}))

    assert result['id'] == 31
    upsert, _ = connection.cursor_instance.executed[0]
    audit, audit_params = connection.cursor_instance.executed[1]
    assert 'ON CONFLICT (projeto_id,usuario_id,chave)' in upsert
    assert 'copilot_memory_saved' in audit
    assert 'hectares' not in audit_params[-1]
    assert connection.committed


def test_save_memory_rejects_invalid_key_and_oversized_value(monkeypatch):
    connection = MemoryConnection()
    install_connection(monkeypatch, connection)

    with pytest.raises(HTTPException) as invalid:
        asyncio.run(copilot.save_memory({'projeto_id': 4, 'chave': 'bad key', 'valor': 'x'}, {'id': 2, 'perfil': 'admin'}))
    assert invalid.value.status_code == 400

    with pytest.raises(HTTPException) as too_large:
        asyncio.run(copilot.save_memory({'projeto_id': 4, 'chave': 'large_value', 'valor': 'x' * 4097}, {'id': 2, 'perfil': 'admin'}))
    assert too_large.value.status_code == 413
    assert not connection.committed


def test_delete_memory_looks_up_only_current_users_memory(monkeypatch):
    connection = MemoryConnection()
    install_connection(monkeypatch, connection)

    result = asyncio.run(copilot.delete_memory(31, {'id': 2, 'perfil': 'admin'}))

    assert result == {'status': 'ok'}
    assert connection.committed
    lookup, lookup_params = connection.cursor_instance.executed[0]
    assert 'usuario_id=%s' in lookup
    assert lookup_params == (31, 2)
