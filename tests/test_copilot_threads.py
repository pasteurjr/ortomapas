import asyncio
from contextlib import contextmanager

from backend.routers import copilot


class ThreadCursor:
    def __init__(self):
        self.rows = []
        self.query = None
        self.params = None

    def execute(self, query, params=()):
        self.query = query
        self.params = params
        self.rows = [
            {'id': 18, 'projeto_id': 4, 'usuario_id': 2, 'titulo': 'Conversa recente'},
            {'id': 11, 'projeto_id': 4, 'usuario_id': 2, 'titulo': 'Conversa anterior'},
        ]

    def fetchall(self):
        return self.rows


class ThreadConnection:
    def __init__(self):
        self.cursor_instance = ThreadCursor()

    def cursor(self, dictionary=False):
        assert dictionary
        return self.cursor_instance


def test_list_threads_is_scoped_to_user_and_project(monkeypatch):
    connection = ThreadConnection()

    @contextmanager
    def get_connection():
        yield connection

    monkeypatch.setattr(copilot, 'get_connection', get_connection)
    result = asyncio.run(copilot.list_threads(4, {'id': 2, 'perfil': 'admin'}))

    assert [thread['id'] for thread in result['conversas']] == [18, 11]
    assert 'WHERE projeto_id=%s AND usuario_id=%s ORDER BY atualizado_em DESC' in connection.cursor_instance.query
    assert connection.cursor_instance.params == (4, 2)
