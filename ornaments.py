"""Decorative SVG leaf sprigs (Central Park–style greens) as CSS data URIs."""

import math
from urllib.parse import quote

GREENS = ["#286140", "#1E9B18", "#79C000", "#C8E379"]


def _sprig(n_leaves: int, length: float, seed: int) -> str:
    """A curved stem with alternating almond-shaped leaves, drawn along a quadratic curve."""
    w, h = 320, 320
    p0, p1, p2 = (20, h - 20), (w * 0.15, h * 0.25), (w - 30, 30)
    parts = [f'<path d="M{p0[0]},{p0[1]} Q{p1[0]},{p1[1]} {p2[0]},{p2[1]}" stroke="#286140" '
             f'stroke-width="3" fill="none" stroke-linecap="round"/>']
    for i in range(n_leaves):
        t = 0.12 + 0.82 * i / max(n_leaves - 1, 1)
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
        dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
        angle = math.degrees(math.atan2(dy, dx)) + (55 if i % 2 else -55)
        size = length * (1.1 - 0.5 * t)
        color = GREENS[(i + seed) % len(GREENS)]
        parts.append(
            f'<g transform="translate({x:.1f},{y:.1f}) rotate({angle:.1f})">'
            f'<path d="M0,0 C{size * .35:.1f},{-size * .28:.1f} {size * .75:.1f},{-size * .22:.1f} {size:.1f},0 '
            f'C{size * .75:.1f},{size * .22:.1f} {size * .35:.1f},{size * .28:.1f} 0,0Z" fill="{color}"/>'
            f'<path d="M2,0 L{size * .9:.1f},0" stroke="#FFFFFF" stroke-opacity=".35" stroke-width="1.2"/></g>'
        )
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">{"".join(parts)}</svg>'
    return "data:image/svg+xml," + quote(svg)


SPRIG_A = _sprig(9, 70, 0)
SPRIG_B = _sprig(7, 60, 2)
