# B10-362 — Prerregistro de medición actual MOD-09

Se prepara una medición actual del circuito completo de derechos tras el [contraste323](323-contraste-fuentes-mod09-b10-20261024.md) y el [preflight324](324-preflight-actual-mod09-b10-20261024.md). No repetir el corte histórico para cambiar su FAIL: se ejecutará el instrumento sobre fuentes actuales y se conservará cualquier fallo nuevo. No se cambia aplicación, fixture, umbral ni criterio temporal.

Selección: test_owned_complete_target_delivery; dos casos independientes concurrentes con1500revisiones/16MiBJSON/64MiB originales por caso. Comando oficial run_capacity_environment: --selection-tcp --selection-concurrent --selection-gunicorn --database-heavy --object-delivery --cpu-budget 8 --delivery-complete; imagen soporte inmutable sha256:f50e2f01874ebbd1147261160c6058c64bf2e8d26d50b2446c7549d2692b947b validada en preflight. Fuentes e intérprete actuales montados de sólo lectura, sin cambiar imagen latest.

Conservar los objetivos de cobertura p95≤2s y entrega JSON/binaria por paquete p95≤5s, además de los límites propios de generación/acciones, integridad de cuerpos, autoridad fresca, revocación, cuotas y limpieza. No cronometra revisión humana ni convierte la suma de fases en latencia total. Una imagen/entorno diferentes de la referencia histórica impiden atribuir causalidad exclusiva al código; la medida actual sí permite conocer el estado vigente.

Referencia de planificación: el caso histórico completo tardó1989,924s deJUnit, aproximadamente33minutos, además de preparación. No es plazo garantizado: el instrumento admite un tiempo máximo de11500s y un fallo de recursos invalida la ejecución. No interferir en servicios ajenos ni usar datos reales/proveedores.

Antes del lanzamiento: guardar manifiesto completo de fuentes, hashes de protocolo/grafo/controladores y relevo; comprobar helpers estáticamente y sus avisos. Ejecutar persistentemente con stdin cerrado y logs en artifacts, aviso terminal Telegram tras limpieza y supervisor separado. Durante la espera, pausar el mismo objetivo con aviso previo confirmado; compactar al alcanzar estado idle y reactivar el mismo objetivo sólo al terminal por el mecanismo ya autorizado, conservando creación y consumo. Una petición de compactación no acredita su finalización.

Al regresar: auditar resultado original, JUnit y errores/omisiones, ambas identidades/cuerpos/concurrencia, huellas, límites reales, retirada independiente y Telegram. No lanzar otra carga automáticamente. Conciliar B10 y las exclusiones pertinentes de B16 antes de cualquier acta. La aceptación provisional MOD-09 permanece; seguimos en alfa.

Estado de este documento: preparación, sin resultado de la medida. Los identificadores y recibos de lanzamiento se conservarán separadamente para mantener el protocolo congelado.
