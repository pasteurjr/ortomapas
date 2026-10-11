from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.main import RateLimitMiddleware


def test_tiles_are_bounded_without_starving_api():
    app=FastAPI()
    app.add_middleware(RateLimitMiddleware,limit=2,tile_limit=3,window=60)
    @app.get('/api/analises/1/tile/17/35770/48995.png')
    def tile(): return {'ok':True}
    @app.get('/api/control')
    def control(): return {'ok':True}
    with TestClient(app) as client:
        url='/api/analises/1/tile/17/35770/48995.png'
        for _ in range(3): assert client.get(url).status_code==200
        response=client.get(url)
        assert response.status_code==429 and response.headers['retry-after']=='60'
        for _ in range(2): assert client.get('/api/control').status_code==200
        assert client.get('/api/control').status_code==429


def test_tile_access_uses_control_budget_not_tile_budget():
    app=FastAPI()
    app.add_middleware(RateLimitMiddleware,limit=1,tile_limit=3,window=60)
    @app.get('/api/analises/1/tile-access')
    def access(): return {'ok':True}
    with TestClient(app) as client:
        assert client.get('/api/analises/1/tile-access').status_code==200
        assert client.get('/api/analises/1/tile-access').status_code==429
