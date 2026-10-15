# FTD — València Futura: proponer y votar reformas del barrio con impacto medido

**Estado:** spec aprobada (2026-10-15 ~15:00) · andamiaje hecho · **Fecha:** 2026-10-15

## Intención

Que un vecino diseñe una reforma de su barrio sobre un mapa con lo que ya existe (bancos, árboles, parques), vea su impacto calculado con datos municipales y la someta a votación. Así el voto es informado, no una lista de deseos.

**Objeción más fuerte:** VLCParticipa ya permite proponer y votar. La diferencia defendible es que aquí cada propuesta lleva un impacto **calculado y reproducible** (cobertura y coste), no un texto libre.

## Spec

**Problema:** las inversiones de barrio se proponen y votan sin ver qué hay ya en la zona ni cuánta gente beneficiarían. El Ayuntamiento espera las quejas en vez de detectar necesidades.

**Usuario:** vecino de València (propone y vota) y técnico municipal (compara propuestas antes de invertir).

**Objetivo:** en la demo, dos propuestas del mismo barrio se comparan con números (mayores cubiertos, coste, coste por persona beneficiada) y el ranking de votos muestra esos números junto a cada una.

### Dentro de alcance
- Elegir un barrio de València y ver en el mapa la **posición real** de bancos, árboles y parques/jardines existentes (datos del Ayuntamiento), con su recuento.
- Colocar bancos (y árboles) virtuales en el mapa.
- Indicador: **personas mayores de 65 años a ≤ R metros de un banco**, antes y después (distancia en línea recta).
- **Variables ajustables** visibles: radio de cobertura R, coste por banco, coste por árbol, % de población mayor, habitantes por manzana.
- Guardar la propuesta (título, autor, elementos, coste, impacto).
- Votación: un voto por vecino y propuesta; ranking con votos + coste + impacto + coste por beneficiado.
- Selector de "vecino" para simular varios usuarios en la demo.

### Fuera de alcance
- Rutas peatonales reales, sombra, accesibilidad, costes oficiales.
- Reparto de presupuesto entre propuestas (votación tipo b): diapositiva de ampliación.
- Autenticación real, despliegue en la nube.

### Criterios de aceptación
1. Dado un barrio elegido, cuando se carga, entonces el mapa muestra bancos, árboles y parques en su posición real y un panel con el recuento de cada uno.
2. Dado el barrio cargado, cuando añado un banco virtual, entonces el indicador "mayores cubiertos" y el coste se recalculan y se ve el antes/después.
3. Dado que cambio el radio R o el coste por banco, cuando se recalcula, entonces los números cambian de forma coherente (más radio ⇒ cobertura ≥ que antes).
4. Dado una propuesta guardada, cuando dos vecinos distintos la votan, entonces tiene 2 votos; si el mismo vecino vota dos veces, sigue contando 1.
5. Dado ≥ 2 propuestas, cuando abro el ranking, entonces aparecen ordenadas por votos con coste, mayores cubiertos y coste por beneficiado.
6. Toda cifra de población indica si es dato oficial o estimación.

### Cobertura de los criterios de evaluación
- **Demo real:** posiciones reales de 5.957 bancos, ~157.000 árboles y 807 zonas verdes del geoportal municipal; cálculo en vivo.
- **Utilidad pública:** prioriza la inversión con impacto medible antes de gastar dinero público.
- **Innovación defendible:** proponer + votar ya existe; proponer con impacto calculado y votar viéndolo, no.

### Puntos abiertos (suposiciones tomadas)
- ⚠️ **Población por edad:** la capa "Manzanas con datos de población" del geoportal publica **solo la geometría, sin campos de población** (comprobado el 2026-10-15). Suposición: manzanas reales + población **estimada** (habitantes por manzana y % de mayores como variables ajustables, etiquetadas como "estimación"). Si alguien del equipo encuentra el padrón por edades por barrio, se sustituye.
- Distancia en línea recta, no a pie.
- Costes ficticios y ajustables, no presupuestos oficiales.

## Checklist (andamiaje)
- [x] Repo git + `.gitignore` · prueba: `git status` limpio tras commit
- [x] `.venv` + `requirements.txt` mínimo · prueba: `pip install -r requirements.txt` sin errores
- [x] Demo de un comando (mapa de un barrio con bancos/árboles/parques reales) · prueba: se ejecuta y muestra el mapa
- [x] `README.md` y `CLAUDE.md` · prueba: comandos del README ejecutados literalmente

## Evidencia
- Copia limpia + comandos del README (Linux) → `pip install` OK, `streamlit run app.py` responde `/_stcore/health` = 200.
- AppTest sin excepciones; Russafa: 193 bancos, 522 árboles, 13 parques, 81 manzanas (CA1).
- Banco virtual en manzana sin cobertura (R=75) → mayores cubiertos 1.307 → 1.350 (+43), coste 800 €, 19 €/beneficiado (CA2).
- R 75 → 150 m: 1.307 → 1.541 (CA3).
- Votos: Ana+Luis en A = 2, Ana repetida ignorada; ranking A(2) > B(1) (CA4, CA5).
- Pendiente: probar clics reales en el navegador.

## Siguiente paso
Probar la demo en el navegador (clic → banco) y repartir tareas entre los 4.
