# Astra — verificación de la demo y ciclo del borrador

Fecha: 2026-10-15. Base comprobada: `d982e89bd1e6ac49110a2c3ccb5e6ef1b93c8921`.
Rama: `feat/astra-mapa`; destino de revisión: `main`. Worktree: `C:/Hackaton-astra`.

Durante la auditoría Opus publicó `569d64cafb63f017167c5b4edc967a2f5acf20d2`.
Se verificó por separado en `C:/Hackaton-astra-check-569d64c` (HEAD desacoplado),
copiando únicamente nuestros tests/helpers nuevos. **No se hizo merge ni rebase.**
La rama entregada conserva la base acordada `d982e89`. Los tests aceptan ambas
variantes de etiquetas y formato numérico. `model.py`, `data.py`, `db.py` y los
requisitos son idénticos entre ambos commits.

## Resultado y alcance

**La demo NO queda certificada de extremo a extremo.** El servidor arranca y los
cálculos, costes y votos pasan las pruebas automatizadas. En Edge, el componente
`streamlit_folium.st_folium` queda en blanco y termina con timeout. No se han podido
verificar clics reales ni publicar/votar propuestas desde ese navegador.

No se han modificado `app.py`, `model.py`, `data.py`, `db.py`, configuración,
dependencias ni cachés versionadas. No se ha reconstruido el mapa. Solo se añaden este informe,
`ui/astra_map.py`, `tests/test_astra_map.py` y `tests/astra_preview.py`.

El código de Opus ya implementa mapa, simulación, propuestas y votos. El commit
`03c80fd` aporta el andamiaje y `d982e89` el tema visual; ambos acreditan a Opus.

## Entorno y reproducción

Windows, CPython 3.12.15; dependencias EXACTAS de `requirements.txt`:
Streamlit 1.66.0, Folium 0.20.0, streamlit-folium 0.27.4, pandas 3.0.6,
NumPy 2.5.4, requests 2.34.2. No había Python operativo: se preparó un intérprete
con uv y `.venv` exclusivo del worktree, sin cambiar los requisitos del proyecto.

Desde la raíz del checkout aislado, PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m compileall -q app.py model.py data.py db.py ui tests
.venv/Scripts/python.exe -m streamlit run tests/astra_preview.py --server.address 127.0.0.1 --server.port 8511 --server.headless true
```

Abrir `http://127.0.0.1:8511`. El lanzador ejecuta el `app.py` original con
`runpy` y redirige únicamente `db.DB_PATH` en ese proceso a un directorio temporal.
No usarlo para propuestas reales. Los tests también parchean únicamente la ruta
SQLite, bloquean descargas HTTP en las pruebas de aplicación y usan los GeoJSON
versionados. El componente Folium se sustituye por eventos controlados SOLO en
AppTest, nunca en el navegador. AppTest ejecuta la aplicación/modelo/SQLite reales.

La suite tiene **14 pruebas**. Sobre `d982e89`: **12 pasan y 2 fallan**. Sobre
`569d64c`: **13 pasan y 1 falla**, exclusivamente CA5. El refresco tras guardar
ya está corregido por Opus en `569d64c`, comprobado ejecutando el test.
Los fallos conocidos NO se omiten ni se marcan como éxitos: el comando devuelve
código 1 hasta corregirlos. La compilación Python pasa en ambos checkouts.
La versión `569d64c` también se arrancó con el lanzador en el puerto 8512:
health=200, interfaz nueva visible en Edge y el mismo aviso de componente
Folium sin cargar. Los resultados de radio 75/100/150 y cambio de barrio
descritos abajo se observaron en la base `d982e89`.

## Los seis criterios originales y evidencia

Fuente: `02-DOCS/ftd/valencia-futura.md`. Se conservan aquí sus definiciones exactas.

| Criterio | Automatización | Navegador y conclusión |
|---|---|---|
| 1. Dado un barrio elegido, cuando se carga, entonces el mapa muestra bancos, árboles y parques en su posición real y un panel con el recuento de cada uno. | AppTest comprueba 193 bancos, 522 árboles, 13 parques, 81 manzanas en Russafa; inspecciona los marcadores Folium y el orden lat/lon contra la caché. | Recuentos y selección vistos en Edge: Russafa y Benicalap (323/520/49/210). **Parcial: mapa en blanco**, posiciones no verificadas visualmente. No se ha auditado la exactitud del inventario municipal fuera de la caché. |
| 2. Dado el barrio cargado, cuando añado un banco virtual, entonces el indicador "mayores cubiertos" y el coste se recalculan y se ve el antes/después. | Evento inyectado en una manzana sin cobertura aumenta cobertura y coste a 800 €. Repetir el retorno del componente o cambiar el radio no duplica el banco. Árbol: +400 €, sin aumentar cobertura de bancos. | **Clic real bloqueado** por componente. La interfaz ofrece después y delta; no dos valores explícitos antes/después. El refresco al guardar falla en `d982e89` y pasa en `569d64c`. |
| 3. Dado que cambio el radio R o el coste por banco, cuando se recalcula, entonces los números cambian de forma coherente (más radio ⇒ cobertura ≥ que antes). | Monotonía para R=25..300; límites de distancia; costes reales de la UI: banco+árbol 1.200 €, banco a 1.000 € → 1.400 €; controles de población escalan la estimación. | Radio comprobado en Edge: 75 m → 1.307; 100 m → 1.431; 150 m → 1.541. Coste con propuesta comprobado en AppTest, no con clic real. |
| 4. Dado una propuesta guardada, cuando dos vecinos distintos la votan, entonces tiene 2 votos; si el mismo vecino vota dos veces, sigue contando 1. | SQLite temporal: Ana+Luis=2, Ana repetida=1. También se ejercitan guardar y botones de voto de la UI mediante AppTest. Un vecino puede votar propuestas distintas. | No verificado de extremo a extremo en navegador. **Pasa automatizado**. |
| 5. Dado ≥ 2 propuestas, cuando abro el ranking, entonces aparecen ordenadas por votos con coste, mayores cubiertos y coste por beneficiado. | Orden, persistencia de antes/después, coste y €/beneficiado correctos. **Fallo conocido en ambos commits:** UI solo muestra ganancia (en `569d64c`, «+N mayores con banco cerca»), no total cubierto. | **No cumple completamente** la definición exacta. No se da por resuelto aunque los datos estén en SQLite. |
| 6. Toda cifra de población indica si es dato oficial o estimación. | Inspección de UI: caption de estimación en simulador y votación; tooltips de manzanas con «est.». AppTest comprueba las etiquetas de contexto. | Sidebar y total «mayores estimados» vistos. Tooltips y ranking no comprobados visualmente por el bloqueo. **Verificación parcial en navegador**, revisión estática y automatizada del contexto. |

## Incidencias y propuestas para Opus

### P0 — Folium no termina de cargar en Edge

Reproducido con `127.0.0.1` y `localhost`, incluso tras recargar. La interfaz
Streamlit funciona y recalcula el radio. Consola:

```text
Your app is having trouble loading the streamlit_folium.st_folium component.
Client Error: Custom Component streamlit_folium.st_folium timeout error
```

`/_stcore/health`, el HTML del componente y su JS local devuelven HTTP 200.
No hay excepción Python en el servidor. Esto acota el problema al arranque del
componente en navegador, pero **no demuestra su causa**: no atribuirlo aún a la
red, al navegador o a una versión concreta. No se modificaron dependencias,
seguridad del navegador ni archivos de Opus para sortearlo.

Acción: ejecutar este mismo lanzador en el portátil de presentación y abrir
DevTools → Console/Network. Verificar el iframe y los recursos del componente,
Leaflet y teselas; guardar el primer error concreto. Probar otro navegador
disponible sin cambiar configuraciones de seguridad. No dar P1–P3 por aprobados
hasta ver el mapa y completar el guion inferior.

### Resuelto por Opus en 569d64c — métricas desactualizadas tras guardar

Reproducción automática: un banco → publicar → `state.new_benches == []`, pero
la tarjeta sigue mostrando `800 €`, no `0 €`. Los números se calcularon antes
de guardar, mientras los marcadores se dibujan después de vaciar la lista.
Test: `test_known_issue_save_must_refresh_empty_draft_metrics`.

El nuevo commit de Opus añade `flash` y `st.rerun()` tras guardar: el test ahora
pasa. **No aplicar de nuevo esa corrección sobre la versión actual.** Los helpers
inferiores son opcionales para separar la identidad del mapa por barrio/borrador,
y no son necesarios para repetir el arreglo de Opus.

Se propone un reinicio completo del ciclo del borrador y una nueva identidad del
componente. `ui/astra_map.py` contiene solo dos helpers sin dependencias nuevas:

- `map_component_key(barrio, state) -> str`: clave por barrio y generación.
- `reset_proposal(state) -> None`: vacía bancos/árboles, reinicia `last_click` e
  incrementa `astra_map_revision`. Conserva vecino, parámetros y otros campos.

**Integración opcional por Opus en `app.py`:** el ejemplo completo siguiente
describe la base `d982e89`. En `569d64c`, conservar su mecanismo `flash`/rerun y
solo valorar reset+clave; no sustituir su bloque de guardado.

```python
from ui.astra_map import map_component_key, reset_proposal

# En la llamada EXISTENTE a st_folium, mantener todos los demás argumentos:
# key=map_component_key(barrio_name, state)

# Dentro del botón Deshacer todo:
reset_proposal(state)
st.rerun()

# Después de db.save_proposal(...) exitoso, en lugar de solo vaciar listas:
reset_proposal(state)
state["astra_saved_notice"] = True
st.rerun()

# Al principio de tab_sim, antes de dibujar controles:
if state.pop("astra_saved_notice", False):
    st.success("Propuesta publicada. Ve a la pestaña Votación.")
```

Integrar reset+clave+rerun juntos. Cambiar solo `last_click=None` con la misma
clave puede volver a consumir el evento anterior. La clave por barrio también
separa eventos entre barrios. Estos helpers están probados aisladamente; **no
están conectados ni validados en navegador**. No aseguran por sí solos que el
iframe cargue ni rechazan clics fuera del polígono.

### P1 — Ranking incompleto respecto a CA5

Mantener la ganancia y añadir `p['elderly_after']` con etiqueta
«Mayores cubiertos (estimación)»; conservar el caption de estimación y €/beneficiado
calculado sobre `after-before`. Test:
`test_known_issue_ca5_ranking_must_show_total_covered`.

### Observaciones secundarias

- `with sqlite3.Connection` hace commit/rollback, pero no cierra la conexión. En
  Windows quedaron archivos temporales ocupados hasta recoger el GC. El fixture
  ejecuta `gc.collect()` antes de borrar SU directorio temporal. No se ha cambiado
  `db.py`; Opus puede cerrar explícitamente conexiones con `contextlib.closing`.
- A 1272 px la etiqueta de cobertura se trunca. Mejor mostrar antes/después con
  etiquetas cortas y mantener el radio visible; no se alteró el diseño compartido.
- Los datos de población son estimados y las distancias rectas. Árboles no aportan
  cobertura de bancos: es comportamiento esperado, no un fallo.

## Guion de navegador pendiente (sobre SQLite temporal)

1. Arrancar el lanzador anterior. Russafa, R=75, banco=800 €, árbol=400 €,
   habitantes=150, mayores=22 %. Ver mapa, parques y recuentos 193/522/13.
2. En modo Banco, hacer UN clic en una manzana roja. Esperar el rerun: exactamente
   1 banco nuevo, coste 800 €, cobertura no inferior a 1.307 y delta coherente.
   Si se pulsa una zona ya cubierta, delta cero es válido.
3. Cambiar R a 150: cobertura no disminuye; sigue habiendo 1 banco, coste 800 €.
   Cambiar banco a 1.000 €: coste 1.000 €, no aparece otro marcador.
4. Elegir Árbol y clicar en otra posición: 1 banco + 1 árbol, coste 1.400 €.
   La cobertura de bancos no cambia al añadir solo el árbol. Cambiar de pestaña
   y volver: ningún elemento duplicado.
5. Deshacer: 0/0, coste cero, cobertura base. Volver a colocar en el mismo punto;
   comprobar que acepta la nueva propuesta y no recupera un clic antiguo.
6. Publicar A. Confirmar persistencia en Votación y coherencia del borrador vacío
   al volver. Crear y publicar B con otra ubicación; comprobar campos del ranking.
7. Ana vota A dos veces: 1 voto. Cambiar a Luis, votar A: 2 votos. Votar B una vez;
   comprobar A antes que B y coste, total cubierto estimado y €/beneficiado.
8. Cambiar Russafa → Benicalap → Russafa: borrador vacío, sin marcadores del otro
   barrio. Verificar recuentos y centro. Revisar estimación en métricas/tooltips/ranking.

## Seguridad, publicación e incorporación

Auditoría: `git fetch origin`, `git ls-remote --heads origin`, `git status`,
`git branch -a -vv`, `git log`, `git worktree list`, `git diff`. Base remota
confirmada antes de crear rama. Ningún merge/rebase/cherry-pick ni modificación
de `main`. No se usa `git add .`. El checkout original permanece limpio.
Durante las sesiones de navegador aparecieron cuatro cachés nuevas `*_122.geojson`
en el worktree de pruebas. Se dejan sin añadir y fuera del commit; no se eliminan
ni se publican. Los únicos archivos incluidos son los cuatro enumerados arriba.

Para revisar sin tocar el checkout de otro compañero:

```powershell
git fetch origin
git worktree add --detach ../Hackaton-astra-review origin/feat/astra-mapa
cd ../Hackaton-astra-review
# Crear .venv e instalar requirements.txt; ejecutar comandos de verificación.
```

La PR hacia `main` incorpora solamente estos archivos nuevos. No activa los
helpers ni corrige automáticamente `app.py`. Tras revisión, el responsable de
integración decide cómo incorporar la PR y aplica los fragmentos anteriores en
su propio trabajo; ejecutar de nuevo la suite y el guion real de navegador.

Prioridades antes del jurado: (1) resolver/verificar el iframe en el equipo de la
demo; (2) añadir total cubierto al ranking (refresco ya corregido por Opus); (3) ensayar
dos propuestas, dos vecinos y cambio de radio con el guion completo.
