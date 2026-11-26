"""Guard catalog deletion from cascading over operational history."""
import asyncio
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.routers import ortomapas


class FakeCursor:
    def __init__(self, dependencies):
        self.dependencies = dependencies
        self.row = None
        self.statements = []

    def execute(self, query, params=None):
        self.statements.append((query, params))
        if "SELECT * FROM ortomapas" in query:
            self.row = {"id": 955, "projeto_id": 88, "caminho_arquivo": "/fixture/only.tif"}
        elif "COUNT(*) AS total" in query:
            table = next(name for name in self.dependencies if f"FROM {name} " in query)
            self.row = {"total": self.dependencies[table]}

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, dependencies):
        self.cursor_instance = FakeCursor(dependencies)
        self.commits = 0

    def cursor(self, dictionary=False):
        return self.cursor_instance

    def commit(self):
        self.commits += 1

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class OrtomapaDeleteGuardTests(unittest.TestCase):
    def run_delete(self, dependencies):
        connection = FakeConnection(dependencies)
        with patch.object(ortomapas, "get_connection", return_value=connection):
            result = asyncio.run(ortomapas.delete_ortomapa(955, {"id": 1, "perfil": "admin"}))
        return connection, result

    def test_linked_records_block_delete_without_commit(self):
        dependencies = {
            "analises": 1,
            "anotacoes": 1,
            "comparacoes_temporais": 0,
            "tarefas_agentes": 0,
        }
        connection = FakeConnection(dependencies)
        with patch.object(ortomapas, "get_connection", return_value=connection):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(ortomapas.delete_ortomapa(955, {"id": 1, "perfil": "admin"}))
        self.assertEqual(raised.exception.status_code, 409)
        self.assertIn("1 análise", raised.exception.detail)
        self.assertIn("1 anotação", raised.exception.detail)
        self.assertFalse(any(statement.startswith("DELETE") for statement, _ in connection.cursor_instance.statements))
        self.assertEqual(connection.commits, 0)

    def test_unlinked_record_can_be_removed_from_catalog(self):
        dependencies = {
            "analises": 0,
            "anotacoes": 0,
            "comparacoes_temporais": 0,
            "tarefas_agentes": 0,
        }
        connection, result = self.run_delete(dependencies)
        self.assertEqual(result["id"], 955)
        self.assertTrue(any(statement.startswith("DELETE FROM ortomapas") for statement, _ in connection.cursor_instance.statements))
        self.assertEqual(connection.commits, 1)


if __name__ == "__main__":
    unittest.main()
