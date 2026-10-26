# N09N — referencia local de objetos huérfanos verificada

Estado: referencia finita y decisión de conservar la aplicación aceptadas localmente para los escenarios observados. N09 sigue abierto con139IDs pendientes de disposición final y8/13bloques aceptados. Alpha/noindex. Base1562566 y [prerregistro456](456-n09-n-prerregistro-objetos-huerfanos-20261026.md).

Run: 20261026-164859-c0633e8d, 5 PASS sin FAIL/ERROR/SKIP, 124,060 s JUnit y1.783huellas estables. Runner focused serial, parser nativo, PostgreSQL17-alpine/Redis7.4-alpine propios y fixture RustFS real con imagen fijada. Auditoría independiente propia PASS:16fasesTask.run y113huérfanos físicamente retirados. Referencias/filas SQL, medios, cuerpos y metadata de objetos restantes preservados; readback autenticado de referencias vivas. Cinco buckets propios devuelven404tras limpieza y el contenedor exacto de RustFS queda ausente, al igual que recursos y temporal del runner. Telegram terminal y auditoría PASS con recibo sent. No quedan pruebas activas de este lote.

## Referencia temporal y antes/después

Los descriptores SQL se cargan en dos consultas por fase; hay N+2referencias vivas. Cada respuesta de listado tiene una página en esta población. Items cuenta objetos recibidos en la página, no candidatos visitados por el bucle. El retorno de la tarea cuenta bajas completadas sólo cuando termina normalmente.

| Huérfanos | Fase | Retorno | Tarea, ms | SQLexecute, ms | Descriptor, ms | Listado next, ms | Delete, ms | Bajas físicas | Después |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | fresh | 0 | 10.897 | 1.807 | 0.290 | 5.861 | 0.000 | 0 | Sin candidata |
| 0 | aged | 0 | 17.925 | 3.296 | 0.428 | 8.686 | 0.000 | 0 | Sin candidata |
| 0 | aged_replay | 0 | 21.448 | 4.090 | 0.715 | 10.204 | 0.000 | 0 | Sin candidata |
| 1 | fresh | 0 | 20.093 | 3.775 | 0.496 | 10.158 | 0.000 | 0 | Sin candidata |
| 1 | aged | 1 | 30.383 | 2.711 | 0.355 | 7.319 | 16.307 | 1 | Sin candidata |
| 1 | aged_replay | 0 | 10.893 | 1.675 | 0.427 | 5.732 | 0.000 | 0 | Sin candidata |
| 10 | fresh | 0 | 17.938 | 1.938 | 0.908 | 11.639 | 0.000 | 0 | Sin candidata |
| 10 | aged | 10 | 259.975 | 3.387 | 1.790 | 21.446 | 226.590 | 10 | Sin candidata |
| 10 | aged_replay | 0 | 15.546 | 2.011 | 0.871 | 8.136 | 0.000 | 0 | Sin candidata |
| 100 | fresh | 0 | 308.963 | 1.812 | 3.085 | 299.830 | 0.000 | 0 | Sin candidata |
| 100 | aged | 100 | 2461.307 | 2.614 | 4.569 | 93.546 | 2353.386 | 100 | Sin candidata |
| 100 | aged_replay | 0 | 74.191 | 2.078 | 7.582 | 59.500 | 0.000 | 0 | Sin candidata |
| 2 / fallo | fresh | 0 | 18.625 | 3.047 | 0.499 | 10.748 | 0.000 | 0 | Sin candidata |
| 2 / fallo | aged_interrupted | OSError | 38.316 | 5.896 | 0.430 | 8.913 | 18.349 | 1 | Sin candidata |
| 2 / fallo | aged_recovery | 1 | 32.066 | 2.804 | 0.397 | 8.107 | 16.601 | 1 | Sin candidata |
| 2 / fallo | aged_replay | 0 | 13.769 | 2.715 | 0.420 | 6.398 | 0.000 | 0 | Sin candidata |

Decisión: conservar la aplicación. El barrido de100huérfanos con102referencias vivas y202objetos encrypted/v1 recibidos tarda2461,307ms; delete_unreferenced reenviado ocupa2353,386ms dentro de ese tiempo. No se ha demostrado un defecto o incumplimiento que justifique una candidata marginal. El listado reciente de la misma población tarda308,963ms y el replay con102objetos,74,191ms: estados/cachés distintos yN1, no comparación de versiones o mejora. Sin después medido, ganancia causal no evaluable; no trasladar presupuestos HTTP a esta tarea de mantenimiento.

Medidas: wall sólo rodea Task.run. SQLexecute reenvía consultas reales sin texto/params y puede excluir fetch del iterator. Descriptor autentica referencias reales; next mide avance del paginador sin alterar argumentos o respuestas, no todo el consumidor. Delete incluye validación del bucket, baja y confirmación de ausencia. Son relojes parciales anidados/solapados, no sumables. Creación/validación, inventarios físicos completos, readbacks, hashes, asserts, teardown y QA quedan fuera. Los124,060sJUnit son QA. N1, instrumentación con coste no cuantificado, caché calentada y ejes de población acoplados; sin p95, carga limpia, SLA, histórico masivo o natural24h. Fixture observada:0.5CPU,512MiBmemoria/swap y128MiBtmpfs de datos; host Haswell/x86_64 con ocho CPU lógicas, sin carga o cuotas del host medidas por fase.

Objetos: paraN0/1/10/100yfalloN2 se usan Nhuérfanos y N+2referencias vivas Image/Part, con un tombstone creado por write/purge nativos y un objeto de otro prefijo como pines. Bucket propio por caso:2N+4objetos antes yN+4después. Seed por servicios nativos con objetos deshabilitados durante preparación, luego repositorio real y cuerpos sintéticos pequeños con contextos de propietario y readback autenticado. No nuevas autorizaciones HTTP, aprobaciones de imágenes o paquetes grandes. Todos los modelos instalados/through/auth/sesiones/auditorías/exportaciones/referencias y medios quedan byteexactos según sus oráculos; sólo cambian los objetos huérfanos permitidos. Los hashes de supervivientes y metadata coinciden con el inventario posterior, y cada baja se confirma con HEAD404.

Reloj: primera fase con reloj real retorna0y conserva los objetos recién escritos. La segunda avanza sólo el reloj de aplicación dos días y retira los no referenciados; después retorna0. LastModified proviene realmente de RustFS, sin falsificación. En la fase envejecida no se afirma tener un huérfano reciente; su protección se observa en la primera. No se esperaron24horas naturales ni se ejecutó Beat horario. El scan recorre todas las referencias y páginas; chunk_size100 no es un límite global. Una página en esta muestra no prueba costes de un bucket masivo.

Fallo: tras fase reciente0, OSError controlado antes del segundo delete deja el primer objeto realmente ausente y el segundo presente. Retorno ausente por excepción, dos intentos y una baja completa; SQL/medios/supervivientes intactos. Restituido el método real, recuperación1yreplay0. No se crea tombstone para el huérfano nunca publicado, y el tombstone independiente ya existente se conserva. Es interrupción controlada antes de una llamada, no caída abrupta, fallo externo real o rollback físico.

Intento:20261026-164021-e494a95f mantiene5FAIL/0ERROR/SKIPJUnit45,153s, runnerERROR,1.783fuentes estables, recursos/temporal retirados y TelegramERRORsent. Faltaba la imagen exacta en caché y el preflight rechazó antes de crear RustFS/buckets o ejecutar el consumidor; cero perfiles aceptados. Se preparó sólo la imagen pública de pruebas por digest1803faef57627e2d9c2e7d89d655d712ddded5389040054987163043fecb6a3c, con arquitectura amd64/linux y RepoDigest corroborados, sin arrancar servicios por el pull. Su recibo PASS acredita prerrequisito, no QA. Código de instrumento inalterado; nuevo delta semántico y congelación antes de repetir los cinco casos no aceptados. Ningún testigo válido se repitió ni se mezcló el primer tiempo con esta tabla.

Reutilización: seis originales PASS de20261024-094540-3a6ec8ac con19fuentes directas pertinentes idénticas: repositorio inmutable/contexto/rotación/tombstone/restauración, corrupción sin salida, protección por versionado, limpieza de huérfanos con RustFS/reloj sintético/hooks eager y dos tramos de purga de exportación/vencimiento/skip. Conservar sólo sus alcances de consumidor/repositorio; no admisión, generación, descarga HTTP o monitorización actuales, cierre transitivo global, worker, Beat o proveedor. El run antiguo completo conserva ERROR. No se repiten grandes paquetes ni controles válidos de restauración por esta medición.

Revisión: propia Django/Celery/seguridad sobre377líneas propuestas y sus dependencias pertinentes. Root reforzó asserts privados, allowlist exacta de metadata Docker sin Env/HealthLog, hashes reales de SQL/medios/supervivientes y cierre del iterador. Instrumento final SHA2b2454720942fa5ad3577bfc0f13ffe69c2118100738b6ec6a57b51149d4200f/RuffPASS. Reporte inicial con STATUS mayúsculo rechazado y corregido sólo en el campo; diez campos canónicos validados, sin aceptación runtime por complete. Sin cambios de aplicación, esquema, configuración de producto, CI o servicios normales.15archivos laterales preservados fuera de la entrega propia.

Grafo: corte455 de2097fuentes, SHA3e891861c1910cdbc1785a3e88367d6852945f70a9bdee4ad1d5b5b36e86f071. Primer prerregistro AST+sem456/17:2099fuentes/20537nodos/85245relaciones/999comunidades, SHAaef81a63488770ab53faf6a0933d269a2b300ad7baf93b845c7583fc7801a882. Antes de la ejecución aceptada, AST retenido y sólo sem456/17 por imagen preparada:2099fuentes/20538nodos/85247relaciones/1000comunidades, SHA70df23d4e28e85007ba25077ef90a0b266322b56c0e6ba29fc2346e6dd99fedd. Cierre selectivo457/17 sin AST/runtime extra; no reconstrucciónN15 ni semántica exhaustiva. Inventario111 preservado.

Límites: RustFS local no es proveedor productivo, Task.run no es worker/Beat y reloj sintético no es retención natural. La prueba no acredita capacidades de carga, recuperación general o autorización de entrega. N09 mantiene purga de exportaciones, puentes de productores y139disposiciones finales; N10/N11/N15 pendientes, N02restante al final yN12–N14condicionados. No cerrar N09 por sumar objetos o perfiles.
