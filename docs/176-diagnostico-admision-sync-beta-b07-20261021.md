# B07 — Diagnóstico de admisión y manejo sync

Estado: terminal auditado PASS numérico instrumentado; no aceptación de capacidad ni permiso900s. Ocho de18cerrados.

173acota espera después del envío y antes de línea de estado;175calibra61unionescliente/servidor con4workers. Falta saber si el tiempo se concentra antes del handler, durante lectura/parseo o dentro de manejo/limpieza. Se lanza por esta medición ausente, sin candidato de producto nuevo ni búsqueda de unPASS.

Mismo short173:10000perfiles/2000derechos/20RPS60s/1200dinámicasESENpor tercios/1subida,4Gunicornsync1hilo, PostgreSQL17/Redis y worker/Beat propios. Añadir sólo --benchmark-server-boundaries al comando173 con --benchmark-client-phases --benchmark-normal-refresh --benchmark-beta-promotions --workers1 --fixture-snapshots --isolate-test-broker --timeout2400. Misma finalización8ANALYZE y primeraslecturas frías. No otrosprofiler/builds/tests/refrescos de grafo simultáneos; no nuevos recursos niSQLwrappers.

Mismos criterios: p95observable<800ms/errores<1%,generador10/25/100ms,ceroomitidas/finalespendientes,ventana≤20,timeout65/drain70. El veredicto numérico se conserva, sin utilizar servicio o etapas como sustituto de latencia cliente. Captura instrumental impide continuar900s independientemente del veredicto; no aceptaB07.

Unir1200IDs dinámicas y1subida por identidad sintética exacta. Verificar timestamps finitos/monótonos,PIDpropios, cuatroworkers efectivamente observados o declarar la limitación, devolución nativa e intervalos sin solapamiento porPID. Conservar errores, muestras parciales o ausentes; no inventar fases ni relanzar por falta de datos. Revisar fuente de reloj cliente/servidor en el mismo host.

Medidas descriptivas por ruta/ventana y globales:

- handler_entered−(origin_cliente+request_drained): intervalo firmado previo al handler, con negativos preservados; incluye fronteras distintas de envío/admisión/bookkeeping, no cola exclusiva.
- pre_request_entered−handler_entered: espera y parseo dentro del handle.
- handler_exited−pre_request_entered: aplicación/respuesta/limpieza nativa, noCPU.
- Intersección de los intervalos handler_entered→handler_exited con la ventana real de60s: ocupación observada porworker, excluye append del observador y bookkeeping exterior; no CPU ni todo trabajo del proceso. No sumar intervalos solapados o extrapolar desde servicio/60.

Conciliar con servicioGunicorn y etapascliente, sin sumar percentiles. Declarar overhead causal del instrumento no medido; no atribuir diferencias contra173a una optimización. Si hay ocupación alta y espera prehandler, evaluar eliminar trabajo medido antes de tocar concurrencia. Si no, conservar el resultado y localizar el límite observado.

Congelar fuentes/docs/.ai/grafo desde lanzamiento hasta terminal, limpieza, reciboTelegram y auditoría fresca.628fuentes aplicación iguales; dos herramientas modificadas del mapa726más un módulo diagnóstico nuevo. Preparación esperada en minutos/decenasdeminutos, no horas: goal activo. Sin proveedores, publicación, personas reales o ventas. Los negativos previos permanecen intactos.

## Resultado terminal auditado

164127-a74b1fc0:1PASS/0FAIL/0SKIP,958,597sJUnit. [Auditoría](evidencias/b07-sync-boundaries-short-tcp-20261021-164127-a74b1fc0-audit.json):1200dinámicas200,0errores/noemitidas/pendientesfinales,1subida302persistida; p95observable548,230ms y10pendientesventana, todos los criterios numéricos cumplidos. Las1201capturascliente/servidor están completas y unidas; cuatroPIDpropios, retornos nativos e intervalos porworker sin solapamiento verificados.

La rama de protección queda ejercida también con todos los criterios enverde: verdictPASS pero diagnostic_continue_contractFalse por captura opcional. Este resultado no permite900s ni aceptaB07. Los FAIL112359/152807/160253 siguen vigentes.

Sobre1201handles, incluyendo la subida: intervalo firmado envío→handler mediana143,952ms/p95330,805ms,55negativos conservados/mínimo−2,320ms; handler→pre_request mediana0,111ms/p950,239ms/máximo2,225ms; pre_request→salidahandler mediana243,177ms/p95347,996ms. Son poblaciones y etapas distintas, no sumar percentiles ni llamarCPU o colaTCPexacta a sus valores.

La ventana observada dura60,001653s. Ocupación sintética medida porPID:99,40%,99,31%,99,13%y99,09%; suma de intervalos intersectados equivale a3,969workers ocupados, noCPU. Excluye append del observador, bookkeeping exterior y conexiones sinID. La espera principal observada en esta corrida está antes de entrar al handler; el parseo es corto. No atribuir la diferencia frente173al instrumento, host o cachés sin contraste: no hay cambio de aplicación y overhead causal no medido.

Fuentes/628appiguales/dos tools modificadas más1módulodiagnóstico/limpieza/temporales/PIDs/Telegram confirmados. Siguiente177: control limpio sin ambas capturas y sin código nuevo, motivado porPASSinstrumental frente aFAILprevios. No adoptar una configuración ni declarar mejora causal por este resultado.
