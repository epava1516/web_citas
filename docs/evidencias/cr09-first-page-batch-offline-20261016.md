# CR09 — diagnóstico separado sobre las muestras del corto fallido

Se cruzaron los1200IDs únicos de cliente y servicio de `091632-958b115a`, sin errores de parseo ni ausencias. No se ejecutó carga ni cambió producto. [Recibo reproducible y hashes de entradas](cr09-first-page-batch-offline-20261016.json); script `artifacts/cr09-batch-offline-20261016/analyze.py`.

| Llegadas | Solicitudes | HTTP medio | Servicio medio | Diferencia media por ID |
|---|---:|---:|---:|---:|
| 0–1s | 20 | 832,033ms | 348,350ms | 483,683ms |
| 1–2s | 20 | 1155,850ms | 227,516ms | 928,334ms |
| 2–5s | 60 | 1116,527ms | 184,136ms | 932,391ms |
| 5–10s | 100 | 766,442ms | 182,311ms | 584,132ms |
| 10–15s | 100 | 301,966ms | 173,946ms | 128,020ms |
| 15–60s | 900 | 206,989ms | 179,131ms | 27,858ms |

La diferencia se calcula para la misma petición; no se restan percentiles. En Gunicorn23 instalado, `workers/sync.py:166–187` empieza el reloj después de parsear la petición, incluye crear WSGI/ejecutar respuesta/escribir cuerpo y termina antes del accesslog y del cierre posterior. Por tanto, el residuo incluye admisión/parsing/transporte y trabajo del cliente. No se denomina cola de socket exacta ni tiempo preWSGI exclusivo.

Las peticiones llegadas en el primer segundo requieren6,967worker-segundos de servicio medido, frente a4worker-segundos de capacidad temporal de cuatro workers durante ese segundo. Es demanda de servicio de esa cohorte, no CPU medida ni ocupación efectivamente integrada en esa ventana. El siguiente segundo requiere4,550worker-segundos; de2–5s baja a11,048 en tres segundos. El patrón es compatible con acumulación inicial y vaciado progresivo, no demuestra qué hizo más caro ese servicio inicial.

Las muestras de estado1Hz alrededor de0,311/1,311/2,311/3,311/4,311/5,311s registran Dirty0. Los logs muestran refrescos con resultados1 y2 cerca del comienzo: el muestreo no puede excluir intervalos Dirty entre observaciones. No se afirma que la agrupación nunca se ejerciera ni que Dirty persistiese diez segundos. Faltan marcas dentro del worker para atribuir SQL/CPU/GC, arranque de conexión/planes y la intervención exacta del refresco. No se elige hardware, legalidad o sobreingeniería como causa exclusiva.

## Siguiente diagnóstico prerregistrado

Una ejecución aislada del mismo escenario corto, **instrumentada y no apta para aceptación**, usando observador existente de entrada WSGI/SQL/GC y preparación estática productiva. Mantener cuatro workers, presupuestos, subida, GC normal de workers, Beat y generador anteriores; sin otros perfiladores, sin cambios de producto y sin carga concurrente propia adicional. Registrar también preámbulo anterior a las llegadas, PID y SQL por huella sin texto/valores.

Hipótesis: distinguir si el exceso de servicio de las primeras peticiones proviene principalmente de ejecución SQL, CPU Python/GC o espera, y contrastarlo con sus solicitudes posteriores por worker/ruta. Validar emparejamiento deIDs/reloj, arranque preparado y finalización; comparar intervalos de la misma ejecución. SQL/GC se solapan con WSGI y no se suman como fases independientes. El coste del observador no está cuantificado; su p95 no sustituye al corto limpio ni demuestra mejora/empeoramiento del producto. Conservar cualquier fallo y diagnosticar antes de proponer otra optimización. CR09/N3 siguen pendientes.
