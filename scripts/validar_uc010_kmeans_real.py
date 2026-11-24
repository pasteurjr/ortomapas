"""Reproducible functional and repeatability audit of UC-010 on UAV orthos.

This script does not claim semantic accuracy. It uses two real campaign
orthomosaics, runs the production segmentation implementation on the same
geographic window, repeats each run, and records deterministic output checks.
An independent labelled reference is still required to score semantic classes.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.windows import Window

from backend.tools.segmentation import segment_ortomapa

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "2022": ROOT / "data/validacao/uc009_aklavik/2022_ortomosaico.tif",
    "2024": ROOT / "data/validacao/uc009_aklavik/2024_ortomosaico.tif",
}
OUTPUT = ROOT / "docs/validacao/ortomapas_conclusao/etapa-10/uc010_semantic_quality"
WINDOW_SIZE = 768
CLUSTERS = 5


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_crop(source: Path, target: Path) -> dict:
    with rasterio.open(source) as src:
        if src.count < 3 or src.crs is None or not src.crs.is_projected:
            raise AssertionError(f"Fonte não é ortomosaico RGB projetado: {source}")
        if src.width < WINDOW_SIZE or src.height < WINDOW_SIZE:
            raise AssertionError(f"Fonte menor que a janela de auditoria: {source}")
        window = Window(int(src.width * 0.65), (src.height - WINDOW_SIZE) // 2,
                        WINDOW_SIZE, WINDOW_SIZE)
        profile = src.profile.copy()
        profile.update(width=WINDOW_SIZE, height=WINDOW_SIZE,
                       transform=rasterio.windows.transform(window, src.transform),
                       count=3, compress="lzw")
        with rasterio.open(target, "w", **profile) as dst:
            dst.write(src.read((1, 2, 3), window=window))
        return {"width": WINDOW_SIZE, "height": WINDOW_SIZE,
                "crs": src.crs.to_string(), "window": [int(window.col_off), int(window.row_off),
                                                          WINDOW_SIZE, WINDOW_SIZE],
                "bounds": list(rasterio.windows.bounds(window, src.transform)),
                "source_bytes": source.stat().st_size, "source_sha256": sha256(source)}


def run_campaign(label: str, source: Path, temp: Path) -> tuple[dict, np.ndarray, np.ndarray]:
    crop = temp / f"aklavik_{label}_crop.tif"
    first = temp / f"aklavik_{label}_classes_1.tif"
    second = temp / f"aklavik_{label}_classes_2.tif"
    crop_info = make_crop(source, crop)
    first_result = segment_ortomapa(str(crop), str(first), n_clusters=CLUSTERS)
    second_result = segment_ortomapa(str(crop), str(second), n_clusters=CLUSTERS)
    with rasterio.open(crop) as image, rasterio.open(first) as out1, rasterio.open(second) as out2:
        rgb = np.moveaxis(image.read((1, 2, 3)), 0, -1)
        labels1, labels2 = out1.read(1), out2.read(1)
        if out1.crs != image.crs or out1.transform != image.transform:
            raise AssertionError(f"{label}: resultado não preservou georreferenciamento")
        if not np.array_equal(labels1, labels2):
            raise AssertionError(f"{label}: K-Means não repetiu a mesma classificação")
        unique, counts = np.unique(labels1, return_counts=True)
        if unique.tolist() != list(range(1, CLUSTERS + 1)):
            raise AssertionError(f"{label}: esperados grupos 1..{CLUSTERS}, obtido {unique.tolist()}")
        if first_result["sample_pixels"] != min(WINDOW_SIZE**2, 100_000):
            raise AssertionError(f"{label}: número de amostras divergente")
        if first_result["total_valid_pixels"] != WINDOW_SIZE**2:
            raise AssertionError(f"{label}: contagem de pixels válidos divergente")
        expected_pixel_area = abs(image.transform.a * image.transform.e -
                                  image.transform.b * image.transform.d)
        if sum(item["pixel_count"] for item in first_result["clusters"]) != WINDOW_SIZE**2:
            raise AssertionError(f"{label}: contagens por grupo não cobrem todos os pixels")
        if abs(sum(item["percent"] for item in first_result["clusters"]) - 100.0) > 0.001:
            raise AssertionError(f"{label}: percentuais dos grupos não somam 100%")
        for item in first_result["clusters"]:
            if abs(item["area_m2"] - item["pixel_count"] * expected_pixel_area) > 0.011:
                raise AssertionError(f"{label}: área do grupo {item['cluster']} não confere com a grade")
        campaign = {
            "crop": crop_info,
            "n_clusters": first_result["n_clusters"],
            "total_valid_pixels": first_result["total_valid_pixels"],
            "sample_pixels": first_result["sample_pixels"],
            "clusters": first_result["clusters"],
            "repeat_run_pixel_agreement_percent": 100.0,
            "crs_preserved": True,
            "exactly_five_labels_1_to_5": True,
            "semantic_accuracy": None,
            "semantic_accuracy_reason": "não existe máscara independente rotulada disponível para esta cena",
        }
        return campaign, rgb, labels1


def render(campaigns: dict, visuals: dict) -> Path:
    colors = np.array([[35, 180, 95], [244, 180, 0], [70, 120, 220],
                       [220, 70, 65], [170, 90, 200]], dtype=np.uint8)
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.subplots_adjust(top=.91, bottom=.06, left=.03, right=.98, hspace=.14, wspace=.04)
    for row, year in enumerate(("2022", "2024")):
        rgb, labels = visuals[year]
        axes[row, 0].imshow(rgb)
        axes[row, 0].set_title(f"Aklavik {year} — recorte RGB real (768 × 768 px)")
        axes[row, 1].imshow(colors[np.clip(labels.astype(int) - 1, 0, len(colors) - 1)])
        axes[row, 1].set_title(f"K-Means RGB — 5 grupos (IDs sem semântica)")
        for ax in axes[row]:
            ax.set_axis_off()
    fig.suptitle("UC-010 | Execução funcional e repetibilidade em ortomosaicos UAV", fontsize=17)
    fig.text(.5, .018,
             "Cores representam apenas grupos de similaridade RGB; não identificam automaticamente classes de cobertura.",
             ha="center", fontsize=10)
    target = OUTPUT / "01_ortos_reais_e_grupos_kmeans.png"
    fig.savefig(target, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return target


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="uc010-kmeans-") as temp_dir:
        campaigns = {}
        visuals = {}
        for year, source in SOURCES.items():
            if not source.is_file():
                raise FileNotFoundError(f"Ortomosaico da campanha {year} ausente: {source}")
            result, rgb, labels = run_campaign(year, source, Path(temp_dir))
            campaigns[year] = result
            visuals[year] = (rgb, labels)
    figure = render(campaigns, visuals)
    manifest = {
        "validation": "UC-010 K-Means RGB functional/repeatability audit",
        "generated_utc": "2026-11-24",
        "method": "production segment_ortomapa on 768x768 windows at 65% image width and vertical center from two real UAV orthomosaics; two identical runs each",
        "results": campaigns,
        "visual_evidence": figure.relative_to(ROOT).as_posix(),
        "semantic_acceptance": "PARTIAL — no independently labelled reference mask was available; RGB clusters are not semantic classes",
        "external_reference_attempt": "LandCover.ai direct HTTPS download failed because DNS resolution was unavailable in the session",
    }
    target = OUTPUT / "manifest.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(target.relative_to(ROOT)), "figure": str(figure.relative_to(ROOT)),
                      "status": manifest["semantic_acceptance"],
                      "campaigns": {year: {"valid_pixels": item["total_valid_pixels"],
                                           "sample_pixels": item["sample_pixels"],
                                           "agreement": item["repeat_run_pixel_agreement_percent"]}
                                    for year, item in campaigns.items()}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
