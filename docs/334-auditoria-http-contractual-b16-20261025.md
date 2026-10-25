# B16-371/372 — Auditoría del HTTP contractual vigente

La ejecución `20261024-235904-c98b179b`, candidata `8f68fc8`, terminó con `BETA_HTTP_CONTRACTUAL_PASS_NOT_GLOBAL`: un caso aprobado, cero fallos, errores u omisiones; 6582,289 segundos JUnit (1 h 49 min 42 s). Véanse el [protocolo congelado](333-prerregistro-http-contractual-b16-20261025.md) y la [evidencia auditada](evidencias/b16-contractual-http-audit-20261025.json). B16 sigue abierto para conciliación de requisitos y versión; este informe no es su acta.

## Contabilidad y tiempos

Se recorrieron las 18000 muestras, identificadores únicos y ciclo exacto de 96 slots: 6000 listados, 6000 búsquedas y 6000 fichas; 9000 ES y 9000 EN. Todas terminaron con HTTP 200, cuerpo no vacío, sin error inesperado ni timeout. Quince subidas a borradores distintos fueron programadas cada 60 segundos entre 0 y 840 y respondieron 302. El caso comprueba una Photo y un UploadAttempt accepted/duplicate por borrador.

Los percentiles se recalcularon independientemente con la convención congelada de rango superior ceil(n*p/100), sobre las 18000 muestras completas: p95 observable 410,559 ms; máximo 702,782 ms. Generador p95 2,864 ms, p99 5,935 ms y máximo 31,154 ms. Coinciden exactamente las tres distribuciones archivadas: observable, generador y retraso total. Todas las comprobaciones contractuales del instrumento son verdaderas.

## Contenido y autoridad: alcance exacto

El helper tests/capacity_combined_filters.py reconstruye el censo y orden desde autoridad nativa, exige publicación vigente sin marcas pendientes y verifica 68 filas HTTP antes y después. Comprueba IDs ordenados sin duplicados, total nativo, etiquetas premium/top y Cache-Control no-store; ambos conjuntos archivados son iguales. Las 96 sondas frías responden 200. El recorrido temporal registra estado y tamaño, no conserva ni compara el cuerpo completo de cada una de sus 18000 respuestas. No se atribuye esa cobertura adicional. El ranking de referencia comparte primitivas PostgreSQL y su alcance se conserva.

## Congelación, recursos y conservación

Antes de editar documentación se comprobó igualdad de las 1723 fuentes actuales, prerregistradas y originales; también SHA de grafo, protocolo, especificación y ocho helpers. Las cuotas kernel suman 8 CPU y 8 GiB con swap cero. No hubo OOM ni swap observado; la suma conservadora de picos y reserva del controlador es 2229338112 bytes, no un pico concurrente. El techo configurado de almacenamiento propio es 4865392640 bytes, no una medición de almacenamiento productivo.

El controlador archivado terminó exited/0, running=false, oom_killed=false. Se leyeron íntegramente los 74 miembros de archivo y se registró su SHA. Una consulta Docker independiente confirmó ausencia de contenedores, redes y volúmenes con la etiqueta exacta de ejecución. Las identidades PID/start_ticks de supervisor, watcher, resumer y compactor ya no están ejecutándose. Los wrappers del controlador y las rutas temporales de servicios eran tmpfs de los contenedores retirados; se conserva intencionalmente el archivo de evidencias del host. No se acredita un censo global de /tmp. Telegram terminal y reactivación del mismo objetivo constan como enviados, sin nuevo objetivo.

## Disposición

PASS contractual acotado de la candidata vigente, con población sintética y medios compartidos de fixture, proveedores locales y pagos sintéticos. No acredita producción, navegación real de toda la aplicación, contratación ni apertura. No se repite carga. Restan la conciliación B16 requisito→cambio→prueba→evidencia→límite, sus puentes de versiones y el cierre documental del contrato, incluido grafo completo e inventario diferencial. El proyecto permanece en alfa; balance sin cambiar: 14/18.
