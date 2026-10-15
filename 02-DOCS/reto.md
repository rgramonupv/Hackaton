# Reto

**Tema:** Transformación digital: idear soluciones que modernicen las administraciones públicas y mejoren sus servicios mediante nuevas tecnologías.

## Entregables
- Demo real funcionando + presentación al jurado.

## Fechas y duración
- 2026-10-15, **3 horas** de desarrollo (inicio de sesión ~14:13).

## Criterios de evaluación (no hay bases oficiales; criterios propios del equipo)
1. **Demo real**: funciona en vivo con datos reales, no un mockup.
2. **Utilidad pública**: resuelve una necesidad municipal concreta.
3. **Innovación defendible**: aporta algo que no existe (VLCParticipa ya permite proponer y votar).

Sin pesos: se consideran iguales.

## Restricciones
- Equipo: 4 personas.
- Datos: abiertos del Ayuntamiento de València (geoportal / opendata.vlci.valencia.es).
- Lenguaje: Python.

⚠️ No especificado: bases oficiales, jurado, formato y duración del pitch, criterios con peso.

---

## Texto original (correo del equipo, 2026-10-15 14:36)

Vamos a por una idea que pueda ganar la hackathon

Estoy de acuerdo con cambiar de enfoque. No quiero que presentemos otro
chatbot con IA y un diseño bonito. Quiero que construyamos algo que, al
enseñárselo al jurado, provoque esta reacción:

«¿Por qué el Ayuntamiento no tiene ya algo así?»

He investigado qué herramientas existen actualmente en València y hay tres
descubrimientos importantes:

   -

   El Ayuntamiento dispone de un Geoportal con cientos de capas de
   información municipal.
   València

   -

   Ya existen presupuestos participativos donde los ciudadanos pueden
   proponer y votar inversiones.
   VLCParticipa

   -

   Hay datos abiertos sobre árboles, obras, bancos, equipamientos públicos
   e incluso población por edades y manzanas.
   Conjunto de datos
   +2


La oportunidad es transformar esos datos en una herramienta que permita
hacer algo nuevo, no simplemente consultarlos.

Y mantengo las condiciones: cuatro personas, tres horas, una demostración
real, utilidad pública e innovación que se pueda defender.
Tres propuestas mucho más originales
[image: Redibujando el ensanche de Barcelona en Sant Antoni por Leku Studio
| METALOCUS]
1. VALÈNCIA LAB

Un simulador donde los ciudadanos transforman su barrio antes de que el
Ayuntamiento invierta.

Imagina seleccionar una calle real, añadir bancos, árboles o zonas de
sombra y ver visualmente el antes y después, junto con el presupuesto
estimado y los vecinos potencialmente beneficiados.

No es una plataforma para votar propuestas: es una herramienta para
experimentar, comparar alternativas y justificar inversiones públicas.

Innovación: muy alta · Demo visual: muy alta · Riesgo técnico: medio
[image: Digitale Stadt | Landeshauptstadt Wiesbaden]
2. OBRA ZERO

Un detector de conflictos entre obras municipales antes de ejecutarlas.

Un sistema visual donde distintas actuaciones se sitúan en un calendario y
mapa. Si dos obras coinciden en la misma zona y fechas, identifica posibles
conflictos y permite simular otras fechas.

Beneficio directo: mejor coordinación municipal, menos molestias para
residentes y menos riesgo de interrupciones en los servicios.

Innovación: alta · Demo visual: alta · Riesgo técnico: bajo-medio
[image: How to: compute and save heatmaps, and to compute predictions with
Python | Snap4City]
3. LA CIUDAD INVISIBLE

Un sistema que detecta dónde faltan servicios públicos, aunque nadie haya
presentado una queja.

Cruza datos de población y equipamientos. Por ejemplo, identifica zonas con
muchas personas mayores y pocos bancos cercanos. Permite colocar
virtualmente un banco nuevo y calcular cuántos residentes adicionales
quedarían dentro de un radio de cobertura.

Cambiamos una Administración que espera reclamaciones por otra capaz de
identificar necesidades de forma proactiva.

Innovación: muy alta · Demo visual: alta · Riesgo técnico: bajo
Mi elección: combinar lo mejor de VALÈNCIA LAB y LA CIUDAD INVISIBLE

El proyecto se llamaría VALÈNCIA FUTURA — El laboratorio de tu ciudad.

No lo enfocaría como un mapa convencional ni como un videojuego sin
utilidad. Sería una herramienta de planificación urbana participativa
basada en necesidades detectadas mediante datos municipales.
Así sería la demostración

Simulación de inversión pública
Ejemplo ilustrativo

Seleccionamos una zona urbana y estudiamos qué sucede cuando añadimos
servicios.

Bancos nuevos

2

Árboles nuevos

3

Presupuesto hipotético
4000 €

Elementos añadidos
5
Precios ficticios únicamente para demostrar la interacción, no presupuestos
oficiales. En el MVP, los resultados de cobertura se calcularían con
coordenadas y población de una zona seleccionada.

Lo realmente innovador llegaría cuando el sistema mostrase algo como:

«La propuesta A mejora la cobertura de bancos para residentes mayores de 65
años más que la propuesta B con el mismo presupuesto».

Esa conclusión tendría que proceder de un cálculo reproducible con datos
reales, no de una respuesta inventada por IA.
¿De verdad podemos hacerlo en tres horas?

Sí, si concentramos el MVP en una sola necesidad pública: la distribución
de bancos urbanos en relación con la población mayor.

Tenemos fuentes oficiales para ello: el Ayuntamiento publica las
ubicaciones de bancos y datos de población por edades a escala de manzana.
Conjunto de datos
+1

Persona

Trabajo paralelo

1

Mapa interactivo con selección de zonas y colocación virtual de bancos

2

Tratamiento de datos oficiales y cálculo de cobertura por proximidad

3

Interfaz de simulación, presupuesto y comparación de escenarios

4

Integración, pruebas, narrativa y presentación

El cálculo inicial usaría distancias en línea recta, no rutas peatonales
reales. La futura versión podría incorporar accesibilidad, recorridos,
sombra y costes oficiales. Es importante que el jurado distinga la prueba
de concepto de un modelo urbanístico validado.

El reparto temporal sería 20 minutos de definición y preparación de datos,
115 minutos de construcción paralela y 45 minutos de integración, pruebas y
presentación.
Comparación final

Criterio

València Lab

Obra Zero

Ciudad Invisible

Originalidad del enfoque

5/5

4/5

5/5

Utilidad pública

5/5

5/5

5/5

Facilidad de construir

3/5

4/5

4/5

Impacto visual de la demo

5/5

4/5

4/5

Potencial de ampliación

5/5

4/5

5/5
Valoración propia, orientativa, según las restricciones de la hackathon.

Mi apuesta sería VALÈNCIA FUTURA, con el motor de detección de necesidades
de La Ciudad Invisible. Me parece una propuesta con mejor equilibrio entre
creatividad, relevancia municipal y capacidad de enseñar un resultado
auténtico en tres horas.

Además, el proyecto tiene una defensa potente: la Administración no solo
facilita servicios existentes; utiliza sus datos para descubrir dónde hacen
falta nuevos servicios y permite estudiar inversiones antes de gastar
dinero público.

Quiero que nos quedemos con esa ambición: no digitalizar un formulario,
sino cambiar cómo se detectan y resuelven las necesidades de los ciudadanos.


## Idea de Samuel (2026-10-15)

Simulador donde el público propone reformas sobre sus barrios y, mediante un sistema de votos, se eligen las mejores propuestas. La demo debe mostrar si ya hay bancos, árboles y parques en la zona y su posición; todo como variables para ayudar a decidir, usando datos del Ayuntamiento.
