"""Coverage model: estimated elderly residents within R metres of a bench."""

import numpy as np

M_PER_DEG_LAT = 111_320.0


def _to_metres(lat: np.ndarray, lon: np.ndarray, lat0: float) -> tuple[np.ndarray, np.ndarray]:
    """Equirectangular projection around lat0 (accurate enough at city scale)."""
    x = np.asarray(lon) * M_PER_DEG_LAT * np.cos(np.radians(lat0))
    y = np.asarray(lat) * M_PER_DEG_LAT
    return x, y


def polygon_centroid_area(ring: list[list[float]], lat0: float) -> tuple[float, float, float]:
    """Return (lat, lon, area_m2) of a polygon ring given as [lon, lat] pairs."""
    pts = np.asarray(ring)
    x, y = _to_metres(pts[:, 1], pts[:, 0], lat0)
    area = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    return float(pts[:, 1].mean()), float(pts[:, 0].mean()), float(area)


def blocks_from_features(features: list[dict], lat0: float) -> list[dict]:
    """Centroid and area of each city block (manzana)."""
    blocks = []
    for f in features:
        g = f["geometry"]
        ring = g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0]
        lat, lon, area = polygon_centroid_area(ring, lat0)
        blocks.append({"lat": lat, "lon": lon, "area": area})
    return blocks


def estimate_population(blocks: list[dict], mean_residents: float, pct_elderly: float) -> np.ndarray:
    """ESTIMATE: residents scale with block area around a mean; returns elderly per block."""
    areas = np.array([b["area"] for b in blocks])
    if areas.size == 0 or areas.mean() == 0:
        return np.zeros(len(blocks))
    return mean_residents * areas / areas.mean() * pct_elderly / 100


def covered_mask(blocks: list[dict], benches: list[tuple[float, float]], radius_m: float, lat0: float) -> np.ndarray:
    """True for each block whose centroid is within radius_m of any bench."""
    if not blocks or not benches:
        return np.zeros(len(blocks), dtype=bool)
    bx, by = _to_metres(np.array([b["lat"] for b in blocks]), np.array([b["lon"] for b in blocks]), lat0)
    sx, sy = _to_metres(np.array([s[0] for s in benches]), np.array([s[1] for s in benches]), lat0)
    dist = np.hypot(bx[:, None] - sx[None, :], by[:, None] - sy[None, :])
    return (dist <= radius_m).any(axis=1)


def coverage(blocks, elderly, benches, radius_m, lat0) -> float:
    """Estimated elderly residents covered by benches."""
    return float(elderly[covered_mask(blocks, benches, radius_m, lat0)].sum())


def green_space_points(parks: list[dict], min_area_m2: float) -> list[tuple[float, float]]:
    """Vertices (lat, lon) of parks at least min_area_m2 big; distance to them approximates distance to the park."""
    points = []
    for f in parks:
        if (f["properties"].get("sup_total") or 0) < min_area_m2:
            continue
        g = f["geometry"]
        for poly in [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]:
            points += [(lat, lon) for lon, lat in poly[0]]
    return points
