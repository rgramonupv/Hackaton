"""València Futura — propose neighbourhood reforms with measured impact, then vote."""

import html

import folium
import streamlit as st
from streamlit_folium import st_folium

import data
import db
import model

st.set_page_config(page_title="València Futura", page_icon="🌿", layout="wide")

# Huerta valenciana palette: huerta green, orange-tree orange, acequia blue, earth ochre, whitewash.
COLORS = {
    "huerta": "#2F5D3A",
    "naranja": "#E07B24",
    "acequia": "#2C6A86",
    "tierra": "#9A6B34",
    "hoja": "#5E8C3A",
    "cal": "#F6F7F2",
    "tinta": "#1F2A23",
    "covered": "#CFE0C3",
}

st.markdown(
    f"""
    <style>
    .block-container {{padding-top: 1.6rem; max-width: 1500px;}}
    .headline {{font-family: Spectral, serif; font-size: 2.5rem; line-height: 1.2; font-weight: 500;
                color: {COLORS['tinta']}; max-width: 34ch; margin: 0 0 .5rem;}}
    .headline b {{font-weight: 700;}}
    .azulejo {{height: 10px; margin: .2rem 0 .9rem; border-radius: 2px;
               background: repeating-linear-gradient(45deg, {COLORS['acequia']} 0 5px, transparent 5px 10px),
                           repeating-linear-gradient(-45deg, {COLORS['huerta']} 0 5px, {COLORS['cal']} 5px 10px);
               opacity: .55; max-width: 220px;}}
    .existing {{color: #4B5B50; font-size: 1.02rem; margin-bottom: .6rem;}}
    [data-testid="stMetric"] {{border-left: 3px solid {COLORS['huerta']}; padding: .2rem 0 .2rem .8rem;}}
    [data-testid="stMetricValue"] {{font-family: Spectral, serif;}}
    .legend {{display: flex; flex-wrap: wrap; gap: .4rem 1.2rem; font-size: .95rem; margin-top: .4rem;}}
    .legend span {{display: inline-flex; align-items: center; gap: .4rem;}}
    .legend i {{width: 12px; height: 12px; border-radius: 50%; display: inline-block;}}
    .legend i.sq {{border-radius: 2px;}}
    .rank-row {{display: grid; grid-template-columns: 2.2rem 1fr; gap: .2rem 1rem; align-items: baseline;}}
    .rank-pos {{font-family: Spectral, serif; font-size: 1.8rem; color: {COLORS['huerta']};}}
    .rank-title {{font-family: Spectral, serif; font-size: 1.35rem; font-weight: 600;}}
    .rank-meta {{color: #4B5B50; font-size: .95rem;}}
    .bar {{height: 10px; background: #E3EADC; border-radius: 5px; margin: .35rem 0;}}
    .bar > div {{height: 100%; background: {COLORS['huerta']}; border-radius: 5px;}}
    .best {{display: inline-block; background: {COLORS['naranja']}; color: white; font-size: .8rem;
            padding: .05rem .55rem; border-radius: 999px; margin-left: .5rem; vertical-align: middle;}}
    </style>
    """,
    unsafe_allow_html=True,
)


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


def fmt(n: float) -> str:
    """Spanish thousands separator."""
    return f"{n:,.0f}".replace(",", ".")


state = st.session_state

# --- Login: only registered residents can propose and vote ----------------------------
if not state.get("user"):
    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        st.markdown('<p class="headline">Entra para proponer y votar en tu barrio.</p><div class="azulejo"></div>',
                    unsafe_allow_html=True)
        st.write("Comprobamos tu identidad y tu barrio de empadronamiento, así solo votan los vecinos del barrio.")
        with st.form("login"):
            dni = st.text_input("DNI o NIE", placeholder="11111111H")
            pin = st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                user = db.authenticate(dni, pin)
                if user:
                    state.user = user
                    st.rerun()
                st.error("El DNI o la clave no coinciden. Revisa los datos e inténtalo de nuevo.")
        st.caption("Demo: el acceso simula la identificación con Cl@ve y la consulta al padrón municipal.")
        with st.expander("Vecinos de prueba"):
            st.markdown(
                "| DNI | Nombre | Empadronado en | Clave |\n|---|---|---|---|\n"
                + "\n".join(f"| {u[0]} | {u[1]} | {u[2].title()} | {u[3]} |" for u in db.DEMO_USERS)
            )
    st.stop()

user = state.user

# --- Sidebar: user, neighbourhood and decision variables ------------------------------
barrio_names = sorted(b["properties"]["nombre"] for b in data.load_barrios())
with st.sidebar:
    st.title("València Futura")
    st.caption("El laboratorio de tu barrio")
    st.markdown(f"**{user['name']}**, empadronado/a en {user['barrio'].title()}")
    if st.button("Cerrar sesión"):
        state.clear()
        st.rerun()
    barrio_name = st.selectbox("Barrio que estás viendo", barrio_names, index=barrio_names.index(user["barrio"]))
    own_barrio = barrio_name == user["barrio"]
    st.subheader("Variables de decisión")
    radius = st.slider("Distancia máxima a un banco (m)", 25, 300, 75, 25)
    cost_bench = st.number_input("Coste por banco (€)", 100, 5000, 800, 50)
    cost_tree = st.number_input("Coste por árbol (€)", 100, 5000, 400, 50)
    st.subheader("Población estimada")
    st.caption("El geoportal publica las manzanas sin datos de edad, así que estas cifras son una estimación ajustable.")
    mean_residents = st.slider("Habitantes medios por manzana", 20, 500, 150, 10)
    pct_elderly = st.slider("Mayores de 65 años (%)", 5, 40, 22)

d = load_barrio(barrio_name)
lat0, lon0 = barrio_center(d["barrio"])
blocks = model.blocks_from_features(d["manzanas"], lat0)
elderly = model.estimate_population(blocks, mean_residents, pct_elderly)

if state.get("barrio") != barrio_name:
    state.update(barrio=barrio_name, new_benches=[], new_trees=[], last_click=None)
if state.get("flash"):
    st.toast(state.pop("flash"))

all_benches = d["bancos"] + state.new_benches
before = model.coverage(blocks, elderly, d["bancos"], radius, lat0)
after = model.coverage(blocks, elderly, all_benches, radius, lat0)
gained = after - before
cost = len(state.new_benches) * cost_bench + len(state.new_trees) * cost_tree
uncovered = elderly.sum() - after

st.markdown(
    f"""<p class="headline">En {barrio_name.title()}, <b>{fmt(uncovered)} personas mayores</b>
    no tienen un banco a menos de {radius} m.</p><div class="azulejo"></div>""",
    unsafe_allow_html=True,
)

tab_sim, tab_vote = st.tabs(["Diseña tu propuesta", "Vota las propuestas"])

# --- Simulator ------------------------------------------------------------------------
with tab_sim:
    st.markdown(
        f"""<p class="existing">Ya hay en el barrio {fmt(len(d['bancos']))} bancos, {fmt(len(d['arboles']))} árboles
        y {len(d['parques'])} parques y jardines, repartidos en {len(blocks)} manzanas.</p>""",
        unsafe_allow_html=True,
    )
    left, right = st.columns([7, 3], gap="large")
    with right:
        st.subheader("Tu propuesta")
        mode = st.radio("Al hacer clic en el mapa, añade", ["Un banco", "Un árbol"], horizontal=True)
        st.metric(f"Mayores con banco a ≤ {radius} m", fmt(after), f"{gained:+,.0f}".replace(",", "."))
        st.metric("Coste", f"{fmt(cost)} €")
        st.metric("Coste por persona mayor beneficiada", f"{fmt(cost / gained)} €" if gained > 0 else "—")
        st.caption(f"{len(state.new_benches)} bancos y {len(state.new_trees)} árboles nuevos")
        if st.button("Quitar todo lo añadido", disabled=not (state.new_benches or state.new_trees)):
            state.update(new_benches=[], new_trees=[])
            st.rerun()
        if not own_barrio:
            st.info(f"Puedes explorar {barrio_name.title()}, pero solo publicas propuestas en {user['barrio'].title()}.")
        with st.form("save", border=False):
            title = st.text_input("Nombre de la propuesta", placeholder="Bancos junto al mercado de Russafa")
            if st.form_submit_button("Publicar propuesta", type="primary",
                                     disabled=not own_barrio or not (state.new_benches or state.new_trees)):
                db.save_proposal(
                    barrio_name, title or "Propuesta sin nombre", user["name"], state.new_benches, state.new_trees,
                    cost, before, after,
                    {"radius": radius, "mean_residents": mean_residents, "pct_elderly": pct_elderly},
                )
                state.update(new_benches=[], new_trees=[], flash="Propuesta publicada. Ya se puede votar.")
                st.rerun()

    with left:
        m = folium.Map(location=[lat0, lon0], zoom_start=16, tiles="OpenStreetMap")
        folium.GeoJson(d["barrio"], style_function=lambda _: {
            "color": COLORS["huerta"], "fill": False, "weight": 3, "dashArray": "6 4"}).add_to(m)
        for p in d["parques"]:
            folium.GeoJson(p, style_function=lambda _: {
                "color": COLORS["huerta"], "fillColor": COLORS["hoja"], "fillOpacity": 0.45, "weight": 1},
                tooltip=p["properties"].get("nombre")).add_to(m)
        covered = model.covered_mask(blocks, all_benches, radius, lat0)
        for f, ok, e in zip(d["manzanas"], covered, elderly):
            folium.GeoJson(f, style_function=lambda _, ok=ok: {
                "color": "#FFFFFF", "weight": 0.8, "fillColor": COLORS["covered"] if ok else COLORS["naranja"],
                "fillOpacity": 0.35 if ok else 0.55},
                tooltip=f"{e:.0f} mayores (estimado), {'con banco cerca' if ok else 'sin banco cerca'}").add_to(m)
        for lat, lon in d["arboles"]:
            folium.CircleMarker([lat, lon], radius=2.5, color=COLORS["hoja"], fill=True, fill_opacity=0.8,
                                weight=0).add_to(m)
        for lat, lon in d["bancos"]:
            folium.CircleMarker([lat, lon], radius=3.5, color=COLORS["tierra"], fill=True, fill_opacity=1,
                                weight=0).add_to(m)
        for lat, lon in state.new_benches:
            folium.Marker([lat, lon], icon=folium.Icon(color="cadetblue", icon="plus"), tooltip="Banco nuevo").add_to(m)
        for lat, lon in state.new_trees:
            folium.Marker([lat, lon], icon=folium.Icon(color="green", icon="leaf"), tooltip="Árbol nuevo").add_to(m)

        out = st_folium(m, key="map", height=600, use_container_width=True, returned_objects=["last_clicked"])
        st.markdown(
            f"""<div class="legend">
            <span><i style="background:{COLORS['tierra']}"></i>Banco</span>
            <span><i style="background:{COLORS['hoja']}"></i>Árbol</span>
            <span><i class="sq" style="background:{COLORS['hoja']}"></i>Parque o jardín</span>
            <span><i class="sq" style="background:{COLORS['naranja']}"></i>Manzana sin banco a ≤ {radius} m</span>
            <span><i style="background:{COLORS['acequia']}"></i>Lo que tú añades</span></div>""",
            unsafe_allow_html=True,
        )
        click = (out or {}).get("last_clicked")
        if click and click != state.last_click:
            state.last_click = click
            (state.new_benches if mode == "Un banco" else state.new_trees).append((click["lat"], click["lng"]))
            st.rerun()

# --- Voting ---------------------------------------------------------------------------
with tab_vote:
    proposals = db.ranking(barrio_name)
    if not proposals:
        st.info("Todavía no hay propuestas en este barrio. Diseña la primera en la otra pestaña.")
    else:
        if own_barrio:
            st.caption(f"Votas como {user['name']}. Cada vecino puede votar una vez cada propuesta. "
                       "Las cifras de población son estimadas.")
        else:
            st.info(f"Solo los vecinos empadronados en {barrio_name.title()} pueden votar aquí.")
        efficiency = {p["id"]: p["cost"] / g for p in proposals if (g := p["elderly_after"] - p["elderly_before"]) > 0}
        best_id = min(efficiency, key=efficiency.get) if efficiency else None
        max_votes = max(p["votes"] for p in proposals) or 1
        for i, p in enumerate(proposals, 1):
            gain = p["elderly_after"] - p["elderly_before"]
            per_person = f"{fmt(efficiency[p['id']])} € por persona" if p["id"] in efficiency else "sin mayores nuevos cubiertos"
            badge = '<span class="best">La más eficiente</span>' if p["id"] == best_id else ""
            row, action = st.columns([5, 1], vertical_alignment="center")
            row.markdown(
                f"""<div class="rank-row"><div class="rank-pos">{i}</div><div>
                <div class="rank-title">{html.escape(p['title'])}{badge}</div>
                <div class="bar"><div style="width:{100 * p['votes'] / max_votes:.0f}%"></div></div>
                <div class="rank-meta">{p['votes']} votos. Propuesta de {html.escape(p['author'])}: {fmt(p['cost'])} €,
                {gain:+.0f} mayores con banco cerca, {per_person}.</div></div></div>""",
                unsafe_allow_html=True,
            )
            if action.button("Votar", key=f"vote_{p['id']}", disabled=not own_barrio):
                state.flash = {
                    "ok": "Voto registrado.",
                    "duplicate": "Ya habías votado esta propuesta.",
                    "wrong_barrio": "Solo pueden votar los vecinos empadronados en este barrio.",
                }[db.vote(p["id"], user["dni"])]
                st.rerun()
            st.divider()
