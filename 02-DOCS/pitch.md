# Pitch — València Futura (2 minutos)

**Mensaje en una frase:** València Futura deja que los vecinos de València diseñen mejoras para su barrio sobre los datos reales del Ayuntamiento, vean al momento a cuánta gente llegan y cuánto cuesta, y las voten con su identidad verificada.

**Formato supuesto** (no hay bases): 2 min de pitch con demo en directo desde el portátil, presenta Samuel, sin slides obligatorias. ⚠️ por confirmar con la organización si hay turno de preguntas y si piden slides.

---

## 1. Guion cronometrado (≈ 270 palabras ≈ 1 min 55 s)

| Tiempo | Bloque | Qué se dice | En pantalla |
|---|---|---|---|
| 0:00–0:15 | **Gancho** | «En Russafa, **1.677 personas mayores** no tienen un banco donde sentarse a menos de 75 metros de casa. Nadie ha puesto una queja. Pero los datos del Ayuntamiento lo dicen.» | Portada: carrusel y cifras de la ciudad |
| 0:15–0:30 | **Problema** | «Hoy los presupuestos participativos funcionan con listas de deseos: se propone y se vota sin saber qué hay ya en la calle ni a cuánta gente llega cada euro. La administración espera a las quejas.» | Botón verde → login |
| 0:30–1:25 | **Solución + demo** | «València Futura cambia eso. Entro con mi DNI: solo votan los vecinos empadronados. Este es Russafa con sus datos reales: 193 bancos, casi 3.000 árboles y sus parques. En naranja, las manzanas sin banco cerca. Pongo un banco aquí, en la Gran Vía de Germanías… y al momento: **+59 mayores** con banco cerca, **800 €**, **14 € por persona**. Lo publico. Ahora entro como Luis, vecino del barrio: veo la propuesta en el mapa, la voto y propongo una mejora. Y Ana, la autora, ve sus votos a favor, en contra y las mejoras. Gana la mejor informada, no la más gritada.» | Ver guion de la demo |
| 1:25–1:45 | **Datos y cómo está hecho** | «Todo sale de los datos abiertos del Ayuntamiento: arbolado, bancos, zonas verdes, manzanas y barrios del geoportal municipal, más el índice de vulnerabilidad demográfica. Python y Streamlit, en tres horas. Las edades por manzana son una estimación porque no se publican; con el padrón, el cálculo sería exacto.» | Pestaña «València verde» (mapa coroplético) |
| 1:45–2:00 | **Cierre** | «Proponer y votar ya existe. Proponer **con el impacto medido**, no. València Futura convierte una administración que espera quejas en una que detecta lo que falta. ¿Por qué el Ayuntamiento no tiene ya algo así? Ya puede tenerlo.» | Volver al titular grande |

> Ritmo: ~140 palabras/min. Si vas justo, recorta el bloque de datos a una frase: «Todo son datos abiertos del Ayuntamiento».

## 2. Guion de la demo, clic a clic

Preparación (antes de salir): app abierta en http://localhost:8501 en pantalla completa (F11), en la **portada**, sin propuestas previas (ya borradas) o con la definitiva publicada.

1. **Portada** → pulsar **«Haz de tu barrio un lugar más verde»**. El jurado ve: login centrado sobre el carrusel.
2. **Login**: `11111111H` / `1234` → **Entrar**. Ve: titular «1.677 personas mayores de Russafa…», mapa de Russafa, barra lateral con las variables.
3. **Mapa**: «Colorea por» = **Banco cerca**. Señalar las manzanas **naranjas**.
4. **Clic** en la manzana naranja junto a la **Gran Vía de Germanías** (lado norte del barrio). Ve: marcador marrón, «Mayores con banco a ≤ 75 m» **+59**, coste **800 €**, **14 € por persona**.
   - ⚠️ No uses la manzana grande del suroeste (junto a la calle Filipinas): por su tamaño la estimación le asigna muchísima población (+1.038, 1 €/persona) y no es creíble.
5. Nombre «Más bancos y sombra en Russafa» → **Publicar propuesta**. Ve: aviso «Propuesta publicada».
6. **Cerrar sesión** → portada → botón verde → `22222222J` / `1234` (Luis).
7. Pestaña **Vota las propuestas** → **Ver en el mapa** → **A favor** → abrir «Mejoras sugeridas» → escribir «Que tengan respaldo» → **Enviar mejora**.
8. (Si sobra tiempo) Cerrar sesión → entrar como Ana → **Tus propuestas**: 1 a favor, 0 en contra, 100 % de apoyo, 1 mejora.
9. Pestaña **València verde**: mapa de los 88 barrios por m² verdes por hectárea.

Recorte si vas mal de tiempo: haz 1–5 y cuenta 6–8 de palabra.

## 3. Plan B de la demo

- **Si la app no carga en 10 s** o el wifi falla: los datos de Russafa, Benimaclet y otros barrios están en caché local (`data/cache/`), así que la app funciona sin internet; solo el mapa base (calles de OpenStreetMap) necesita red.
- **Si el mapa base no carga**: el resto sí (manzanas, bancos, árboles, cifras). Sigue con la demo diciendo «sin el fondo de calles, pero con todos los datos».
- **Si se cae el servidor**: relanzar con `cd Hackathon_proyecto && source .venv/bin/activate && streamlit run app.py` (tarda ~5 s).
- ⚠️ por hacer: grabar un vídeo de 60 s del recorrido 1–7 o 5 capturas (portada, login, banco con +59, votación, València verde) como respaldo.

## 4. Slides (solo si las piden; 5)

1. **«1.677 mayores de Russafa sin un banco a 75 m»** — el titular de la app a pantalla completa.
2. **El problema** — proponer y votar sin datos (logo/captura de un sistema de propuestas genérico, sin marcas).
3. **La solución** — captura del mapa con manzanas naranjas y el panel +59 / 14 € por persona.
4. **Vota quien vive allí** — captura de login + votación a favor/en contra + mejoras.
5. **Datos abiertos, impacto medido** — logos de fuentes en texto: geoportal municipal, opendata València, criterio OMS.

## 5. Cobertura de criterios (de `02-DOCS/reto.md`)

| Criterio | Dónde se demuestra |
|---|---|
| **Demo real** | 0:30–1:25: demo en directo con datos reales del geoportal (193 bancos, 2.945 árboles en Russafa) y cálculo en vivo |
| **Utilidad pública** | Gancho (necesidad detectada sin quejas) + € por persona para priorizar dinero público + votación verificada |
| **Innovación defendible** | Cierre: frente a VLCParticipa, la propuesta lleva el impacto medido y el voto es informado |

## 6. De dónde salen los datos

| Dato | Fuente | Qué usamos |
|---|---|---|
| Bancos | Geoportal del Ayuntamiento, capa *Bancos en vía pública* (`SociedadBienestar/MapServer/32`) | 5.921 bancos con posición |
| Arbolado | Geoportal, capa *Arbolado* (`MedioAmbiente/MapServer/151`) | 156.223 árboles, especie y posición |
| Parques y jardines | Geoportal, capa *Espacios verdes* (`MedioAmbiente/MapServer/8`) | 807 zonas verdes, 523 ha |
| Manzanas | Geoportal, capa *Manzanas con datos de población* (`UrbanismoEInfraestructuras/MapServer/215`) | Forma de cada manzana (la capa **no** trae población) |
| Barrios | Geoportal, capa *Barrios* (`UrbanismoEInfraestructuras/MapServer/224`) | 88 barrios |
| % de mayores y niños por barrio | Portal opendata.vlci.valencia.es, *Vulnerabilidad por barrios 2021* (índice demográfico) | Estimación: medias de la ciudad (22 % y 13 %) ajustadas por el índice |
| Zona verde cerca | Criterio de la OMS Europa (2016): ≥ 0,5 ha a ≤ 300 m | Frase de los niños del titular |
| Fotos | Wikimedia Commons, CC BY / CC BY-SA (`static/CREDITS.md`) | Carrusel |

**Estimaciones (decirlo si preguntan):** habitantes por manzana = 150 × tamaño relativo de la manzana; % de edades por barrio a partir del índice; distancias en línea recta; costes orientativos (800 € banco, 400 € árbol); usuarios de prueba ficticios.

## 7. Preguntas probables del jurado

1. **¿Los datos de población son reales?** — Las posiciones de bancos, árboles, parques y manzanas sí. Las personas por manzana y edad son una estimación, porque el Ayuntamiento no las publica; con el padrón, el cálculo sería exacto sin cambiar la herramienta.
2. **¿En qué se diferencia de VLCParticipa / Decidim?** — Allí se propone texto y se vota. Aquí la propuesta se dibuja sobre datos reales y lleva su impacto y coste calculados; el voto es informado.
3. **¿Cómo evitáis votos falsos?** — Login con DNI y clave (simula Cl@ve + padrón): solo votan empadronados, un voto por propuesta, cifrado con hash. Proponer y sugerir lo puede hacer cualquiera.
4. **¿Por qué 75 metros?** — Es un parámetro ajustable en la barra lateral; el técnico municipal lo fija según su criterio de accesibilidad.
5. **¿Escala a toda la ciudad?** — Sí: funciona con los 88 barrios y descarga del geoportal bajo demanda; los agregados de ciudad se calculan en el servidor del Ayuntamiento.
6. **¿Usa IA?** — No: todo es cálculo reproducible sobre datos abiertos; preferimos que cada cifra se pueda comprobar.
7. **¿Qué haríais con más tiempo?** — Padrón por edades real, rutas a pie en lugar de línea recta, sombra y costes oficiales, y despliegue con Cl@ve real.
8. **¿Qué pasa con los árboles en el coste por persona?** — Suman coste pero el indicador solo cuenta mayores con banco cerca; los árboles tienen su propio indicador (manzanas con árbol cerca).
