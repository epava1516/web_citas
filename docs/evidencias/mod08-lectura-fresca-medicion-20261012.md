# MOD-08 — medida final y aceptación provisional de tiempos, 2026-10-12

Código c92fe649a5a2c9e7365118f87fcaa710701857bb; [evidencia estructurada](mod08-lectura-fresca-medicion-20261012.json).
[Integración funcional previa](mod08-lectura-fresca-integrada-20261012.md): 184 codec/transport y25 LOGIN/PG/RustFS/Caddy PASS.

## Comparación limpia, segundos

Referencia388c991, measure125702-b2d8dd6f. Actual150109-89880182:
FAIL_DELIVERY_STAGE_LIMITS,1FAIL1989.924s,0errores/skips y seis límites excedidos.
No repetir la medida fallida. El resultado original queda inmutable: aceptación
provisional del usuario es una decisión posterior, no un PASS del instrumento.

| Etapa/caso | Anterior | Actual | Reducción observada | Objetivo original |
| --- | ---: | ---: | ---: | ---: |
| Cobertura A | 3.251440 | 3.285302 | -1.04% | 2 |
| JSON por paquete A | 6.486092 | 6.701149 | -3.32% | 5 |
| Binario por paquete A | 7.064550 | 6.820655 | 3.45% | 5 |
| Cobertura B | 3.275722 | 3.327704 | -1.59% | 2 |
| JSON por paquete B | 6.379550 | 6.716520 | -5.28% | 5 |
| Binario por paquete B | 7.070781 | 6.705964 | 5.16% | 5 |

Binario mejora3.45–5.16%; cobertura y JSON empeoran1.04–1.59% y3.32–5.28%.
Una ejecución por versión, sin reproducibilidad ni atribución causal exclusiva.
Las imágenes, dependencias congeladas y kernel son iguales al preflight actual;
los cambios de aplicación respecto a388 incluyen rotación ylectura final streaming.
No atribuir diferencias del portátil al código: alternaba cargador/perfil energético.

## Qué tiempo corresponde a una exportación

El p95 de descarga mide UN paquete de hasta8 MiB, POST303→GET200 y cuerpo completo,
no toda la copia ni toda la solicitud. La entrega contiene múltiples partes JSON
/binarias; se comprueban reconstrucción completa, datasets e imágenes dentro del
ensayo, pero no hay una métrica de una única descarga total de la copia.

| Fases automáticas observadas, una ejecución por caso | Antes A/B | Actual A/B |
| --- | ---: | ---: |
| Generación incluida cola | 41.314 /40.180s | 42.380 /42.973s |
| Preparación de respuesta | 20.160 /20.140s | 20.659 /20.651s |
| Acción de inspección final | 3.729 /3.544s | 3.701 /3.838s |
| Acción de aprobación final | 3.123 /3.014s | 3.489 /3.396s |
| Cierre | 19.608 /19.280s | 21.391 /21.431s |
| Suma aritmética de estas fases | 87.934 /86.157s | 91.620 /92.289s |

La suma no es duración end-to-end ni p95 total: excluye aprobación previa,
identidad, espera humana, barreras/otras operaciones y descargas. Revisiones
humanas del ensayo se ejercen por actores sintéticos mediante servicios reales;
no cronometra atención humana real. Generación y operaciones finales cumplen
sus objetivos propios120s/30s; sólo fallan los seis p95 listados.

1.500 revisiones/16MiB JSON/64MiB originales por caso y dos casos concurrentes es
una prueba extrema definida por Codex bajo delegación expresa; no previsión
comercial ni distribución medida de anunciantes. Una nueva Revision corresponde
a un nuevo borrador/versión; guardar campos en el mismo borrador, renovar y
las autosubidas no equivalen a crear otra versión. Un caso pequeño no se estima
linealmente desde este ensayo ni se afirma que tarde menos de un minuto.

## Decisión posterior del usuario

Usuario: «lo doy por aprobado provisional», con perfeccionamiento futuro y
continuación del resto del contrato. Confirmación posterior: «el estado actual
esta bien, es suficiente, pero marcarlo como mejorable no es malo».
Registrar rendimiento actual MOD08 SUFICIENTE PROVISIONAL /MEJORABLE NO BLOQUEANTE.
Alcance: escenario/versión/recursos medidos ydeuda de sus latencias. No promete
solicitud completa en7s o60s, no acepta global/N3 ni autoriza producción.
Los objetivos originales permanecen como referencia de mejora, sin falsear
FAIL histórico ni relajar integridad/autoridad/revocación/purga/recursos.

La regla RGPD12.3 regula la atención de solicitudes de derechos y su plazo
ordinario de un mes, con extensión motivada prevista; no impone estos SLO2s/5s.
[RGPD12.3](https://www.boe.es/buscar/doc.php?id=DOUE-L-2016-80807),
[AEPD](https://www.aepd.es/preguntas-frecuentes/1-tus-derechos/2-tus-derechos-de-proteccion-de-datos).
La rapidez de una descarga no acredita el cumplimiento del proceso completo.

## Entorno y cierre

Python3.12.15, PG17.11, Django5.2.17, dependencias/kernel native-sealed congelados.
8CPU/8GiB/storage≤20GiB/swap0; pico conservador propio medida4215144448bytes<6GiB,
sin OOM/swap. 384 navegaciones y20 descargas/tipo/caso; cuotas efectivas, tamaños,
concurrencia, cuerpos, procesos e integridad auditados independientemente.
Fuentes idénticas, archivo completo, sin perfiles/spans en measure.

Preflight145536-689259ce READY_NOT_CAPACITY/1PASS72.417s;
probe145837-4ab8d9f2 NATIVE_INSTRUMENT_PROBE_NOT_CAPACITY/1PASS42.189s.
Diagnose153711-7794fc07 se inició separado tras el FAIL yse interrumpió por la
nueva decisión del usuario: SIGINT sólo al pytest propio verificado por PID/ticks.
Original ERROR/1FAIL997.548s conservado, no PASS ni nueva aceptación de perfil.
Fuentes/archivo/retirada originales también auditados; cota2072338432bytes.

Todos los contenedores/red/volúmenes de los cuatro runners están ausentes. Se
retiró sólo la etiqueta temporal latest del ID propio verificado ecb4b179;
etiqueta nombrada84f1886-20261012/layers conservadas, sin prune ni servicios ajenos.

## Impacto en clientes y continuación

Estas latencias no son el tiempo de listado/búsqueda/ficha o publicación; esas
rutas no ejecutan este validador de exportación. Configuración común Dockerfile:
2workers sync yCompose compartido PG/app. Puede haber espera indirecta si todos
los workers se ocupan; no medida aquí ni porcentaje deabandono estimado.
[Gunicorn](https://docs.gunicorn.org/en/stable/design.html?highlight=workers).
La experiencia visual precisa medición de navegador distinta del p95HTTP:
[LCP](https://web.dev/articles/lcp). No reabrir por rutina la lectura ya aceptada.
Siguiente: consolidación técnica CR09 en versión común, N3 ypendientes reales,
seguida deCR10→GS01→BF/BB→C según el contrato. Proveedores/datos reales/publicación
continúan fuera deautorización.
