"""
Seed script — populates the projetos table with 10 real Minas Gerais projects.

Usage::

    python -m backend.database.seed

Or directly::

    python backend/database/seed.py
"""

import logging
import sys
from pathlib import Path

# Ensure the project root is importable when running the script directly
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.database.connection import execute_query, execute_many, init_database

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Seed data — 10 real study areas in Minas Gerais
# ---------------------------------------------------------------------------
PROJETOS_SEED = [
    {
        "nome": "Serra do Cipo - Lapinha",
        "descricao": (
            "Levantamento aerofotogrametrico da regiao da Serra do Cipo, "
            "municipio de Santana do Riacho, com foco na vegetacao de campos "
            "rupestres e deteccao de mudancas ambientais."
        ),
        "area_estudo": "Serra do Cipo, Santana do Riacho - MG",
        "bbox_norte": -19.067,
        "bbox_sul": -19.167,
        "bbox_leste": -43.617,
        "bbox_oeste": -43.717,
        "centro_lat": -19.117,
        "centro_lon": -43.667,
        "objetivo": "Classificacao de campos rupestres e deteccao de mudancas",
        "responsavel": "Pesquisador",
        "data_inicio": "2026-05-01",
        "data_fim": None,
        "status": "planejado",
    },
    {
        "nome": "Brumadinho - Rio Paraopeba",
        "descricao": (
            "Monitoramento aereo da calha do Rio Paraopeba no trecho afetado "
            "pelo rompimento da barragem da Mina Corrego do Feijao, com "
            "analise multitemporal de recuperacao ambiental."
        ),
        "area_estudo": "Brumadinho, Rio Paraopeba - MG",
        "bbox_norte": -20.117,
        "bbox_sul": -20.217,
        "bbox_leste": -44.067,
        "bbox_oeste": -44.167,
        "centro_lat": -20.167,
        "centro_lon": -44.117,
        "objetivo": "Monitoramento ambiental pos-desastre da barragem",
        "responsavel": "Pesquisador",
        "data_inicio": "2026-05-01",
        "data_fim": None,
        "status": "planejado",
    },
    {
        "nome": "Serra da Moeda - Topo do Mundo",
        "descricao": (
            "Mapeamento geologico e estrutural da Serra da Moeda, incluindo "
            "o ponto turistico Topo do Mundo, com geracao de modelo digital "
            "de terreno de alta resolucao."
        ),
        "area_estudo": "Serra da Moeda, Nova Lima / Brumadinho - MG",
        "bbox_norte": -20.033,
        "bbox_sul": -20.133,
        "bbox_leste": -43.900,
        "bbox_oeste": -44.000,
        "centro_lat": -20.083,
        "centro_lon": -43.950,
        "objetivo": "Mapeamento geologico estrutural",
        "responsavel": "Pesquisador",
        "data_inicio": "2026-05-01",
        "data_fim": None,
        "status": "planejado",
    },
    {
        "nome": "Rio das Velhas - Rio Acima",
        "descricao": (
            "Monitoramento da bacia do Rio das Velhas no municipio de Rio "
            "Acima, com avaliacao da qualidade hidrica e estado de "
            "conservacao da mata ciliar por sensoriamento remoto."
        ),
        "area_estudo": "Rio das Velhas, Rio Acima - MG",
        "bbox_norte": -20.033,
        "bbox_sul": -20.133,
        "bbox_leste": -43.733,
        "bbox_oeste": -43.833,
        "centro_lat": -20.083,
        "centro_lon": -43.783,
        "objetivo": "Monitoramento de qualidade hidrica e mata ciliar",
        "responsavel": "Pesquisador",
        "data_inicio": "2026-05-01",
        "data_fim": None,
        "status": "planejado",
    },
    {
        "nome": "Serra da Piedade",
        "descricao": (
            "Estudo da geologia do itabirito e dos campos rupestres "
            "ferruginosos da Serra da Piedade, entre Caete e Sabara, com "
            "mapeamento litologico e de cobertura vegetal."
        ),
        "area_estudo": "Serra da Piedade, Caete / Sabara - MG",
        "bbox_norte": -19.767,
        "bbox_sul": -19.867,
        "bbox_leste": -43.617,
        "bbox_oeste": -43.717,
        "centro_lat": -19.817,
        "centro_lon": -43.667,
        "objetivo": "Geologia de itabirito e campos rupestres ferruginosos",
        "responsavel": "Pesquisador",
        "data_inicio": "2026-05-01",
        "data_fim": None,
        "status": "planejado",
    },
    {
        "nome": "Serra do Gandarela",
        "descricao": (
            "Avaliacao do conflito entre mineracao e conservacao na Serra do "
            "Gandarela, com mapeamento de recursos hidricos, cangas "
            "ferruginosas e areas de preservacao."
        ),
        "area_estudo": "Serra do Gandarela, Raposos / Caete - MG",
        "bbox_norte": -19.950,
        "bbox_sul": -20.050,
        "bbox_leste": -43.617,
        "bbox_oeste": -43.717,
        "centro_lat": -20.000,
        "centro_lon": -43.667,
        "objetivo": "Conflito mineracao-conservacao e recursos hidricos",
        "responsavel": "Pesquisador",
        "data_inicio": "2026-05-01",
        "data_fim": None,
        "status": "planejado",
    },
    {
        "nome": "Serra do Curral",
        "descricao": (
            "Documentacao aerea da Serra do Curral em Belo Horizonte, "
            "registrando o avanco da mineracao sobre a paisagem cultural "
            "e patrimonio tombado."
        ),
        "area_estudo": "Serra do Curral, Belo Horizonte / Nova Lima - MG",
        "bbox_norte": -19.917,
        "bbox_sul": -20.017,
        "bbox_leste": -43.850,
        "bbox_oeste": -43.950,
        "centro_lat": -19.967,
        "centro_lon": -43.900,
        "objetivo": "Documentacao de conflito minerario e paisagem cultural",
        "responsavel": "Pesquisador",
        "data_inicio": "2026-05-01",
        "data_fim": None,
        "status": "planejado",
    },
    {
        "nome": "Lagoa Santa - Matozinhos",
        "descricao": (
            "Estudo da geomorfologia carstica e do patrimonio arqueologico "
            "da regiao de Lagoa Santa e Matozinhos, com mapeamento de "
            "dolinas, grutas e sitios pre-historicos."
        ),
        "area_estudo": "Lagoa Santa / Matozinhos - MG",
        "bbox_norte": -19.500,
        "bbox_sul": -19.600,
        "bbox_leste": -44.033,
        "bbox_oeste": -44.133,
        "centro_lat": -19.550,
        "centro_lon": -44.083,
        "objetivo": "Geomorfologia carstica e patrimonio arqueologico",
        "responsavel": "Pesquisador",
        "data_inicio": "2026-05-01",
        "data_fim": None,
        "status": "planejado",
    },
    {
        "nome": "Quadrilatero Ferrifero - Lavras Novas",
        "descricao": (
            "Mapeamento da paisagem de mineracao historica em Lavras Novas, "
            "distrito de Ouro Preto, com identificacao de cicatrizes de "
            "mineracao colonial e cobertura vegetal atual."
        ),
        "area_estudo": "Lavras Novas, Ouro Preto - MG",
        "bbox_norte": -20.417,
        "bbox_sul": -20.517,
        "bbox_leste": -43.417,
        "bbox_oeste": -43.517,
        "centro_lat": -20.467,
        "centro_lon": -43.467,
        "objetivo": "Paisagem de mineracao historica",
        "responsavel": "Pesquisador",
        "data_inicio": "2026-05-01",
        "data_fim": None,
        "status": "planejado",
    },
    {
        "nome": "Serra de Ouro Branco",
        "descricao": (
            "Levantamento dos campos rupestres da Serra de Ouro Branco, "
            "borda sul da Cadeia do Espinhaco, com classificacao de "
            "fitofisionomias e deteccao de areas degradadas."
        ),
        "area_estudo": "Serra de Ouro Branco - MG",
        "bbox_norte": -20.450,
        "bbox_sul": -20.550,
        "bbox_leste": -43.650,
        "bbox_oeste": -43.750,
        "centro_lat": -20.500,
        "centro_lon": -43.700,
        "objetivo": "Campos rupestres da Cadeia do Espinhaco",
        "responsavel": "Pesquisador",
        "data_inicio": "2026-05-01",
        "data_fim": None,
        "status": "planejado",
    },
]

# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------
INSERT_SQL = """\
INSERT INTO projetos
    (nome, descricao, area_estudo,
     bbox_norte, bbox_sul, bbox_leste, bbox_oeste,
     centro_lat, centro_lon,
     objetivo, responsavel, data_inicio, data_fim, status)
VALUES
    (%(nome)s, %(descricao)s, %(area_estudo)s,
     %(bbox_norte)s, %(bbox_sul)s, %(bbox_leste)s, %(bbox_oeste)s,
     %(centro_lat)s, %(centro_lon)s,
     %(objetivo)s, %(responsavel)s, %(data_inicio)s, %(data_fim)s, %(status)s)
"""


def seed_projetos(*, skip_if_exists: bool = True) -> int:
    """
    Insert seed projects into the database.

    Parameters
    ----------
    skip_if_exists : bool
        When True, skip seeding if the table already has rows.

    Returns
    -------
    int
        Number of rows inserted.
    """
    if skip_if_exists:
        result = execute_query(
            "SELECT COUNT(*) AS total FROM projetos", fetch_one=True
        )
        if result and result.get("total", 0) > 0:
            logger.info(
                "projetos table already has %d rows — skipping seed.",
                result["total"],
            )
            return 0

    inserted = 0
    for proj in PROJETOS_SEED:
        execute_query(INSERT_SQL, tuple(proj.values()), commit=True)
        inserted += 1

    logger.info("Seeded %d projects into projetos.", inserted)
    return inserted


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
    )

    logger.info("Ensuring database schema exists ...")
    init_database()

    logger.info("Seeding projetos ...")
    count = seed_projetos()
    if count:
        logger.info("Done — inserted %d projects.", count)
    else:
        logger.info("No new rows inserted (table already populated).")


if __name__ == "__main__":
    main()
