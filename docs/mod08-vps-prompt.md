# Prompt de continuación en el servidor — MOD-08

Copiar el bloque siguiente al agente que trabaje en el checkout del servidor.
El usuario autoriza instalar herramientas gratuitas y ejecutar estas pruebas
sintéticas. No implica desplegar cambios en producción ni usar datos reales.

```text
Continúa MOD-08 en este servidor. Primero sincroniza el código y después instala
los instrumentos y ejecuta los tests. Haz el trabajo, no te limites a proponerlo.

1. Identifica el checkout de epava1516/web_citas y lee AGENTS.md. Ejecuta git status,
   git fetch origin y, si el checkout está limpio y puede avanzar sin conflictos,
   git pull --ff-only origin master. No pierdas cambios locales ni uses reset --hard.
   Si hay cambios o divergencia, conserva ese checkout y crea un worktree aislado
   desde origin/master para estas pruebas. Registra el SHA completo que vas a medir.
   Comprueba que incluye scripts/run_vps_capacity.py, el instalador, el lock de
   herramientas y la corrección --init de scripts/check_capacity_environment.py.

2. Lee docs/mod08-vps-medicion.md, docs/evidencias/mod08-vps-preparacion-verificada-20261012.md,
   docs/16-contrato-ejecucion-desarrollo.md y el final de docs/17-seguimiento-desarrollo.md.
   Los perfiles de energía del portátil cambiaban mientras alternaba su cargador;
   no atribuyas sus diferencias a una optimización ni reproduzcas sus ajustes en
   el VPS. El servidor debe aportar sus propias mediciones y metadatos.

3. Prepara Linux/glibc, Docker local, Git y uv; instala sólo requisitos gratuitos
   que falten, sin sustituir servicios existentes. Usa el intérprete uv Python
   3.12.15 y uv sync --frozen --python 3.12.15. Instala los instrumentos mediante
   bash scripts/install_diagnostic_tools.sh, en venv separado de la aplicación.
   No cambies versiones ni hashes del lock para hacer pasar la instalación.
   Memray y Scalene deben quedar inactivos durante las mediciones HTTP.

4. Valida el kernel canónico native-sealed. Si falta, usa el builder y Cython
   3.0.12 aislado como indica el procedimiento. Si existe pero es inválido, conserva
   la evidencia y resuelve origen/ABI antes de reemplazarlo; nunca acepta fallback
   silencioso. Prepara las imágenes de Docker indicadas antes del intervalo medido
   y registra sus identidades. Mantén cuotas totales 4CPU/8GiB y almacenamiento
   propio limitado a20GiB. Si el host no puede soportarlas, informa incompatibilidad;
   no inventes equivalencia ni relajes el contrato.

5. Ejecuta Ruff, comprobación de docs y tests rápidos:
   uv run ruff check .
   uv run python scripts/check_docs.py
   uv run pytest -q tests/test_capacity_process_lifecycle.py tests/test_vps_capacity_handoff.py tests/test_capacity_worker_wsgi.py tests/test_capacity_preflight_contract.py tests/test_capacity_request_timing.py tests/test_capacity_delivery_samples.py tests/test_capacity_delivery_http.py

6. Ejecuta secuencialmente, sin editar las fuentes mientras un comando está vivo:
   uv run python scripts/run_vps_capacity.py preflight
   uv run python scripts/run_vps_capacity.py probe
   uv run python scripts/run_vps_capacity.py measure
   No ejecutes pruebas en paralelo ni sobre los servicios de producción. El runner
   utiliza PostgreSQL/Redis/RustFS/Caddy propios, red interna y datos sintéticos.
   Conserva fallos y verifica limpieza real de contenedores, red y volúmenes.
   No ocultes procesos vivos ni zombis al cerrar; --init es la corrección estándar.

7. Evalúa el resultado completo, no sólo números aislados. Exige cero fallos,
   errores y skips, fuentes sin cambios, intervalos concurrentes y cuerpos íntegros.
   Umbrales p95: navegación2s, JSON5s, binario5s. Dos casos,384 navegaciones y20
   descargas por tipo/caso. DELIVERY_STAGES_PASS_NOT_GLOBAL_CAPACITY_OR_N3 sólo
   acepta esas etapas, no N3 ni toda la capacidad del proyecto.
   Referencia local correctiva:1,611558/4,181215/4,166493s y1PASS909,989s;
   no es una garantía para otro hardware. Primera ejecución local falló en teardown
   y se conserva; el probe final real con init sí pasó.

8. Si measure cumple, repite una sola vez con el mismo SHA y entorno para comprobar
   reproducibilidad; informa ambas ejecuciones, no selecciones sólo la mejor.
   Si incumple o falla, corrige primero fallos del instrumento/topología. Para
   investigar rendimiento usa, en otra ejecución, exclusivamente:
   uv run python scripts/run_vps_capacity.py diagnose
   Este modo usa py-spy y observación PG y no acredita p95 contractual. No mezcles
   spans/cProfile/perfiladores antiguos, Memray o Scalene con esta captura. Examina
   CPU steal, presión y throttling antes de culpar al código. Investiga una hipótesis
   concreta con evidencia; no memoices autoridad ni adelantes lecturas mutables.
   Tras una corrección comprobada, permite un reensayo sin perfiladores. Si se repite
   el mismo bloqueo o falta evidencia útil, detén el bucle y documenta qué falta;
   no rebajes umbrales ni encadenes microoptimizaciones especulativas.

9. Guarda resultados y recibos bajo artifacts/, y un resumen verificable sin
   secretos en docs/evidencias/; actualiza docs/17-seguimiento-desarrollo.md y conserva
   el consumo previo de .ai/tasks/desarrollo.md. No subas .env, tokens, bases de
   datos, cuerpos privados, venvs o grandes artefactos temporales. No publiques,
   despliegues ni contrates servicios. No invoques otras cuentas/modelos sin el
   contrato aplicable. Cierra con tabla p95 por caso/ejecución, SHA, versiones,
   límites, estado de limpieza y lo que queda pendiente. El objetivo de este
   relevo es verificar instalación y rendimiento real en VPS, no declarar cierre
   global del proyecto sin sus otras puertas.
```
