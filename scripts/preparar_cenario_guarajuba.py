"""Converte o recorte OSM de Guarajuba em camadas GeoJSON para demonstracao."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from shapely.geometry import Polygon, mapping

ROOT = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/guarajuba_osm.osm"
output = ROOT / "data/guarajuba_osm_referencia.geojson"
aoi_output = ROOT / "data/guarajuba_condominio_paraiso_aoi.geojson"
tree = ET.parse(source)
nodes = {element.attrib["id"]: (float(element.attrib["lon"]), float(element.attrib["lat"])) for element in tree.findall("node")}
features = []
for way in tree.findall("way"):
    tags = {tag.attrib.get("k"): tag.attrib.get("v") for tag in way.findall("tag")}
    refs = [nd.attrib["ref"] for nd in way.findall("nd")]
    coords = [nodes[ref] for ref in refs if ref in nodes]
    if len(coords) < 2 or not any(key in tags for key in ("building", "highway", "leisure", "landuse")):
        continue
    is_area = coords[0] == coords[-1] and len(coords) >= 4
    geometry = {"type": "Polygon", "coordinates": [coords]} if is_area else {"type": "LineString", "coordinates": coords}
    features.append({"type": "Feature", "id": way.attrib.get("id"), "properties": {key: value for key, value in tags.items() if key in {"building", "highway", "leisure", "landuse", "name"}}, "geometry": geometry})

# AOI aproximada para teste; nao representa limite cadastral oficial.
aoi = Polygon([(-38.0758, -12.6538), (-38.0680, -12.6538), (-38.0680, -12.6470), (-38.0758, -12.6470), (-38.0758, -12.6538)])
features.append({"type": "Feature", "properties": {"tipo": "AOI_TESTE", "nome": "Condominio Paraiso - AOI aproximada", "observacao": "Confirmar com levantamento cadastral antes de uso operacional."}, "geometry": mapping(aoi)})
collection = {"type": "FeatureCollection", "name": "Guarajuba_Condominio_Paraiso_Demonstracao", "crs": {"type": "name", "properties": {"name": "EPSG:4326"}}, "features": features}
output.write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")
aoi_output.write_text(json.dumps({"type": "Feature", "properties": {"tipo": "AOI_TESTE", "nome": "Condominio Paraiso - AOI aproximada"}, "geometry": mapping(aoi)}, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"source": str(source), "output": str(output), "aoi_output": str(aoi_output), "features": len(features), "aoi": "-12.6538,-38.0758 / -12.6470,-38.0680"}, ensure_ascii=False))
