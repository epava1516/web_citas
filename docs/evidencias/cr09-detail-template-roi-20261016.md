# ROI de plantilla de consulta de detalle

Ejecución `20261016-125113-ab047032`: 1 PASS en 193,90s, 1296 lecturas/72 conexiones propias/10k sintéticos. Cumple los criterios prerregistrados en ambas rutas; controles estables, CPU backend precisa. No es p95 HTTP.

| Ruta | A/B medio ms | C medio ms | Ahorro tiempo | Ahorro CPU app | Cambio CPU PG |
|---|---:|---:|---:|---:|---:|
| ES | 70.814 | 66.826 | 5.63% | 10.62% | +3.45% |
| EN | 73.616 | 66.122 | 10.18% | 15.56% | -1.75% |

27 consultas en todos los brazos. Primeras seis lecturas: ahorro2,61% ES/11,81% EN; en caliente7,94%/8,86%. Bloques sin regresión8/12 y10/12. Una creación de plantilla y431aciertos, sin resultados retenidos. CPU PG caliente ES+6,37%; el criterio previo era CPU PG total≤5% (ES+3,45%), no aceptación de todo escenario. Sin cambio de política del planificador.

Dispatcher común, GC normal, preparación de conexión fuera del reloj, primer uso C incluido. Python/buffers PG ya usados; dos anuncios de agencia/clon, sin TCP/Gunicorn/Beat/subida. Fuentes y limpieza verificadas independientemente. [Recibo](cr09-detail-template-roi-20261016.json). Siguiente ampliar controles de anunciante individual y guardas antes de integrar. No nuevo p95, CR09/N3 abiertos.
