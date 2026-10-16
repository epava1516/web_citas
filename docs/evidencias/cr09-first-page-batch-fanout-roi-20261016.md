# CR09 — ROI WSGI con relaciones fuera de página (2026-10-16)

Run `artifacts/local-ci/20261016-085503-d020b682`, base `aecb0fc5d00f9ae94da287df195381d8fdc457d7`. Resultado funcional **1PASS**, 288lecturas medidas y108calentamientos; 10.000anuncios sintéticos. PostgreSQL propio real y límites anteriores conservados. Fuentes congeladas y limpieza verificadas independientemente. No nueva carga TCP/Gunicorn ni aceptación del p95.

Se fuerzan24pending válidos que ocupan la primera página en ambas rutas, más un limpio desplazado con128municipios legítimos. Los IDs de página se verifican antes del reloj. A/B son la misma implementación vigente; C es el prototipo de agrupación. Tres bloques ABC/BCA/CAB, seis calentamientos y16lecturas por brazo/ruta/bloque, GC normal y sin perfiladores. La instrumentación sólo cuenta SQL y comprueba PID de conexión. No hay writes/Beat/refresh real durante el reloj.

| Ruta | Media nativa A/A | Media agrupada | Reducción wall | Reducción CPU |
|---|---:|---:|---:|---:|
| /es/ | 381.583ms | 317.106ms | 16.90% | 15.76% |
| /en/?q=synthetic | 440.626ms | 381.522ms | 13.41% | 13.91% |

Ambas rutas cumplen los criterios prerregistrados: A/A discrepa<=10% en wall/CPU, ahorro medio wall>=10%, regresiónCPU<=5% y no-regresiónwall en al menos2/3bloques; en este run son3/3. Se reutilizó contexto132veces con48padres y sin fallback por selected ausente. SQL64→42 en ambos idiomas.

La sobrelectura comprobada antes sigue existiendo: este resultado demuestra que128municipios en un limpio desplazado no eliminan el ahorro en este fixture; no prueba todo fanout posible, cota de memoria ni distribución real de clientes. No se añade un límite arbitrario de relaciones ni se cambian guards/snapshot/recursos. Los porcentajes de este escenario no se comparan causalmente con el escenario dirty1: cambian los datos y el trabajo.

Decisión: conservar la variante como candidata, terminar el control dirigido del reloj de expiración e integrar con regresiones en suite normal. Después comprobar la versión común e imagen antes del corto limpio sin perfiladores. La adopción experimental no satisface CR09/N3 ni el contrato completo. Evidencia de muestras y planes: [JSON](cr09-first-page-batch-fanout-roi-20261016.json).
