"""Download and cache open data layers from the València geoportal (ArcGIS REST)."""

import json
from pathlib import Path

import requests

BASE = "https://geoportal.valencia.es/server/rest/services/OPENDATA"
LAYERS = {
    "barrios": "UrbanismoEInfraestructuras/MapServer/224",
    "bancos": "SociedadBienestar/MapServer/32",
    "arboles": "MedioAmbiente/MapServer/151",
    "parques": "MedioAmbiente/MapServer/8",
    "manzanas": "UrbanismoEInfraestructuras/MapServer/215",
}
CACHE_DIR = Path(__file__).parent / "data" / "cache"
PAGE_SIZE = 1000


def _query(layer: str, extra: dict) -> list[dict]:
    """Run a paginated geojson query and return all features (WGS84)."""
    url = f"{BASE}/{LAYERS[layer]}/query"
    features, offset = [], 0
    while True:
        params = {
            "where": "1=1",
            "outFields": "*",
            "outSR": 4326,
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": PAGE_SIZE,
            **extra,
        }
        resp = requests.post(url, data=params, timeout=60)
        resp.raise_for_status()
        page = resp.json().get("features", [])
        features += [f for f in page if f.get("geometry")]
        if len(page) < PAGE_SIZE:
            return features
        offset += PAGE_SIZE


def _cached(name: str, fetch) -> list[dict]:
    path = CACHE_DIR / f"{name}.geojson"
    if path.exists():
        return json.loads(path.read_text())["features"]
    features = fetch()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    return features


def load_barrios() -> list[dict]:
    """All 88 neighbourhood polygons."""
    return _cached("barrios", lambda: _query("barrios", {}))


def load_layer_in_barrio(layer: str, barrio: dict) -> list[dict]:
    """Features of `layer` intersecting the given neighbourhood polygon."""
    geom = barrio["geometry"]
    rings = geom["coordinates"] if geom["type"] == "Polygon" else [r for p in geom["coordinates"] for r in p]
    esri_polygon = {"rings": rings, "spatialReference": {"wkid": 4326}}
    extra = {
        "geometry": json.dumps(esri_polygon),
        "geometryType": "esriGeometryPolygon",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
    }
    code = barrio["properties"]["coddistbar"]
    return _cached(f"{layer}_{code}", lambda: _query(layer, extra))
