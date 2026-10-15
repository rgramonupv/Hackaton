"""'València verde' tab: city-wide green data from the municipal geoportal, interactive."""

import altair as alt
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import data
import model

GREEN, HIGHLIGHT = "#257422", "#FC992F"


def _area_m2(barrio: dict) -> float:
    """Polygon area; the geoportal leaves the area field empty for some barrios."""
    g = barrio["geometry"]
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    return sum(model.polygon_centroid_area(p[0], 39.47)[2] for p in polys)


@st.cache_data(show_spinner="Calculando los datos verdes de toda la ciudad…")
def city_table() -> pd.DataFrame:
    """One row per barrio: trees, benches, green m², area and green m² per hectare (all real data)."""
    barrios = data.load_barrios()
    df = pd.DataFrame({
        "barrio": [b["properties"]["nombre"] for b in barrios],
        "key": [data.normalize_barrio(b["properties"]["nombre"]) for b in barrios],
        "area_ha": [_area_m2(b) / 10_000 for b in barrios],
    })
    trees = pd.DataFrame(data.group_stats("arboles", "barrio", [("count", "objectid", "n")]))
    trees["key"] = trees["barrio"].map(data.normalize_barrio)
    benches = pd.DataFrame(data.group_stats("bancos", "barrio", [("count", "gid", "n")]))
    benches["key"] = benches["barrio"].map(data.normalize_barrio)
    df["arboles"] = df["key"].map(trees.groupby("key")["n"].sum()).fillna(0).astype(int)
    df["bancos"] = df["key"].map(benches.groupby("key")["n"].sum()).fillna(0).astype(int)

    green = dict.fromkeys(df["barrio"], 0.0)
    for p in data.load_all_parks():
        g = p["geometry"]
        ring = g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0]
        lat, lon = sum(q[1] for q in ring) / len(ring), sum(q[0] for q in ring) / len(ring)
        for b in barrios:
            if model.point_in_polygon(lat, lon, b["geometry"]):
                green[b["properties"]["nombre"]] += p["properties"].get("sup_total") or 0
                break
    df["zona_verde_m2"] = df["barrio"].map(green)
    df["m2_verde_por_ha"] = df["zona_verde_m2"] / df["area_ha"]
    df["arboles_por_ha"] = df["arboles"] / df["area_ha"]
    return df.drop(columns="key")


@st.cache_data
def species_table(top: int = 10) -> pd.DataFrame:
    rows = data.group_stats("arboles", "nom_comu_c", [("count", "objectid", "n")])
    df = pd.DataFrame(rows).rename(columns={"nom_comu_c": "especie"}).dropna()
    return df.sort_values("n", ascending=False).head(top)


def species_chart(sp: pd.DataFrame) -> alt.Chart:
    """Horizontal bars of the most planted species, with hover tooltips."""
    return alt.Chart(sp).mark_bar(cornerRadiusEnd=4, height=14, color=GREEN).encode(
        y=alt.Y("especie:N", sort="-x", title=None),
        x=alt.X("n:Q", title="Árboles", axis=alt.Axis(grid=True, gridOpacity=0.3)),
        tooltip=[alt.Tooltip("especie:N", title="Especie"), alt.Tooltip("n:Q", title="Árboles", format=",.0f")],
    ).properties(height=alt.Step(22))


def fmt(n: float) -> str:
    return f"{n:,.0f}".replace(",", ".")


def ranked_bar(df: pd.DataFrame, field: str, title: str, barrio: str, top: int = 15) -> alt.Chart:
    """Top-N barrios by `field`, plus the selected barrio (highlighted and direct-labelled) if outside the top."""
    ranked = df.sort_values(field, ascending=False).reset_index(drop=True)
    ranked["puesto"] = ranked.index + 1
    shown = pd.concat([ranked.head(top), ranked[ranked["barrio"] == barrio]]).drop_duplicates("barrio")
    shown["nombre"] = shown["puesto"].astype(str) + ". " + shown["barrio"].str.title()
    shown["tuyo"] = shown["barrio"] == barrio
    base = alt.Chart(shown).encode(
        y=alt.Y("nombre:N", sort=alt.SortField("puesto"), title=None),
        x=alt.X(f"{field}:Q", title=title, axis=alt.Axis(grid=True, gridOpacity=0.3)),
    )
    bars = base.mark_bar(cornerRadiusEnd=4, height=14).encode(
        color=alt.condition("datum.tuyo", alt.value(HIGHLIGHT), alt.value(GREEN)),
        tooltip=[alt.Tooltip("barrio:N", title="Barrio"), alt.Tooltip(f"{field}:Q", title=title, format=",.0f"),
                 alt.Tooltip("puesto:Q", title="Puesto de 88")],
    )
    label = base.transform_filter("datum.tuyo").mark_text(align="left", dx=6, color="#133A24").encode(
        text=alt.Text(f"{field}:Q", format=",.0f"))
    return (bars + label).properties(height=alt.Step(22))


def render(barrio: str) -> None:
    df = city_table()
    me = df[df["barrio"] == barrio].iloc[0]
    rank_trees = int((df["arboles"] > me["arboles"]).sum()) + 1
    rank_green = int((df["m2_verde_por_ha"] > me["m2_verde_por_ha"]).sum()) + 1

    st.markdown(
        f"""<div class="stats">
<div><b>{fmt(df['arboles'].sum())}</b><span>árboles en la ciudad</span></div>
<div><b>{fmt(df['zona_verde_m2'].sum() / 10_000)}</b><span>hectáreas de parques y jardines</span></div>
<div><b>{fmt(len(data.load_all_parks()))}</b><span>zonas verdes</span></div>
<div><b>{fmt(df['bancos'].sum())}</b><span>bancos</span></div></div>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"**{barrio.title()}** tiene {fmt(me['arboles'])} árboles (puesto {rank_trees} de {len(df)}) y "
        f"{fmt(me['m2_verde_por_ha'])} m² de zona verde por hectárea (puesto {rank_green}; "
        f"la mediana de la ciudad es {fmt(df['m2_verde_por_ha'].median())})."
    )

    metric = st.segmented_control(
        "Colorea el mapa por", ["Zona verde por hectárea", "Árboles por hectárea"], default="Zona verde por hectárea")
    field = "arboles_por_ha" if metric == "Árboles por hectárea" else "m2_verde_por_ha"
    unit = "árboles/ha" if field == "arboles_por_ha" else "m² verdes/ha"

    left, right = st.columns([3, 2], gap="large")
    with left:
        barrios = data.load_barrios()
        values = dict(zip(df["barrio"], df[field]))
        m = folium.Map(location=[39.47, -0.376], zoom_start=12, tiles="OpenStreetMap")
        geo = {"type": "FeatureCollection", "features": [
            {**b, "properties": {**b["properties"], "valor": round(values[b["properties"]["nombre"]], 1)}}
            for b in barrios]}
        folium.Choropleth(geo, data=df, columns=["barrio", field], key_on="feature.properties.nombre",
                          fill_color="Greens", fill_opacity=0.75, line_opacity=0.4, legend_name=unit,
                          nan_fill_color="#FFFFFF").add_to(m)
        folium.GeoJson(geo, style_function=lambda f: {
            "fill": False, "weight": 4 if f["properties"]["nombre"] == barrio else 0, "color": HIGHLIGHT},
            tooltip=folium.GeoJsonTooltip(["nombre", "valor"], aliases=["Barrio", unit])).add_to(m)
        st_folium(m, key=f"green_map_{field}", height=520, use_container_width=True, returned_objects=[])
        st.caption("Datos: geoportal del Ayuntamiento (arbolado, espacios verdes, barrios). "
                   "Cada parque se asigna al barrio donde cae su centro.")
    with right:
        st.altair_chart(ranked_bar(df, field, unit, barrio), use_container_width=True)

    st.markdown("#### Especies más plantadas en la ciudad")
    st.altair_chart(species_chart(species_table()), use_container_width=True)
    with st.expander("Ver la tabla de todos los barrios"):
        st.dataframe(
            df.sort_values(field, ascending=False).rename(columns={
                "barrio": "Barrio", "area_ha": "Superficie (ha)", "arboles": "Árboles", "bancos": "Bancos",
                "zona_verde_m2": "Zona verde (m²)", "m2_verde_por_ha": "m² verdes/ha", "arboles_por_ha": "Árboles/ha"}),
            hide_index=True, use_container_width=True,
            column_config={c: st.column_config.NumberColumn(format="%.0f") for c in
                           ["Superficie (ha)", "Zona verde (m²)", "m² verdes/ha", "Árboles/ha"]},
        )
