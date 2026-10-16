# Imagen sin bytecode del host: publicación y supresión sobre PostgreSQL

La primera selección en imagenbb8bc8e5497c terminó17PASS/2FAIL252,11s. Los dos límites48/49 no llegaron a sus aserciones: el generador sintético rechaza `test_ci` y exige `test_promotion_gate_*`. No se cambia esa protección. Adaptador corregido para crear base `promotion_gate_ci` en PostgreSQL propio, con testDB `test_promotion_gate_ci`. No es una autorización para ejecutar el generador en bases normales.

Durante la revisión de trazas se comprobó además que `.dockerignore` no excluía cachés anidadas:583pyc de tests dentro de la imagen antigua, con rutas del host. Sus hashes de fuente no bastaban para descartar lectura de bytecode previo; no se acepta esa imagen como evidencia común final. Se conservan su resultado y logs. Se añaden exclusiones recursivas `**/__pycache__`, `**/*.pyc`, `**/*.pyo` y cachés de pytest/Ruff, sin cambiar código funcional.

Nueva construcción terminalexit0, **`web-modelos-cr09-native:20261016-v2`**, IDsha256:1c4a9aca45f343f2f59595a7038bf5f02082104521151d9a8f2e18f36b628705. Reutiliza la compilación nativa validada dentro del builder; no incorpora el artefacto del host. Base de etiqueta536ad2e más `.dockerignore` modificado con hash expreso. [Recibo completo](cr09-docker-pg-journeys-terminal-20261016.json).

| Selección en imagen v2 | Casos PASS | Fallos/errores/skips |
| --- | ---: | ---: |
| Publicación, cobertura, pertenencia, recuperación y material final | 19 | 0/0/0 |
| Kernel, equivalencia nativa y límites de pila | 118 | 0/0/0 |

La primera selección tarda258,56s;la segunda11,61s. Son dos selecciones secuenciales en la misma imagen, no una regresión integral/N3 ni casos adicionales por sumar intentos anteriores. Pruebas existentes sin cambios y kernel native-sealed binario2caa578c…. Testigo previo exige cero pyc enapps/tests; hashes de9fuentes evaluadas coinciden host/imagen. La nueva batería del kernel sustituye la incertidumbre de cachés de la imagen anterior.

Las19pruebas cubren censo current/missing/old_version/inherited, frontera48/49 del fallback, conteo exacto y orphanFKdiferido, pertenencia y filtros/páginas ESEN con referencia nativa, copia restaurada seleccionada/no seleccionada y materialfinal pending ante reintroducción de publicación. No son pruebas de navegador ni carga Gunicorn. Las118 cubren el kernel y sus negativos según [detalle anterior](cr09-docker-kernel-parity-20261016.md), ahora sobrev2.

App de pruebas UID10001/raízro/redinterna,sin puertos publicados,2CPU/3584MiB,sin swap,pids512,tmpfs1GiB. PG1CPU/1536MiB,pids128,tmpfs768MiB;Redis0,2CPU/128MiB,pids64,sin persistencia. Red/PG/Redis exclusivos, datos sintéticos, tareas eager donde lo fija el fixture; no worker real inferido. Pytest y dependencias de herramientas en montaje separado y readonly, sin sustituir dependencias de aplicación. Playwright se importa como dependencia de fixtures, no se inicia navegador ni proveedor. Autoload deshabilitado y plugin pytest-django explícito. Identidades/versiones en recibo.

Fuentes verificadas, contenedores/red propios e intermediarios de construcción ausentes de forma independiente. Logs,JUnit,testigos,inspecciones y adaptadores en `artifacts/cr09-docker-pg-journeys{,-v2}-20261016/`, `artifacts/cr09-docker-native-v2-20261016/` y `artifacts/cr09-docker-kernel-parity-v2-20261016/`. Ruff y docs comprobados tras cierre.

**Sin nuevo p95 ni aceptación CR09/N3.** La imagen corregida queda disponible para posteriores recorridos/capacidad. Las mediciones del host y el runner de capacidad que monta checkout/venv no se convierten por esto en medición del runtime empaquetado. Se conservan los pendientes del directorio, reproducibilidad, carga larga y versión común integral.
