# B07 — Límites mínimos del worker sync

Estado: diez casos y calibración TCP pequeña auditados; no capacidad ni ahorro causal. Ocho de18cerrados.

173sitúa la espera entre envío local y línea de estado, sin separar admisión y parseo. scripts/benchmark_sync_boundaries.py añade sólo al diagnóstico dos wrappers: handle nativo y pre_request nativo. Registra entrada del handler después de accept/setblocking/cloexec, entrada de pre_request tras el parser y salida de handle después de limpieza nativa. No cambia worker_class, nºprocesos, respuestas, WSGI, SQL, render, autorización o calentamiento de rutas.

Un appendJSON por petición identificada se hace después del reloj de salida; sólo conservaID sintético d/u,PID,tresmarcasmonotónicas y retorno nativo. No rutas,SQL,cuerpos o cabeceras. El append y los wrappers tienen coste causal no medido y pueden influir en la admisión siguiente; no descontarlo ni declarar equivalencia de rendimiento. No es instrumentación de producción.

El cliente añade origin_monotonic_seconds a su captura opcional para unir los relojes del mismo host. No modifica el emisor ni la política. El servidor no registra el instante exacto de accept; su primer límite excluye bookkeeping anterior. Diferencia entre drain y handler es intervalo firmado entre límites, no cola socket exclusiva. Handler→pre_request incluye espera/lectura del parser; pre_request→salida incluye aplicación, respuesta y limpieza. Ningún tramo equivale aCPU.

## Verificación y límites

162827-318317d5:10PASS/10,740sJUnit con doble simple de configuración. Lectura posterior del código instalado detecta que Config no admite asignar directamente pre_request: debe usarse cfg.set. No hubo integración real de ese primer instrumento y no se acredita como tal; archivos iniciales preservados.

Corregido instrumento y sustituidos dobles por gunicorn.config.Config real:162928-c1053578,10PASS/0omisiones/10,748sJUnit. Seis casos cliente y cuatro de límites: delegación/resultados/restauración, excepción sin estado pegado, privacidad de identidad y rechazo de duplicados/no finitos/orden inválido/datos extra. No se modifican servicios de aplicación.

163052-0b9d67b5:1PASS/0omisiones/88,76spytest,10perfiles/2derechos,60dinámicas200 y1subida302persistida con worker/Beat/PostgreSQL/Redis reales. [Auditoría](evidencias/b07-sync-boundaries-calibration-20261021-163052-0b9d67b5-audit.json):61capturascliente/61servidor, cuatroPIDworkerpropios, marcas entre inicio cliente y línea de estado, retorno nativo de61handles e intervalos no solapados dentro de cada worker. p95cliente214,929ms no es capacidad10000ni una mejora frente a otra calibración.

48de61intervalos drain→handler son negativos, mínimo−0,477ms: conexión aceptada antes de terminar el envío local. No se descartan ni se truncan a cero. El mayor handler→pre_request de esta pequeña muestra es3,609ms; no extrapolar al diagnóstico grande.

Las628fuentes apps/config/templates permanecen iguales. Del mapaimagen726,724iguales y dos herramientas modificadas (cliente/runner); además se añade un módulo diagnóstico nuevo. No afirmar que todo runtime actual coincide con la imagen previa. Fuentes del gate, limpieza de servicios/temporales/PIDs y Telegram auditados. La unidad y TCP conservan fuente del instrumento idéntica; runner y testHTTP son los cambios de cableado entre ambos.

[GuardasCLI](evidencias/b07-sync-boundaries-cli-guards-20261021.json): seis rechazos antes de crear runs. --benchmark-server-boundaries requiere cliente, refresco normal, promociones sintéticas y ningún profiler previo; hereda focused/1worker/selector funcional o corto. measured está excluido. El prerrequisito beta se explicitó después de la calibración, que ya llevaba todas las banderas exigidas.

No se habilita900s ni se aceptaB07. Siguiente176: mismas condiciones de173más límites de servidor, para distinguir espera anterior al handler, parser y manejo nativo; nunca atribuir una resta a cola exacta o a CPU.
