"""València Futura — propose neighbourhood reforms with measured impact, then vote."""

import html

import folium
import streamlit as st
from streamlit_folium import st_folium

import data
import db
import model

st.set_page_config(page_title="València Futura", page_icon="🌿", layout="wide")

# Palette inspired by conservation.org, shifted to green: ozone paper, deep pine green, biodiversity/forest
# greens, climate orange (alert) and lime (what the resident adds).
COLORS = {
    "ozone": "#FAF7F2",
    "whale": "#133A24",
    "whale70": "#56685B",
    "forest": "#257422",
    "biodiversity": "#4BAA47",
    "climate": "#FC992F",
    "ocean": "#8CC63F",
    "bench": "#3B2A1E",
    "covered": "#D6E9CF",
}
SLIDES = [f"app/static/slide{i}.jpg" for i in range(1, 6)]
SLIDE_SECONDS = 6
PHOTO_CREDIT = ("Fotos: Joanbanjo, Pacopac, isaacpanoramio y Acediscovery "
                "(CC BY-SA / CC BY, Wikimedia Commons)")


def carousel() -> str:
    """Cross-fading background photos (pure CSS); static first photo under reduced motion."""
    total = SLIDE_SECONDS * len(SLIDES)
    return '<div class="slides" aria-hidden="true">' + "".join(
        f'<i style="background-image:url({url});animation-delay:{i * SLIDE_SECONDS}s;'
        f'animation-duration:{total}s"></i>' for i, url in enumerate(SLIDES)
    ) + "</div>"

st.markdown(
    f"""
    <style>
    header[data-testid="stHeader"] {{background: transparent;}}
    .block-container {{max-width: none; padding: 0 3rem 3rem;}}
    h1, h2, h3, .display {{text-wrap: balance;}}
    .display {{font-family: 'Barlow Condensed', sans-serif; text-transform: uppercase; font-weight: 800;
               line-height: .95; letter-spacing: .005em; margin: 0;}}

    .hero {{position: relative; margin: 0 -3rem 2rem; min-height: 440px; display: flex; align-items: flex-end; overflow: hidden;}}
    .slides, .slides i {{position: absolute; inset: 0;}}
    .slides i {{background: center 40% / cover no-repeat; opacity: 0; animation: fade linear infinite;}}
    .slides::after {{content: ""; position: absolute; inset: 0;
                     background: linear-gradient(90deg, rgba(19,58,36,.92) 0%, rgba(19,58,36,.6) 45%, rgba(19,58,36,.1) 100%);}}
    .login-hero .slides::after {{background: linear-gradient(0deg, rgba(19,58,36,.9) 0%, rgba(19,58,36,.2) 70%);}}
    @keyframes fade {{0% {{opacity: 0;}} 4% {{opacity: 1;}} 20% {{opacity: 1;}} 24% {{opacity: 0;}} 100% {{opacity: 0;}}}}
    @media (prefers-reduced-motion: reduce) {{
        .slides i {{animation: none;}} .slides i:first-child {{opacity: 1;}}
    }}
    .hero-inner, .login-hero .display {{position: relative; z-index: 1;}}
    .hero-inner {{padding: 6rem 3rem 2.6rem; max-width: 62rem; color: {COLORS['ozone']};}}
    .hero .display {{font-size: clamp(2.6rem, 5.2vw, 5rem); color: {COLORS['ozone']};}}
    .hero p {{font-size: 1.15rem; max-width: 46ch; margin: 1rem 0 0; opacity: .92;}}
    .hero .credit {{position: absolute; z-index: 1; right: 1rem; bottom: .5rem; font-size: .72rem; opacity: .7; color: #fff;}}

    .stats {{display: flex; flex-wrap: wrap; gap: 2.5rem; margin: 0 0 1.6rem; color: {COLORS['whale']};}}
    .stats div {{font-variant-numeric: tabular-nums;}}
    .stats b {{display: block; font-family: 'Barlow Condensed', sans-serif; font-size: 2.6rem; font-weight: 700;
                line-height: 1;}}
    .stats span {{color: {COLORS['whale70']}; font-size: .95rem;}}

    .section-title {{font-size: 2.2rem; color: {COLORS['whale']}; margin: .4rem 0 .8rem;}}
    [data-testid="stMetric"] {{border-top: 3px solid {COLORS['biodiversity']}; padding-top: .5rem;}}
    [data-testid="stMetricValue"] {{font-family: 'Barlow Condensed', sans-serif; font-weight: 700;
                                    font-variant-numeric: tabular-nums;}}
    [data-baseweb="tab"] p {{font-family: 'Barlow Condensed', sans-serif; text-transform: uppercase;
                              font-size: 1.25rem; font-weight: 700; letter-spacing: .02em;}}
    .stButton button, .stFormSubmitButton button {{text-transform: uppercase; font-weight: 700;
                                                   letter-spacing: .04em;}}
    button:focus-visible, input:focus-visible, [role="tab"]:focus-visible {{
        outline: 3px solid {COLORS['climate']} !important; outline-offset: 2px;}}

    .legend {{display: flex; flex-wrap: wrap; gap: .4rem 1.4rem; font-size: .95rem; margin-top: .5rem;
               color: {COLORS['whale']};}}
    .legend span {{display: inline-flex; align-items: center; gap: .45rem;}}
    .legend i {{width: 12px; height: 12px; border-radius: 50%; display: inline-block;}}
    .legend i.sq {{border-radius: 2px;}}

    .rank {{display: grid; grid-template-columns: 3.2rem minmax(0, 1fr); gap: 0 1rem; align-items: start;}}
    .rank-pos {{font-family: 'Barlow Condensed', sans-serif; font-size: 3rem; font-weight: 800; line-height: .9;
                color: {COLORS['forest']};}}
    .rank-title {{font-family: 'Barlow Condensed', sans-serif; font-size: 1.7rem; font-weight: 700;
                  text-transform: uppercase; color: {COLORS['whale']}; overflow-wrap: anywhere;}}
    .rank-meta {{color: {COLORS['whale70']}; font-variant-numeric: tabular-nums;}}
    .bar {{height: 8px; background: #DCE8D5; margin: .45rem 0;}}
    .bar > div {{height: 100%; background: {COLORS['biodiversity']};}}
    .best {{display: inline-block; background: {COLORS['climate']}; color: {COLORS['whale']}; font-size: .85rem;
            padding: .1rem .6rem; margin-left: .6rem; vertical-align: middle; letter-spacing: .03em;}}

    .login-hero {{position: relative; overflow: hidden; min-height: 78vh; display: flex; align-items: flex-end;
                  margin: 0 0 0 -3rem;}}
    .login-hero .display {{font-size: clamp(2.8rem, 5vw, 4.6rem); color: {COLORS['ozone']};
                           padding: 0 3rem 2.4rem;}}
    .login-hero small {{display: block; font-family: 'Montserrat', sans-serif; text-transform: none;
                        font-weight: 400; font-size: 1.05rem; line-height: 1.5; margin-top: 1rem; opacity: .9;}}
    @media (max-width: 760px) {{
        .block-container {{padding: 0 1rem 2rem;}}
        .hero {{margin: 0 -1rem 1.5rem; min-height: 360px;}}
        .hero-inner {{padding: 5rem 1rem 2rem;}}
        .login-hero {{margin: 0 -1rem; min-height: 50vh;}}
        .login-hero .display {{padding: 0 1rem 1.5rem;}}
    }}
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
    photo, form_col = st.columns([1.35, 1], gap="large", vertical_alignment="center")
    with photo:
        st.markdown(
            f"""<div class="login-hero">{carousel()}
            <h1 class="display">Tu barrio se decide con datos<small>Propón mejoras para tu calle con datos
            reales del Ayuntamiento y vota las de tus vecinos.</small></h1></div>
            <p style="font-size:.72rem;color:{COLORS['whale70']};margin:.4rem 0 0">{PHOTO_CREDIT}</p>""",
            unsafe_allow_html=True,
        )
    with form_col:
        st.markdown('<h2 class="display section-title">Entra en València Futura</h2>', unsafe_allow_html=True)
        st.write("Comprobamos tu identidad y tu barrio de empadronamiento: solo votan los vecinos del barrio.")
        with st.form("login"):
            dni = st.text_input("DNI o NIE", placeholder="11111111H…", autocomplete="username")
            pin = st.text_input("Clave", type="password", autocomplete="current-password")
            if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                user = db.authenticate(dni, pin)
                if user:
                    state.user = user
                    st.rerun()
                st.error("El DNI o la clave no coinciden. Revisa los datos y vuelve a intentarlo.")
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
    st.markdown('<p class="display" style="font-size:2rem">València Futura</p>', unsafe_allow_html=True)
    st.markdown(f"**{html.escape(user['name'])}**, empadronado/a en {user['barrio'].title()}")
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
    f"""<section class="hero">{carousel()}
    <div class="hero-inner">
    <h1 class="display">{fmt(uncovered)} personas mayores de {barrio_name.title()} no tienen un banco a menos de {radius}&nbsp;m</h1>
    <p>Coloca bancos y árboles en el mapa, mide a cuántos vecinos llegas y publícalo para que el barrio vote.</p>
    </div><span class="credit">{PHOTO_CREDIT}</span></section>
    <div class="stats" aria-label="Lo que ya hay en el barrio">
    <div><b>{fmt(len(d['bancos']))}</b><span>bancos</span></div>
    <div><b>{fmt(len(d['arboles']))}</b><span>árboles</span></div>
    <div><b>{len(d['parques'])}</b><span>parques y jardines</span></div>
    <div><b>{len(blocks)}</b><span>manzanas</span></div>
    <div><b>{fmt(elderly.sum())}</b><span>mayores estimados</span></div></div>""",
    unsafe_allow_html=True,
)

tab_sim, tab_vote = st.tabs(["Diseña tu propuesta", "Vota las propuestas"])

# --- Simulator ------------------------------------------------------------------------
with tab_sim:
    left, right = st.columns([7, 3], gap="large")
    with right:
        st.markdown('<h2 class="display section-title">Tu propuesta</h2>', unsafe_allow_html=True)
        mode = st.radio("Al hacer clic en el mapa, añade", ["Un banco", "Un árbol"], horizontal=True)
        st.metric(f"Mayores con banco a ≤ {radius} m", fmt(after), f"{gained:+,.0f}".replace(",", "."))
        st.metric("Coste", f"{fmt(cost)} €")
        st.metric("Coste por persona mayor beneficiada", f"{fmt(cost / gained)} €" if gained > 0 else "—")
        st.caption(f"{len(state.new_benches)} bancos y {len(state.new_trees)} árboles nuevos")
        if st.button("Quitar lo añadido", disabled=not (state.new_benches or state.new_trees)):
            state.update(new_benches=[], new_trees=[])
            st.rerun()
        if not own_barrio:
            st.info(f"Puedes explorar {barrio_name.title()}, pero solo publicas propuestas en {user['barrio'].title()}.")
        with st.form("save", border=False):
            title = st.text_input("Nombre de la propuesta", placeholder="Bancos junto al mercado de Russafa…",
                                  autocomplete="off")
            if st.form_submit_button("Publicar propuesta", type="primary", use_container_width=True,
                                     disabled=not own_barrio or not (state.new_benches or state.new_trees)):
                db.save_proposal(
                    barrio_name, title or "Propuesta sin nombre", user["name"], state.new_benches,
                    state.new_trees, cost, before, after,
                    {"radius": radius, "mean_residents": mean_residents, "pct_elderly": pct_elderly},
                )
                state.update(new_benches=[], new_trees=[], flash="Propuesta publicada. Ya se puede votar.")
                st.rerun()

    with left:
        m = folium.Map(location=[lat0, lon0], zoom_start=16, tiles="OpenStreetMap")
        folium.GeoJson(d["barrio"], style_function=lambda _: {
            "color": COLORS["whale"], "fill": False, "weight": 3, "dashArray": "6 4"}).add_to(m)
        for p in d["parques"]:
            folium.GeoJson(p, style_function=lambda _: {
                "color": COLORS["forest"], "fillColor": COLORS["biodiversity"], "fillOpacity": 0.5, "weight": 1},
                tooltip=p["properties"].get("nombre")).add_to(m)
        covered = model.covered_mask(blocks, all_benches, radius, lat0)
        for f, ok, e in zip(d["manzanas"], covered, elderly):
            folium.GeoJson(f, style_function=lambda _, ok=ok: {
                "color": "#FFFFFF", "weight": 0.8, "fillColor": COLORS["covered"] if ok else COLORS["climate"],
                "fillOpacity": 0.4 if ok else 0.6},
                tooltip=f"{e:.0f} mayores (estimado), {'con banco cerca' if ok else 'sin banco cerca'}").add_to(m)
        for lat, lon in d["arboles"]:
            folium.CircleMarker([lat, lon], radius=2.5, color=COLORS["forest"], fill=True, fill_opacity=0.8,
                                weight=0).add_to(m)
        for lat, lon in d["bancos"]:
            folium.CircleMarker([lat, lon], radius=3.5, color=COLORS["bench"], fill=True, fill_opacity=1,
                                weight=0).add_to(m)
        for lat, lon in state.new_benches:
            folium.Marker([lat, lon], icon=folium.Icon(color="lightgreen", icon="plus"), tooltip="Banco nuevo").add_to(m)
        for lat, lon in state.new_trees:
            folium.Marker([lat, lon], icon=folium.Icon(color="green", icon="leaf"), tooltip="Árbol nuevo").add_to(m)

        out = st_folium(m, key="map", height=600, use_container_width=True, returned_objects=["last_clicked"])
        st.markdown(
            f"""<div class="legend" aria-label="Leyenda del mapa">
            <span><i aria-hidden="true" style="background:{COLORS['bench']}"></i>Banco</span>
            <span><i aria-hidden="true" style="background:{COLORS['forest']}"></i>Árbol</span>
            <span><i aria-hidden="true" class="sq" style="background:{COLORS['biodiversity']}"></i>Parque o jardín</span>
            <span><i aria-hidden="true" class="sq" style="background:{COLORS['climate']}"></i>Manzana sin banco a ≤ {radius}&nbsp;m</span>
            <span><i aria-hidden="true" style="background:{COLORS['ocean']}"></i>Lo que tú añades</span></div>""",
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
        st.info("Todavía no hay propuestas en este barrio. Diseña la primera en «Diseña tu propuesta».")
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
                f"""<div class="rank"><div class="rank-pos">{i}</div><div>
                <div class="rank-title">{html.escape(p['title'])}{badge}</div>
                <div class="bar" role="img" aria-label="{p['votes']} de {max_votes} votos">
                <div style="width:{100 * p['votes'] / max_votes:.0f}%"></div></div>
                <div class="rank-meta">{p['votes']} votos. Propuesta de {html.escape(p['author'])}: {fmt(p['cost'])} €,
                {gain:+.0f} mayores con banco cerca, {per_person}.</div></div></div>""",
                unsafe_allow_html=True,
            )
            if action.button("Votar", key=f"vote_{p['id']}", disabled=not own_barrio, use_container_width=True):
                state.flash = {
                    "ok": "Voto registrado.",
                    "duplicate": "Ya habías votado esta propuesta.",
                    "wrong_barrio": "Solo pueden votar los vecinos empadronados en este barrio.",
                }[db.vote(p["id"], user["dni"])]
                st.rerun()
            st.divider()
