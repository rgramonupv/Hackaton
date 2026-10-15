"""València Futura — propose neighbourhood reforms with measured impact, then vote."""

import folium
import streamlit as st
from streamlit_folium import st_folium

import data
import db
import model

st.set_page_config(page_title="València Futura", page_icon="🏙️", layout="wide")
NEIGHBOURS = ["Ana", "Luis", "Marta", "Pepe"]


@st.cache_data(show_spinner="Descargando datos del geoportal municipal…")
def load_barrio(name: str) -> dict:
    barrio = next(b for b in data.load_barrios() if b["properties"]["nombre"] == name)
    return {
        "barrio": barrio,
        "bancos": [tuple(reversed(f["geometry"]["coordinates"][:2])) for f in data.load_layer_in_barrio("bancos", barrio)],
        "arboles": [tuple(reversed(f["geometry"]["coordinates"][:2])) for f in data.load_layer_in_barrio("arboles", barrio)],
        "parques": data.load_layer_in_barrio("parques", barrio),
        "manzanas": data.load_layer_in_barrio("manzanas", barrio),
    }


def barrio_center(barrio: dict) -> tuple[float, float]:
    g = barrio["geometry"]
    ring = g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"][0][0]
    return sum(p[1] for p in ring) / len(ring), sum(p[0] for p in ring) / len(ring)


# --- Sidebar: neighbourhood, neighbour and decision variables -------------------------
barrio_names = sorted(b["properties"]["nombre"] for b in data.load_barrios())
with st.sidebar:
    st.title("🏙️ València Futura")
    barrio_name = st.selectbox("Barrio", barrio_names, index=barrio_names.index("RUSSAFA"))
    voter = st.selectbox("Soy el vecino/a", NEIGHBOURS)
    st.subheader("Variables de decisión")
    radius = st.slider("Radio de cobertura de un banco (m)", 25, 300, 75, 25)
    cost_bench = st.number_input("Coste por banco (€)", 100, 5000, 800, 50)
    cost_tree = st.number_input("Coste por árbol (€)", 100, 5000, 400, 50)
    st.caption("Población — **estimación** (el geoportal no publica edades por manzana)")
    mean_residents = st.slider("Habitantes medios por manzana", 20, 500, 150, 10)
    pct_elderly = st.slider("% de mayores de 65 años", 5, 40, 22)

d = load_barrio(barrio_name)
lat0, lon0 = barrio_center(d["barrio"])
blocks = model.blocks_from_features(d["manzanas"], lat0)
elderly = model.estimate_population(blocks, mean_residents, pct_elderly)

state = st.session_state
if state.get("barrio") != barrio_name:
    state.update(barrio=barrio_name, new_benches=[], new_trees=[], last_click=None)

tab_sim, tab_vote = st.tabs(["🛠️ Simulador", "🗳️ Votación"])

# --- Simulator ------------------------------------------------------------------------
with tab_sim:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bancos existentes", len(d["bancos"]))
    c2.metric("Árboles existentes", len(d["arboles"]))
    c3.metric("Parques y jardines", len(d["parques"]))
    c4.metric("Manzanas", len(blocks))

    all_benches = d["bancos"] + state.new_benches
    before = model.coverage(blocks, elderly, d["bancos"], radius, lat0)
    after = model.coverage(blocks, elderly, all_benches, radius, lat0)
    cost = len(state.new_benches) * cost_bench + len(state.new_trees) * cost_tree
    gained = after - before

    left, right = st.columns([3, 1])
    with right:
        mode = st.radio("Al hacer clic en el mapa añado…", ["🪑 Banco", "🌳 Árbol"])
        st.metric("Mayores a ≤ %d m de un banco" % radius, f"{after:,.0f}", f"{gained:+,.0f}")
        st.caption(f"de {elderly.sum():,.0f} mayores estimados en el barrio")
        st.metric("Coste de la propuesta", f"{cost:,.0f} €")
        st.metric("€ por mayor beneficiado", f"{cost / gained:,.0f} €" if gained > 0 else "—")
        st.write(f"Nuevos: {len(state.new_benches)} bancos · {len(state.new_trees)} árboles")
        if st.button("↩️ Deshacer todo"):
            state.update(new_benches=[], new_trees=[])
            st.rerun()
        with st.form("save"):
            title = st.text_input("Título de la propuesta")
            if st.form_submit_button("📤 Publicar para votación", disabled=not (state.new_benches or state.new_trees)):
                db.save_proposal(
                    barrio_name, title or "Propuesta sin título", voter, state.new_benches, state.new_trees,
                    cost, before, after,
                    {"radius": radius, "mean_residents": mean_residents, "pct_elderly": pct_elderly},
                )
                state.update(new_benches=[], new_trees=[])
                st.success("Propuesta publicada. Ve a la pestaña Votación.")

    with left:
        m = folium.Map(location=[lat0, lon0], zoom_start=16, tiles="OpenStreetMap")
        folium.GeoJson(d["barrio"], style_function=lambda _: {"color": "#333", "fill": False, "weight": 2}).add_to(m)
        for p in d["parques"]:
            folium.GeoJson(p, style_function=lambda _: {"color": "#2e7d32", "fillOpacity": 0.35, "weight": 1},
                           tooltip=p["properties"].get("nombre")).add_to(m)
        covered = model.covered_mask(blocks, all_benches, radius, lat0)
        for f, ok, e in zip(d["manzanas"], covered, elderly):
            folium.GeoJson(f, style_function=lambda _, ok=ok: {
                "color": "#999", "weight": 0.5, "fillColor": "#cfd8dc" if ok else "#e53935", "fillOpacity": 0.45},
                tooltip=f"{e:.0f} mayores (est.) · {'cubierta' if ok else 'SIN banco cerca'}").add_to(m)
        for lat, lon in d["arboles"]:
            folium.CircleMarker([lat, lon], radius=2, color="#43a047", fill=True, weight=0).add_to(m)
        for lat, lon in d["bancos"]:
            folium.CircleMarker([lat, lon], radius=3, color="#1e88e5", fill=True, fill_opacity=1, weight=0).add_to(m)
        for lat, lon in state.new_benches:
            folium.Marker([lat, lon], icon=folium.Icon(color="orange", icon="plus"), tooltip="Banco nuevo").add_to(m)
        for lat, lon in state.new_trees:
            folium.Marker([lat, lon], icon=folium.Icon(color="green", icon="leaf"), tooltip="Árbol nuevo").add_to(m)

        out = st_folium(m, key="map", height=620, use_container_width=True, returned_objects=["last_clicked"])
        st.caption("🔵 banco existente · 🟢 árbol existente · zona verde = parque · 🟥 manzana sin banco a ≤ R m · 🟧 propuesta")
        click = (out or {}).get("last_clicked")
        if click and click != state.last_click:
            state.last_click = click
            point = (click["lat"], click["lng"])
            (state.new_benches if mode.startswith("🪑") else state.new_trees).append(point)
            st.rerun()

# --- Voting ---------------------------------------------------------------------------
with tab_vote:
    st.subheader(f"Propuestas para {barrio_name}")
    st.caption(f"Votando como **{voter}** · un voto por vecino y propuesta · cifras de población estimadas")
    proposals = db.ranking(barrio_name)
    if not proposals:
        st.info("Aún no hay propuestas. Crea una en el Simulador.")
    for i, p in enumerate(proposals, 1):
        gain = p["elderly_after"] - p["elderly_before"]
        with st.container(border=True):
            a, b, c, e, f = st.columns([3, 1, 1, 1, 1])
            a.markdown(f"**#{i} {p['title']}**  \npor {p['author']}")
            b.metric("Votos", p["votes"])
            c.metric("Coste", f"{p['cost']:,.0f} €")
            e.metric("Mayores ganados", f"{gain:+,.0f}")
            f.metric("€ / beneficiado", f"{p['cost'] / gain:,.0f}" if gain > 0 else "—")
            if st.button(f"👍 Votar como {voter}", key=f"vote_{p['id']}"):
                st.toast("Voto registrado" if db.vote(p["id"], voter) else f"{voter} ya había votado esta propuesta")
                st.rerun()
