"""Optional lifecycle helpers for the EXISTING Folium map, pending Opus integration.

No rendering, model changes, persistence or dependencies. Call reset_proposal after
a successful save or explicit undo, then st.rerun() BEFORE rebuilding the map and
metrics. Pass map_component_key to the existing st_folium call. Both changes must
be integrated together so a previous component's last_clicked is not replayed.
"""
from collections.abc import MutableMapping
from typing import Any


def map_component_key(barrio: str, state: MutableMapping[str, Any]) -> str:
    """Namespace component events by neighbourhood and proposal generation."""
    return f"astra-map:{barrio}:{state.get('astra_map_revision', 0)}"


def reset_proposal(state: MutableMapping[str, Any]) -> None:
    """Clear only transient proposal fields, leaving voter/parameters untouched."""
    state.update(
        new_benches=[],
        new_trees=[],
        last_click=None,
        astra_map_revision=state.get("astra_map_revision", 0) + 1,
    )
