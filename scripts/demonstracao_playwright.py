#!/usr/bin/env python3
"""Captura evidencias visuais da demonstracao operacional."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path('docs/validacao/demonstracao_2026-09-14')
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1920, 'height': 1080}, ignore_https_errors=True)
    page.goto('http://127.0.0.1:5176/', wait_until='networkidle', timeout=30000)
    page.screenshot(path=str(OUT/'01_aplicacao_mapa.png'), full_page=False)
    page.goto('http://127.0.0.1:8888/docs', wait_until='networkidle', timeout=30000)
    page.screenshot(path=str(OUT/'02_api_swagger.png'), full_page=False)
    page.goto('http://127.0.0.1:8020/', wait_until='domcontentloaded', timeout=30000)
    page.screenshot(path=str(OUT/'03_webodm.png'), full_page=False)
    page.goto('http://127.0.0.1:8021/info', wait_until='networkidle', timeout=30000)
    page.screenshot(path=str(OUT/'04_nodeodm_info.png'), full_page=False)
    (OUT/'servicos.json').write_text(json.dumps({
        'webodm_url': 'http://127.0.0.1:8020',
        'nodeodm_url': 'http://127.0.0.1:8021/info',
        'frontend_url': 'http://127.0.0.1:5176',
        'backend_url': 'http://127.0.0.1:8888'
    }, indent=2), encoding='utf-8')
    browser.close()
print(OUT)
