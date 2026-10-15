# València Futura — el laboratorio de tu barrio

Web donde los vecinos de València diseñan reformas de su barrio sobre el mapa (bancos, árboles) viendo lo que ya existe, con su impacto calculado con datos abiertos del Ayuntamiento, y votan las mejores propuestas.
Proponer y votar ya existe (VLCParticipa); aquí cada propuesta lleva su impacto medido: mayores de 65 años a menos de R metros de un banco, coste y € por beneficiado.

## Requisitos
- Python 3.11+ e internet (la primera vez que abres un barrio se descargan sus datos del geoportal; después quedan en `data/cache/`).

## Instalación y ejecución

Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Se abre en el navegador en http://localhost:8501.

## Cómo se usa
1. Elige barrio y vecino en la barra lateral; ajusta las variables (radio, costes, población).
2. **Simulador:** haz clic en el mapa para añadir bancos o árboles. Las manzanas en rojo no tienen banco a ≤ R m.
3. Publica la propuesta y vótala en la pestaña **Votación** (un voto por vecino y propuesta).

## Datos
| Capa | Fuente (geoportal.valencia.es, OPENDATA) |
|---|---|
| Bancos | SociedadBienestar/MapServer/32 |
| Arbolado | MedioAmbiente/MapServer/151 |
| Espacios verdes | MedioAmbiente/MapServer/8 |
| Manzanas | UrbanismoEInfraestructuras/MapServer/215 |
| Barrios | UrbanismoEInfraestructuras/MapServer/224 |

⚠️ La población por manzana es una **estimación** (habitantes medios × área relativa × % mayores): el geoportal publica las manzanas sin campos de población. Distancias en línea recta; costes ficticios y ajustables.

## Código
- `app.py` — interfaz Streamlit (mapa, simulador, votación)
- `data.py` — descarga y caché de capas del geoportal
- `model.py` — cálculo de cobertura y población estimada
- `db.py` — propuestas y votos en SQLite (`data/valencia_futura.db`)
