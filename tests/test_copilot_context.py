import asyncio
from fastapi import HTTPException

from backend.routers import agents
from backend.agents.schemas import CopilotResponse, TOOL_CATALOG, ToolRequest
from backend.routers.agents import _read_raster_sample
from backend.agents.llm_client import LMStudioClient
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
import numpy as np
import requests


class Cursor:
    def __init__(self, user_id):
        self.user_id = user_id
        self.row = None
        self.rows = []

    def execute(self, query, params=()):
        if 'SELECT id,projeto_id,estado FROM copilot_threads' in query:
            self.row = {'id': 14, 'projeto_id': 8, 'estado': {}} if params == (14, 5) else None
        elif 'SELECT papel,conteudo' in query:
            self.rows = [
                {'papel': 'user', 'conteudo': 'Calcule area e perimetro desta geometria.'},
                {'papel': 'assistant', 'conteudo': 'O projeto tem o produto DTM 31.', 'ferramentas': [
                    {'tool': 'medir_geometria', 'result': {'dados': {'area_m2': 123, 'perimetro_m': 44, 'unidade_area': 'm2'}}}
                ]},
                {'papel': 'user', 'conteudo': 'Qual produto tem DTM?'},
            ]
        elif 'SELECT id,nome,status FROM projetos' in query:
            self.row = {'id': 8, 'nome': 'Projeto de teste', 'status': 'ativo'}
        elif 'SELECT chave,valor FROM copilot_memorias' in query:
            self.rows = [{'chave': 'preferencia_unidades', 'valor': 'hectares'}]
        elif 'SELECT id,data_voo,altitude_voo_m' in query or 'SELECT p.id,p.tipo,p.formato,p.crs' in query or 'SELECT a.id,a.tipo,a.categoria' in query:
            self.rows = []
        else:
            self.row = None

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class Connection:
    def __init__(self, user_id):
        self.user_id = user_id

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def cursor(self, dictionary=False):
        return Cursor(self.user_id)

    def commit(self):
        pass


def test_copilot_resumes_owned_thread_and_measures_selected_geometry(monkeypatch):
    captured = []
    user = {'id': 5, 'perfil': 'pesquisador'}
    monkeypatch.setattr(agents, 'get_connection', lambda: Connection(user['id']))
    monkeypatch.setattr(agents, 'require_project_role', lambda *_: None)

    class Client:
        def complete(self, messages, tools):
            captured.append(messages)
            return CopilotResponse(answer='A geometria foi medida.', confidence=0.9), {'model': 'test'}

    monkeypatch.setattr(agents, 'LMStudioClient', Client)
    geometry = {'type': 'Feature', 'properties': {}, 'geometry': {
        'type': 'Polygon', 'coordinates': [[[0, 0], [0.001, 0], [0.001, 0.001], [0, 0.001], [0, 0]]]
    }}
    response = asyncio.run(agents.ask_copilot({
        'prompt': 'Calcule area e perimetro desta geometria.',
        'thread_id': 14,
        'context': {'projeto_id': 8, 'geometria': geometry},
    }, user))
    assert captured[0][1] == {'role': 'user', 'content': 'Qual produto tem DTM?'}
    assert captured[0][2]['role'] == 'assistant'
    assert captured[0][2]['content'].startswith('O projeto tem o produto DTM 31.')
    assert 'Evidencias estruturadas desta resposta' in captured[0][2]['content']
    assert '"unidade_area": "m2"' in captured[0][2]['content']
    assert 'Memorias pessoais' in captured[0][0]['content']
    assert 'preferencia_unidades' in captured[0][3]['content']
    assert 'hectares' in captured[0][3]['content']
    assert 'medir_geometria' in [tool['tool'] for tool in response['ferramentas_executadas']]
    measurement = response['ferramentas_executadas'][0]['result']['dados']
    assert measurement['area_m2'] > 12_000
    assert measurement['perimetro_m'] > 400
    assert response['ferramentas_executadas'][0]['result']['origem']['tipo'] == 'geometria_selecionada_no_mapa'


def test_copilot_hides_threads_owned_by_another_user(monkeypatch):
    user = {'id': 99, 'perfil': 'pesquisador'}
    monkeypatch.setattr(agents, 'get_connection', lambda: Connection(user['id']))
    monkeypatch.setattr(agents, 'require_project_role', lambda *_: None)
    try:
        asyncio.run(agents.ask_copilot({
            'prompt': 'Continue a analise anterior.', 'thread_id': 14,
            'context': {'projeto_id': 8},
        }, user))
        assert False, 'Thread de outro usuario deveria ser negada'
    except HTTPException as error:
        assert error.status_code == 404


def test_raster_sampling_masks_pixels_outside_selected_aoi():
    data = np.arange(100, dtype=np.float32).reshape(10, 10)
    polygon = {'type': 'Polygon', 'coordinates': [[
        [500000, 1000], [500040, 1000], [500040, 960], [500000, 960], [500000, 1000]
    ]]}
    with MemoryFile() as memory:
        with memory.open(driver='GTiff', height=10, width=10, count=1, dtype='float32', crs='EPSG:32623', transform=from_origin(500000, 1000, 10, 10)) as dataset:
            dataset.write(data, 1)
        with memory.open() as dataset:
            sampled, affine = _read_raster_sample(dataset, polygon, 'EPSG:32623', max_dimension=None)
    assert sampled.count() == 16
    assert np.isclose(float(sampled.mean()), float(data[:4, :4].mean()))
    assert affine.a == 10 and affine.e == -10


def test_lm_studio_timeout_returns_controlled_error(monkeypatch):
    calls = []

    def timeout(*_args, **_kwargs):
        calls.append(1)
        raise requests.Timeout('simulated timeout')

    monkeypatch.setattr('backend.agents.llm_client.requests.post', timeout)
    monkeypatch.setattr('backend.agents.llm_client.time.sleep', lambda *_: None)
    try:
        LMStudioClient().complete([{'role': 'user', 'content': 'test'}], [])
        assert False, 'Timeout deveria retornar erro controlado'
    except RuntimeError as error:
        assert 'apos 3 tentativas' in str(error)
    assert len(calls) == 3


def test_lm_studio_native_tool_calls_avoid_structured_output_conflict(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {'model': 'qwen/qwen3.8-27b', 'choices': [{'message': {
                'content': '',
                'tool_calls': [{'function': {'name': 'medir_geometria', 'arguments': '{"geometry":{"type":"Polygon"}}'}}],
            }}]}

    def post(_url, json, timeout):
        captured.update(json)
        return Response()

    monkeypatch.setattr('backend.agents.llm_client.requests.post', post)
    result, _ = LMStudioClient().complete([{'role': 'user', 'content': 'Meça esta geometria.'}], TOOL_CATALOG)

    assert 'response_format' not in captured
    assert captured['tool_choice'] == 'auto'
    assert result.tool_calls[0].name == 'medir_geometria'
    assert result.tool_calls[0].arguments == {'geometry': {'type': 'Polygon'}}


def test_lm_studio_keeps_json_schema_for_final_responses(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {'model': 'qwen/qwen3.8-27b', 'choices': [{'message': {
                'content': '{"answer":"Área calculada.","tool_calls":[],"confidence":0.9}',
            }}]}

    def post(_url, json, timeout):
        captured.update(json)
        return Response()

    monkeypatch.setattr('backend.agents.llm_client.requests.post', post)
    result, _ = LMStudioClient().complete([{'role': 'user', 'content': 'Resuma o resultado.'}], [])

    assert captured['response_format']['type'] == 'json_schema'
    assert result.answer == 'Área calculada.'
    assert result.confidence == 0.9


def test_copilot_does_not_execute_repeated_identical_tool_calls(monkeypatch):
    executions = []
    calls = []
    geometry = {'type': 'Polygon', 'coordinates': [[[0, 0], [0.001, 0], [0.001, 0.001], [0, 0]]]}

    class Client:
        def complete(self, messages, tools):
            calls.append(bool(tools))
            if tools:
                return CopilotResponse(answer='', tool_calls=[ToolRequest(
                    name='buffer_geometria', arguments={'geometry': geometry, 'distancia': 20}
                )]), {'model': 'test'}
            return CopilotResponse(answer='Buffer criado uma vez.', confidence=0.9), {'model': 'test'}

    async def execute(data, _user):
        executions.append(data)
        return {'status': 'ok', 'dados': {'geometry': geometry, 'distancia_m': 20}}

    monkeypatch.setattr(agents, 'LMStudioClient', Client)
    monkeypatch.setattr(agents, 'execute_tool', execute)
    monkeypatch.setattr(agents, '_audit', lambda *_args, **_kwargs: None)
    response = asyncio.run(agents.ask_copilot({'prompt': 'Gere um buffer de 20 metros.'}, {'id': 5}))

    assert len(executions) == 1
    assert len(response['ferramentas_executadas']) == 1
    assert response['resposta']['answer'] == 'Buffer criado uma vez.'
    assert calls == [True, True, False]
