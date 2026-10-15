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
PAGE_SIZE = 500


def _query(layer: str, extra: dict) -> list[dict]:
    """Fetch all matching features (WGS84): ask for the object ids first, then download them in batches.

    Offset paging is unreliable on this server (short pages, unstable order, duplicates)."""
    url = f"{BASE}/{LAYERS[layer]}/query"
    resp = requests.post(url, data={"where": "1=1", "returnIdsOnly": "true", "f": "json", **extra}, timeout=60)
    resp.raise_for_status()
    ids = sorted(resp.json().get("objectIds") or [])
    features = []
    for i in range(0, len(ids), PAGE_SIZE):
        params = {"objectIds": ",".join(map(str, ids[i:i + PAGE_SIZE])), "outFields": "*", "outSR": 4326,
                  "f": "geojson"}
        page = requests.post(url, data=params, timeout=60)
        page.raise_for_status()
        features += [f for f in page.json().get("features", []) if f.get("geometry")]
    return features

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


def normalize_barrio(name: str | None) -> str:
    """'121 - AIORA' / 'Aiora' -> 'AIORA' so layers with different barrio formats can be joined."""
    import unicodedata

    if not isinstance(name, str) or not name:
        return ""
    name = name.split(" - ", 1)[-1].strip().upper()
    return "".join(c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn")


def group_stats(layer: str, group_field: str, stats: list[tuple[str, str, str]]) -> list[dict]:
    """Server-side GROUP BY on a layer: stats = [(type, field, out_name)], e.g. ("count", "objectid", "n")."""
    def fetch():
        out = [{"statisticType": t, "onStatisticField": f, "outStatisticFieldName": o} for t, f, o in stats]
        resp = requests.post(f"{BASE}/{LAYERS[layer]}/query", data={
            "where": "1=1", "groupByFieldsForStatistics": group_field,
            "outStatistics": json.dumps(out), "f": "json"}, timeout=60)
        resp.raise_for_status()
        return [{"type": "Feature", "geometry": None, "properties": f["attributes"]} for f in resp.json()["features"]]
    name = f"stats_{layer}_{group_field}_" + "_".join(o for _, _, o in stats)
    return [f["properties"] for f in _cached(name, fetch)]


def load_all_parks() -> list[dict]:
    """All 807 municipal green spaces (polygons)."""
    return _cached("parques_all", lambda: _query("parques", {}))


VULNERABILITY_CSV = ("https://opendata.vlci.valencia.es/dataset/ca18278b-d040-4274-b9c7-c1a9daae54b9/resource/"
                     "6648d1d5-4d35-410d-8260-432069045334/download/vulnerabilidad-por-barrios.csv")
CITY_PCT_ELDERLY, CITY_PCT_CHILDREN = 22.0, 13.0


def age_estimates() -> dict[str, tuple[float, float, bool]]:
    """ESTIMATE per barrio: (% aged 65+, % under 15, from_index) keyed by normalize_barrio(name).

    The council publishes no ages per barrio, but it does publish a demographic vulnerability index (2021,
    lower = more vulnerable, i.e. older population). We scale the city averages by that index; barrios
    without an index get the city average."""
    import pandas as pd

    path = CACHE_DIR / "vulnerabilidad_barrios.csv"
    if not path.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_bytes(requests.get(VULNERABILITY_CSV, timeout=60).content)
    v = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    mean = v["Ind_Dem"].mean()
    out = {}
    for name, idx in zip(v["Nombre"], v["Ind_Dem"]):
        elderly = min(max(CITY_PCT_ELDERLY * mean / idx, 12), 32)
        children = min(max(CITY_PCT_CHILDREN * idx / mean, 8), 18)
        out[normalize_barrio(name)] = (round(elderly), round(children), True)
    return out
