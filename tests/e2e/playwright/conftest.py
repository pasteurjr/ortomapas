"""
Configuracao compartilhada para testes Playwright E2E.
"""
import os

BASE_URL = "http://localhost:5176"
API_URL = "http://localhost:8888"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "runtime", "screenshots")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data")

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Test ortomapa paths (relative to data/)
TEST_ORTOMAPA_1 = "ortomapas/serra_moeda_teste.tif"
TEST_ORTOMAPA_2 = "ortomapas/serra_moeda_teste_2.tif"
TEST_DSM = "dsm/serra_moeda_dsm.tif"
