# N01 — Primer lote de diagnóstico de descubrimiento

25 de octubre de 2026. Prerregistro anterior a ejecución y a cualquier cambio de producto. N00 aceptado por [343](343-n00-aceptacion-local-20261025.md); N01 en curso. Este lote inicia S01/N04/I01–I04 por una muestra acotada; no acepta N01 completo ni la ficha pública, promociones, ES/EN entero, páginas profundas o navegador.

## Hipótesis, selección y base

Existe evidencia contractual agregada aceptada de la candidata B16. Sigue idéntico el conjunto de1507fuentes ejecutables; no se repite la carga18000/900s para redactar esta ficha. Falta separar escenarios y saber si el listado mantiene un coste SQL acotado en poblaciones pequeñas antes de elegir otro candidato.

Instrumento existente y sin editar: `tests/test_discovery_query_profile.py::test_discovery_full_visibility_query_growth[10]` y `[100]`. Dos casos explícitos, un worker, sin otras pruebas pytest. Su nombre histórico no fuerza fallback: se ejecuta el handler nativo vigente con `state_page` disponible, sin monkeypatch del producto. Cualquier caída a referencia es comportamiento actual, no un resultado descartable.

Datos: fixture directory/seed_demo y `scripts.synthetic_load_dataset.populate`;10 y100publicados, dos casos aislados. Fixtures sintéticos clonados, incluida fotografía compartida, sin calibración de duplicados ni100publicaciones moderadas individualmente. Preparación fuera del intervalo medido; ANALYZE de la carga según helper actual. No distribución nacional representativa, no promociones, no pagos reales. Se conservan migraciones y datos de la fixture existente.

Acción: una petición por caso, Django HTTP Client a `/es/`, anónima, listado inicial sin filtros. Concurrencia1. Wrapper SQL sólo cuenta tablas/cantidad y ejecuta la consulta original; no registra parámetros o valores. Mide walltime instrumentado del cliente, SQL total y conteos por tabla. Muestra de una petición por tamaño: no percentiles, calentamiento controlado, causalidad, TCP/Gunicorn,20RPS, worker/Beat real o SLA de producción. No se resta CPU por diferencia entre cronómetros.

## Oráculos y presupuestos anteriores al resultado

Gates funcionales existentes: HTTP200, población publicada exactamente10/100, página con min(población,24)elementos y Cache-Control no-store. Ambos casos deben ejecutarse, sin FAIL/ERROR/SKIP. No desactivar autoridad, validaciones o señales para acelerar.

Esta es la base diagnóstica: SQL/tiempo se observan, no tienen un límite numérico nuevo inventado. Un incremento constituye hipótesis para atribuir, no defecto N+1 probado por dos puntos. Antes de cualquier candidato se fijará el presupuesto de comparación sobre esa base y escenarios aplicables. El gate contractual p95<800ms/errores<1% conserva su protocolo original y no se aplica a estas dos muestras instrumentadas.111/338siguen como propuestas fuera de sus criterios expresamente adoptados.

Recursos: PostgreSQL17/Redis7.4 desechables propiedad del runner, localhost; el runner conserva --pull=never y no descarga imágenes durante la ejecución. aplicación en proceso local, un worker, sin cuotas comparables a la carga contractual8CPU/8GiB. No afirmar aislamiento o capacidad de host. Native librdb2.4.0 en `/tmp/web-modelos-librdb-v2.4.0`, compilado por el runner oficial y manifiesto preservado. Dependencias offline locked. Registrar imágenes, fuentes antes/después, manifiesto nativo, JUnit/journal, tiempos, recursos y limpieza.

Comando previsto, después de actualizar el grafo y congelar el corte:

```bash
.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --test tests/test_discovery_query_profile.py --workers 1 --timeout 900
```

El timeout900s limita cada paso del runner, no es SLA del producto ni ETA garantizada. Se prevé una prueba acotada, no una batería de horas. No hay objetivo de QA/paralelización. Si aparece una espera previsiblemente larga, aplicar persistencia/aviso/pausa/compactación/retorno del mismo goal conforme aAGENTS, sin repetir ni matar un caso sano por tardar más de lo esperado.

## Registro, conservación y siguientes lotes

La congelación después de la integración del grafo fijará SHA de producto/instrumentos y documentos, no sólo HEAD. No editar fuentes durante la prueba. run_local_ci notifica terminal tras limpieza; comprobar recibo. Conservar fallos, archivos y originales; un error de infraestructura/notificación no convierte el resultado enPASS. Auditar los dos nodeids/fases, propiedades, fuentes y ausencia de recursos al terminar, antes de interpretar medidas.

Después: prerregistrar segmentos ES/EN, filtros válidos/vacíos, paginación y promoción de S01 con datos/oráculos explícitos, y las fichas de los otros ocho grupos. Esta muestra no los sustituye ni justifica cerrar todo N01 o N04. La optimización se decide por coste y paridad, sin modificación obligatoria si no hay mejora respaldada.

## Preflight anterior a congelación

La imagen postgres:17-alpine no estaba disponible en este host; Redis7.4 sí. Se prepara la dependencia oficial PostgreSQL17 mediante docker pull antes de congelar y fuera del tiempo de medición, registrando digest eID en la congelación. Es preparación local de herramientas, sin contratación ni despliegue. No se cambia el objetivo PostgreSQL17. El resultado no afirma identidad de imagen con la batería anterior: la nueva referencia fijará el entorno real que también deberá usar cualquier candidato comparable.
