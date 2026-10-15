"""València Futura — propose neighbourhood reforms with measured impact, then vote."""

import html
import json

import folium
import streamlit as st
from streamlit_folium import st_folium

import data
import db
import green
import model
import ornaments

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
    @keyframes fade {{0% {{opacity: 0;}} 4% {{opacity: 1;}} 20% {{opacity: 1;}} 24% {{opacity: 0;}} 100% {{opacity: 0;}}}}
    @media (prefers-reduced-motion: reduce) {{
        .slides i {{animation: none;}} .slides i:first-child {{opacity: 1;}}
    }}
    .hero-inner {{position: relative; z-index: 1;}}
    .claims {{display: grid;}}
    /* Two headlines, 7 s each (14 s cycle). The first is visible from the very first frame; the swap takes
       ~0.3 s and both change at the same moment. The negative delay puts the second mid-cycle, so nothing waits. */
    .claims span {{grid-area: 1 / 1; animation: claim 14s linear infinite;}}
    .claims span:nth-child(2) {{animation-delay: -7s;}}
    @keyframes claim {{0%, 48% {{opacity: 1;}} 50%, 98% {{opacity: 0;}} 100% {{opacity: 1;}}}}
    @media (prefers-reduced-motion: reduce) {{
        .claims {{display: block;}} .claims span {{display: block; animation: none;}}
        .claims span:nth-child(2) {{font-size: .55em; margin-top: .6rem;}}
    }}
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
    .bar.split {{display: flex; gap: 2px; background: transparent;}}
    .bar.split > div {{border-radius: 2px;}}
    .bar.split > div.against {{background: {COLORS['climate']};}}
    .bar.split > div.none {{background: #DCE8D5; flex: 1;}}
    .mine {{display: inline-block; background: {COLORS['whale']}; color: #FFFFFF; font-size: .85rem;
            padding: .1rem .6rem; margin-left: .6rem; vertical-align: middle;}}
    .suggestion {{border-left: 3px solid {COLORS['biodiversity']}; padding: .2rem 0 .2rem .8rem; margin: .4rem 0;}}
    .suggestion small {{color: {COLORS['whale70']};}}
    .best {{display: inline-block; background: {COLORS['climate']}; color: {COLORS['whale']}; font-size: .85rem;
            padding: .1rem .6rem; margin-left: .6rem; vertical-align: middle; letter-spacing: .03em;}}

    @media (max-width: 760px) {{
        .block-container {{padding: 0 1rem 2rem;}}
        .hero {{margin: 0 -1rem 1.5rem; min-height: 360px;}}
        .hero-inner {{padding: 5rem 1rem 2rem;}}
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
if not state.get("user") and not state.get("guest"):
    # Full-screen photo carousel behind a centred card framed by leaf sprigs (Central Park–style greens).
    st.markdown(
        f"""<style>
        [data-testid="stApp"], [data-testid="stMain"] {{background: transparent;}}
        .login-bg {{position: fixed; inset: 0; z-index: 0;}}
        .login-bg .slides::after {{background: radial-gradient(ellipse at center, rgba(19,58,36,.35) 0%,
                                   rgba(19,58,36,.8) 75%);}}
        [data-testid="stMainBlockContainer"] {{position: relative; z-index: 1; padding-top: 6vh;}}
        .login-title {{text-align: center; color: #FFFFFF; font-size: clamp(2.6rem, 5vw, 4.4rem);
                       text-shadow: 0 2px 18px rgba(0,0,0,.35); margin: 0 auto .4rem; max-width: 18ch;}}
        .login-sub {{text-align: center; color: #F1F6EE; font-size: 1.1rem; margin: 0 auto 2.2rem; max-width: 44ch;}}
        .st-key-login_card {{position: relative; background: rgba(255,255,255,.96); border-radius: 22px;
                             padding: 2.2rem 2.2rem 1.6rem; border: 2px solid #C8E379;
                             box-shadow: 0 24px 60px rgba(10,35,20,.35);}}
        .st-key-login_card::before, .st-key-login_card::after {{content: ""; position: absolute; width: 190px;
                                                              height: 190px; background: center / contain no-repeat;
                                                              pointer-events: none;}}
        .st-key-login_card::before {{background-image: url("{ornaments.SPRIG_A}"); left: -92px; top: -96px;
                                     transform: rotate(-8deg);}}
        .st-key-login_card::after {{background-image: url("{ornaments.SPRIG_B}"); right: -90px; bottom: -92px;
                                    transform: rotate(172deg);}}
        .leaf-rule {{height: 22px; margin: .2rem 0 1rem; background: url("{ornaments.SPRIG_B}") left center / 70px no-repeat,
                     linear-gradient(#C8E379, #C8E379) 80px center / calc(100% - 80px) 2px no-repeat;}}
        .login-credit {{position: fixed; right: 1rem; bottom: .5rem; z-index: 1; font-size: .72rem;
                        color: rgba(255,255,255,.8);}}
        @media (max-width: 760px) {{
            .st-key-login_card {{padding: 1.6rem 1.2rem 1.2rem;}}
            .st-key-login_card::before, .st-key-login_card::after {{width: 110px; height: 110px;}}
            .st-key-login_card::before {{left: -40px; top: -60px;}}
            .st-key-login_card::after {{right: -40px; bottom: -60px;}}
        }}
        </style>""",
        unsafe_allow_html=True,
    )
    # No indentation inside this HTML: after a <style> block, indented lines would render as a code block.
    st.markdown(
        f'<div class="login-bg">{carousel()}</div>'
        '<h1 class="display login-title">Tu barrio se decide con datos</h1>'
        '<p class="login-sub">Propón mejoras para tu calle con datos reales del Ayuntamiento y vota las de tus '
        f'vecinos.</p><span class="login-credit">{PHOTO_CREDIT}</span>',
        unsafe_allow_html=True,
    )
    if not state.get("show_login"):
        # Public landing: rotating real city-wide green figures, calls to action that open the login,
        # and content sections below the fold.
        city = green.city_table()
        species = green.species_table()
        top_trees = city.sort_values("arboles", ascending=False).iloc[0]
        top_green = city.sort_values("m2_verde_por_ha", ascending=False).iloc[0]
        stat_sets = [
            [(fmt(city["arboles"].sum()), "árboles en la ciudad"),
             (fmt(city["zona_verde_m2"].sum() / 10_000), "hectáreas de parques y jardines"),
             (fmt(city["bancos"].sum()), "bancos en la calle")],
            [(fmt(len(data.load_all_parks())), "zonas verdes"),
             (fmt(len(data.group_stats("arboles", "nom_comu_c", [("count", "objectid", "n")]))), "especies de árbol"),
             (fmt(species.iloc[0]["n"]), f"ejemplares de {species.iloc[0]['especie'].lower()}, el más plantado")],
            [(fmt(top_trees["arboles"]), f"árboles en {top_trees['barrio'].title()}, el barrio con más"),
             (fmt(top_green["m2_verde_por_ha"]), f"m² verdes por hectárea en {top_green['barrio'].title()}"),
             (fmt(city["m2_verde_por_ha"].median()), "m² verdes por hectárea en el barrio mediano")],
        ]
        seconds = 5
        sets_html = "".join(
            f'<div class="stat-set" style="animation-delay:{-((len(stat_sets) - i) % len(stat_sets)) * seconds}s;'
            f'animation-duration:{seconds * len(stat_sets)}s">'
            + "".join(f"<div><b>{v}</b>{label}</div>" for v, label in group) + "</div>"
            for i, group in enumerate(stat_sets)
        )
        st.markdown(
            f"""<style>
            [data-testid="stMainBlockContainer"] {{padding-top: 2.5vh;}}
            .login-sub {{margin-bottom: 1.2rem;}}
            .landing-stats {{display: grid; margin: 0 auto 2rem; color: #FFFFFF; text-align: center;
                             text-shadow: 0 2px 12px rgba(0,0,0,.35); min-height: 7.5rem;}}
            .stat-set {{grid-area: 1 / 1; display: flex; justify-content: center; flex-wrap: wrap; gap: 1rem 3.5rem;
                        animation: statfade linear infinite;}}
            .stat-set div {{max-width: 16rem;}}
            .stat-set b {{display: block; font-family: 'Barlow Condensed', sans-serif; font-size: 3.4rem;
                          font-weight: 800; line-height: 1; font-variant-numeric: tabular-nums;}}
            @keyframes statfade {{0%, 31% {{opacity: 1;}} 33.3%, 98% {{opacity: 0;}} 100% {{opacity: 1;}}}}
            @media (prefers-reduced-motion: reduce) {{
                .stat-set {{animation: none; opacity: 0;}} .stat-set:first-child {{opacity: 1;}}
            }}
            [class*="st-key-cta_"] button {{border-radius: 999px; min-height: 3.4rem; font-size: 1.05rem;
                                           transition: transform .15s ease, background-color .15s ease;}}
            [class*="st-key-cta_"] button:hover {{transform: translateY(-2px);}}
            .st-key-cta_main button, .st-key-cta_end button {{background: #79C000; border-color: #79C000;
                                      color: #133A24; box-shadow: 0 10px 30px rgba(121,192,0,.35);}}
            .st-key-cta_main button:hover, .st-key-cta_end button:hover {{background: #8CD11A; color: #133A24;}}
            .st-key-cta_discover button {{background: rgba(255,255,255,.12);
                                      border: 2px solid #FFFFFF; color: #FFFFFF; backdrop-filter: blur(4px);}}
            .st-key-cta_discover button:hover {{background: #FFFFFF; color: #133A24;}}
            .st-key-cta_login button {{background: transparent; border: 0; color: #FFFFFF; min-height: 2.4rem;
                                       text-decoration: underline; text-underline-offset: 4px; box-shadow: none;}}
            @media (prefers-reduced-motion: reduce) {{[class*="st-key-cta_"] button {{transition: none;}}
                                                      [class*="st-key-cta_"] button:hover {{transform: none;}}}}
            .st-key-landing_more {{position: relative; z-index: 1; background: #F1F6EE; margin: 12vh -3rem -3rem;
                                   padding: 4rem 3rem 2rem; border-top: 6px solid #79C000;}}
            .steps {{display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); gap: 2rem;
                     margin: 1rem 0 3.5rem;}}
            .steps div {{border-top: 3px solid #4BAA47; padding-top: 1rem; color: #133A24;}}
            .steps b {{display: block; font-family: 'Barlow Condensed', sans-serif; font-size: 3rem; font-weight: 800;
                       color: #257422; line-height: 1;}}
            .steps h3 {{font-family: 'Barlow Condensed', sans-serif; text-transform: uppercase; font-size: 1.6rem;
                        margin: .4rem 0;}}
            .statement {{background: #133A24; color: #F1F6EE; margin: 3rem -3rem 0; padding: 4rem 3rem;
                         text-align: center;}}
            .statement p.display {{font-size: clamp(2rem, 4vw, 3.4rem); max-width: 24ch; margin: 0 auto;
                                   color: #FFFFFF;}}
            .statement span {{display: block; margin-top: 1rem; color: #C8E379;}}
            .landing-footer {{margin: 0 -3rem -2rem; padding: 2rem 3rem; background: #0E2C1B; color: #BED0C6;
                              font-size: .85rem;}}
            .landing-footer a {{color: #C8E379;}}
            </style>""",
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="landing-stats" aria-live="off">{sets_html}</div>', unsafe_allow_html=True)
        _, main_col, _ = st.columns([1, 1.3, 1])
        if main_col.button("Haz de tu barrio un lugar más verde", key="cta_main", use_container_width=True):
            state.show_login = True
            st.rerun()
        _, discover_col, _ = st.columns([1, 1.3, 1])
        if discover_col.button("Descubre tu barrio", key="cta_discover", use_container_width=True):
            state.guest = True
            st.rerun()
        _, login_col, _ = st.columns([1, 1.3, 1])
        if login_col.button("Ya tengo cuenta: iniciar sesión", key="cta_login", type="tertiary",
                            use_container_width=True):
            state.show_login = True
            st.rerun()

        with st.container(key="landing_more"):
            st.markdown(
                '<h2 class="display section-title">Cómo funciona</h2><div class="steps">'
                '<div><b>1</b><h3>Entra con tu DNI</h3>Comprobamos que vives en el barrio, así cada voto es de '
                'un vecino real.</div>'
                '<div><b>2</b><h3>Diseña en el mapa</h3>Coloca bancos y árboles sobre los datos reales del '
                'Ayuntamiento y mira al momento a cuántos vecinos llegas y cuánto cuesta.</div>'
                '<div><b>3</b><h3>Vota y decide</h3>Las propuestas se ordenan por votos y muestran su coste por '
                'persona beneficiada: votas sabiendo qué funciona.</div></div>',
                unsafe_allow_html=True,
            )
            chart_col, text_col = st.columns([3, 2], gap="large", vertical_alignment="center")
            with chart_col:
                st.markdown('<h2 class="display section-title">Los árboles de València</h2>', unsafe_allow_html=True)
                st.altair_chart(green.species_chart(species), use_container_width=True)
            with text_col:
                st.markdown(
                    f"València tiene **{fmt(city['arboles'].sum())} árboles** en la calle, pero no están repartidos "
                    f"por igual: {top_trees['barrio'].title()} tiene {fmt(top_trees['arboles'])} y el barrio "
                    f"mediano, {fmt(city['arboles'].median())}.\n\n"
                    "Con València Futura cada vecino puede ver qué tiene cerca y proponer lo que falta."
                )
                if st.button("Descubre tu barrio", key="cta_end", use_container_width=True):
                    state.guest = True
                    st.rerun()
            st.markdown(
                '<div class="statement"><p class="display">Una administración que detecta lo que falta antes de '
                'que lleguen las quejas</p><span>Con datos abiertos del Ayuntamiento de València y el criterio de zonas '
                'verdes de la OMS</span></div>'
                f'<div class="landing-footer">València Futura, proyecto de hackathon (2026). Datos: '
                '<a href="https://geoportal.valencia.es">geoportal.valencia.es</a> (arbolado, bancos, espacios '
                f'verdes, manzanas y barrios). {PHOTO_CREDIT}.</div>',
                unsafe_allow_html=True,
            )
        st.stop()

    _, center, _ = st.columns([1, 1.15, 1])
    with center, st.container(key="login_card"):
        st.markdown('<h2 class="display section-title" style="text-align:center">Entra en València Futura</h2>'
                    '<div class="leaf-rule" aria-hidden="true"></div>', unsafe_allow_html=True)
        st.write("Comprobamos tu identidad y tu barrio de empadronamiento: solo votan los vecinos del barrio.")
        with st.form("login", border=False):
            dni = st.text_input("DNI o NIE", placeholder="11111111H…", autocomplete="username")
            pin = st.text_input("Clave", type="password", autocomplete="current-password")
            if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                user = db.authenticate(dni, pin)
                if user:
                    state.update(user=user, guest=False)
                    st.rerun()
                st.error("El DNI o la clave no coinciden. Revisa los datos y vuelve a intentarlo.")
        st.caption("Demo: el acceso simula la identificación con Cl@ve y la consulta al padrón municipal.")
        if st.button("Volver al inicio", type="tertiary"):
            state.show_login = False
            st.rerun()
        with st.expander("Vecinos de prueba"):
            st.markdown(
                "| DNI | Nombre | Empadronado en | Clave |\n|---|---|---|---|\n"
                + "\n".join(f"| {u[0]} | {u[1]} | {u[2].title()} | {u[3]} |" for u in db.DEMO_USERS)
            )
    st.stop()

user = state.get("user")
guest = user is None


def require_login() -> None:
    """Send a visitor to the login; the draft on the map is kept in the session."""
    state.update(guest=False, show_login=True)
    st.rerun()


# --- Sidebar: user, neighbourhood and decision variables ------------------------------
barrio_names = sorted(b["properties"]["nombre"] for b in data.load_barrios())
with st.sidebar:
    st.markdown('<p class="display" style="font-size:2rem">València Futura</p>', unsafe_allow_html=True)
    if guest:
        st.markdown("Estás de visita: puedes explorarlo todo. Para publicar, votar o sugerir, inicia sesión.")
        if st.button("Iniciar sesión", type="primary"):
            require_login()
    else:
        st.markdown(f"**{html.escape(user['name'])}**, empadronado/a en {user['barrio'].title()}")
        if st.button("Cerrar sesión"):
            state.clear()
            st.rerun()
    default_barrio = state.get("barrio") or (user["barrio"] if user else "RUSSAFA")
    barrio_name = st.selectbox("Barrio que estás viendo", barrio_names, index=barrio_names.index(default_barrio))
    own_barrio = bool(user) and barrio_name == user["barrio"]
    st.subheader("Variables de decisión")
    radius = st.slider("Distancia máxima a un banco (m)", 25, 300, 75, 25,
                       help="Consideramos que una persona tiene un banco cerca si vive a menos de esta distancia.")
    cost_bench = st.number_input("Coste por banco (€)", 100, 5000, 800, 50)
    cost_tree = st.number_input("Coste por árbol (€)", 100, 5000, 400, 50)
    st.subheader("Población estimada")
    st.caption("El geoportal publica las manzanas sin datos de edad, así que estas cifras son una estimación ajustable.")
    mean_residents = st.slider("Habitantes medios por manzana", 20, 500, 150, 10)
    pct_elderly = st.slider("Mayores de 65 años (%)", 5, 40, 22)
    pct_children = st.slider("Menores de 15 años (%)", 5, 30, 13)
    st.subheader("Zonas verdes")
    st.caption("Criterio de la OMS: una zona verde de al menos 0,5 ha a 300 m de casa.")
    green_radius = st.slider("Distancia máxima a una zona verde (m)", 100, 1000, 300, 50)
    green_min_area = st.slider("Tamaño mínimo de zona verde (m²)", 0, 20000, 5000, 500)

d = load_barrio(barrio_name)
lat0, lon0 = barrio_center(d["barrio"])
blocks = model.blocks_from_features(d["manzanas"], lat0)
elderly = model.estimate_population(blocks, mean_residents, pct_elderly)
children = model.estimate_population(blocks, mean_residents, pct_children)
green_points = model.green_space_points(d["parques"], green_min_area)
children_without_green = children.sum() - model.coverage(blocks, children, green_points, green_radius, lat0)

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
    <h1 class="display claims">
    <span>{fmt(uncovered)} personas mayores de {barrio_name.title()} no tienen un banco a menos de {radius}&nbsp;m</span>
    <span>{fmt(children_without_green)} niños de {barrio_name.title()} no tienen una zona verde a menos de {green_radius}&nbsp;m de casa</span>
    </h1>
    <p>Coloca bancos y árboles en el mapa, mide a cuántos vecinos llegas y publícalo para que el barrio vote.</p>
    </div><span class="credit">{PHOTO_CREDIT}</span></section>
    <div class="stats" aria-label="Lo que ya hay en el barrio">
    <div><b>{fmt(len(d['bancos']))}</b><span>bancos</span></div>
    <div><b>{fmt(len(d['arboles']))}</b><span>árboles</span></div>
    <div><b>{len(d['parques'])}</b><span>parques y jardines</span></div>
    <div><b>{len(blocks)}</b><span>manzanas</span></div>
    <div><b>{fmt(elderly.sum())}</b><span>mayores estimados</span></div>
    <div><b>{fmt(children.sum())}</b><span>niños estimados</span></div></div>""",
    unsafe_allow_html=True,
)

tab_sim, tab_vote, tab_green = st.tabs(["Diseña tu propuesta", "Vota las propuestas", "València verde"])

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
            st.info(f"Puedes proponer cambios en {barrio_name.title()}, pero solo votan sus vecinos empadronados.")
        with st.form("save", border=False):
            title = st.text_input("Nombre de la propuesta", placeholder="Bancos junto al mercado de Russafa…",
                                  autocomplete="off")
            if st.form_submit_button("Inicia sesión para publicar" if guest else "Publicar propuesta",
                                     type="primary", use_container_width=True,
                                     disabled=not (state.new_benches or state.new_trees)):
                if guest:
                    require_login()
                db.save_proposal(
                    barrio_name, title or "Propuesta sin nombre", user["name"], state.new_benches,
                    state.new_trees, cost, before, after,
                    {"radius": radius, "mean_residents": mean_residents, "pct_elderly": pct_elderly},
                    author_dni=user["dni"],
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
        # One GeoJSON layer for thousands of trees keeps the page light (vs. one marker object per tree).
        folium.GeoJson(
            {"type": "FeatureCollection", "features": [
                {"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": [lon, lat]}}
                for lat, lon in d["arboles"]]},
            marker=folium.CircleMarker(radius=2.5, color=COLORS["forest"], fill=True, fill_opacity=0.8, weight=0),
        ).add_to(m)
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
def proposal_map(p: dict) -> folium.Map:
    """The barrio with one proposal drawn on it: its new benches/trees and the blocks it leaves uncovered."""
    benches, trees = [tuple(b) for b in json.loads(p["benches"])], [tuple(t) for t in json.loads(p["trees"])]
    pm = folium.Map(location=[lat0, lon0], zoom_start=16, tiles="OpenStreetMap")
    folium.GeoJson(d["barrio"], style_function=lambda _: {
        "color": COLORS["whale"], "fill": False, "weight": 3, "dashArray": "6 4"}).add_to(pm)
    ok_mask = model.covered_mask(blocks, d["bancos"] + benches, radius, lat0)
    for f, ok in zip(d["manzanas"], ok_mask):
        folium.GeoJson(f, style_function=lambda _, ok=ok: {
            "color": "#FFFFFF", "weight": 0.8, "fillColor": COLORS["covered"] if ok else COLORS["climate"],
            "fillOpacity": 0.35 if ok else 0.55}).add_to(pm)
    for lat, lon in d["bancos"]:
        folium.CircleMarker([lat, lon], radius=3, color=COLORS["bench"], fill=True, fill_opacity=1, weight=0).add_to(pm)
    for lat, lon in benches:
        folium.Marker([lat, lon], icon=folium.Icon(color="lightgreen", icon="plus"), tooltip="Banco propuesto").add_to(pm)
    for lat, lon in trees:
        folium.Marker([lat, lon], icon=folium.Icon(color="green", icon="leaf"), tooltip="Árbol propuesto").add_to(pm)
    return pm


VOTE_MESSAGES = {
    "ok": "Voto registrado.",
    "changed": "Has cambiado tu voto.",
    "duplicate": "Ya habías votado eso en esta propuesta.",
    "wrong_barrio": "Solo pueden votar los vecinos empadronados en este barrio.",
}

with tab_vote:
    proposals = db.ranking(barrio_name)
    mine = [p for p in proposals if user and p.get("author_dni") == user["dni"]]
    if mine:
        st.markdown('<h2 class="display section-title">Tus propuestas</h2>', unsafe_allow_html=True)
        for p in mine:
            total = p["votes_for"] + p["votes_against"]
            position = next(i for i, q in enumerate(proposals, 1) if q["id"] == p["id"])
            with st.container(border=True):
                st.markdown(f"**{html.escape(p['title'])}**")
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("A favor", p["votes_for"])
                c2.metric("En contra", p["votes_against"])
                c3.metric("Apoyo", f"{100 * p['votes_for'] / total:.0f} %" if total else "—")
                c4.metric("Puesto", f"{position} de {len(proposals)}")
                c5.metric("Mejoras sugeridas", p["n_suggestions"])
                for sug in db.suggestions(p["id"]):
                    st.markdown(f'<div class="suggestion">{html.escape(sug["text"])}<br>'
                                f'<small>{html.escape(sug["name"])}, {sug["created"][:16]}</small></div>',
                                unsafe_allow_html=True)
        st.divider()

    st.markdown('<h2 class="display section-title">Propuestas del barrio</h2>', unsafe_allow_html=True)
    if not proposals:
        st.info("Todavía no hay propuestas en este barrio. Diseña la primera en «Diseña tu propuesta».")
    else:
        if guest:
            st.caption("Estás de visita: al pulsar «A favor» o «En contra» te pediremos iniciar sesión.")
        elif own_barrio:
            st.caption(f"Votas como {user['name']}: un voto por propuesta, a favor o en contra (puedes cambiarlo). "
                       "Las cifras de población son estimadas.")
        else:
            st.info(f"Solo los vecinos empadronados en {barrio_name.title()} pueden votar aquí.")
        efficiency = {p["id"]: p["cost"] / g for p in proposals if (g := p["elderly_after"] - p["elderly_before"]) > 0}
        best_id = min(efficiency, key=efficiency.get) if efficiency else None
        max_total = max(p["votes_for"] + p["votes_against"] for p in proposals) or 1
        for i, p in enumerate(proposals, 1):
            gain = p["elderly_after"] - p["elderly_before"]
            per_person = f"{fmt(efficiency[p['id']])} € por persona" if p["id"] in efficiency else "sin mayores nuevos cubiertos"
            badge = '<span class="best">La más eficiente</span>' if p["id"] == best_id else ""
            badge += '<span class="mine">Tu propuesta</span>' if user and p.get("author_dni") == user["dni"] else ""
            w_for, w_against = 100 * p["votes_for"] / max_total, 100 * p["votes_against"] / max_total
            row, action = st.columns([4, 2], vertical_alignment="center")
            row.markdown(
                f"""<div class="rank"><div class="rank-pos">{i}</div><div>
                <div class="rank-title">{html.escape(p['title'])}{badge}</div>
                <div class="bar split" role="img" aria-label="{p['votes_for']} a favor, {p['votes_against']} en contra">
                <div style="width:{w_for:.0f}%"></div><div class="against" style="width:{w_against:.0f}%"></div>
                <div class="none"></div></div>
                <div class="rank-meta">{p['votes_for']} a favor y {p['votes_against']} en contra. Propuesta de
                {html.escape(p['author'])}: {fmt(p['cost'])} €, {gain:+.0f} mayores con banco cerca, {per_person}.</div>
                </div></div>""",
                unsafe_allow_html=True,
            )
            current = db.my_vote(p["id"], user["dni"]) if user else None
            b_for, b_against = action.columns(2)
            for col, value, label in [(b_for, 1, "A favor"), (b_against, -1, "En contra")]:
                if col.button(label, key=f"vote_{p['id']}_{value}", disabled=not (guest or own_barrio), use_container_width=True,
                              type="primary" if current == value else "secondary"):
                    if guest:
                        require_login()
                    state.flash = VOTE_MESSAGES[db.vote(p["id"], user["dni"], value)]
                    st.rerun()
            showing = state.get("view_pid") == p["id"]
            if action.button("Ocultar mapa" if showing else "Ver en el mapa", key=f"map_{p['id']}",
                             use_container_width=True):
                state.view_pid = None if showing else p["id"]
                st.rerun()
            if showing:
                st_folium(proposal_map(p), key=f"pmap_{p['id']}", height=420, use_container_width=True,
                          returned_objects=[])
                st.caption("🟢 bancos y árboles propuestos · 🟧 manzanas que seguirían sin banco a ≤ "
                           f"{radius} m con esta propuesta")
            with st.expander(f"Mejoras sugeridas ({p['n_suggestions']})"):
                for sug in db.suggestions(p["id"]):
                    st.markdown(f'<div class="suggestion">{html.escape(sug["text"])}<br>'
                                f'<small>{html.escape(sug["name"])}, {sug["created"][:16]}</small></div>',
                                unsafe_allow_html=True)
                # Anyone can suggest improvements; only residents of the barrio vote.
                with st.form(f"suggest_{p['id']}", clear_on_submit=True, border=False):
                    text = st.text_area("Propón una mejora para esta propuesta",
                                        placeholder="Por ejemplo: que los bancos tengan respaldo y sombra…",
                                        max_chars=500)
                    if st.form_submit_button("Inicia sesión para enviar" if guest else "Enviar mejora"):
                        if guest:
                            require_login()
                        result = db.add_suggestion(p["id"], user["dni"], user["name"], text)
                        state.flash = {"ok": "Mejora enviada al autor de la propuesta.",
                                       "empty": "Escribe la mejora antes de enviarla."}[result]
                        st.rerun()
            st.divider()

# --- València verde: city-wide green data -------------------------------------------
with tab_green:
    green.render(barrio_name)
