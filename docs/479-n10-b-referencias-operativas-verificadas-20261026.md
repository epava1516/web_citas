# N10B — referencias operativas actuales verificadas

Aceptación local de dos referencias seleccionadas, **sin cerrar N10**. Base `ae33175`; [prerregistro478](478-n10-b-prerregistro-referencias-operativas-20261026.md), instrumento tests/test_owned_operational_reference.py. N10A conserva [su corrección477](477-n10-a-groupadmin-autoridad-verificada-20261026.md). Continúan 9/13 bloques obligatorios aceptados, alpha/noindex.

Run `20261026-213503-04860762`: **2PASS, cero FAIL/ERROR/SKIP**, 47.589s de JUnit QA, 1792 huellas estables. El tiempo QA incluye preparación y oráculos, no es latencia de aplicación. Revisión propia del instrumento con django-expert, django-reviewer y code-security; Ruff y grafo focal antes de ejecutar. Imágenes cacheadas congeladas antes del lanzamiento y observadas en los contenedores del PID/start_ticks exactos del runner: coinciden. No se construyó una imagen ni se repitieron restauraciones o carga.

## Tabla de referencia anterior y actual

| Operación | Evidencia anterior | Referencia actual | Interpretación |
| --- | --- | --- | --- |
| Gunicorn spawn→cuatro workers ready | Testigo real de cuatro workers sin reloj spawn→ready; GC mide WSGI/Client | 1.690134s, una observación | Configuración raíz actual; incluye detección por sondeo de 50ms. No hay pareja temporal para atribuir mejora. |
| Health TCP local, primera petición | Sin pareja temporal comparable de este protocolo | 62.325ms | Petición después de los cuatro ready; PostgreSQL real, 200 y JSON exacto. |
| Health TCP local, cinco posteriores | Sin pareja temporal comparable | Mediana 3.164ms | Sin afinidad por worker, carga ni percentiles de cola. |
| operational_snapshot CLI en proceso, primera | Collector 0/10/100 con 18 muestras, sin equivalencia de dispatch/JSON | 129.319ms / 50SQL | Incluye dispatch de call_command, collector y serialización; no spawn de Python. |
| operational_snapshot CLI en proceso, cinco calientes | Sin pareja CLI comparable | Mediana 127.491ms / 50SQL cada una | Tablas de trabajo sin pendientes; no se extrapola a otros backlogs. |

No hay candidato de rendimiento, porcentaje causal ni nuevo umbral. El lote cierra huecos de medición identificados, no reduce el alcance de N10. Se conserva la referencia del collector y los cuatro perfiles reales de restauración con sus tiempos previos; su reutilización se concilia por fuente y escenario, no por el número de casos nuevos.

## Integridad y límites

Cada caso comparó los 173 modelos instalados, incluidas tablas intermedias, antes/después: ninguna fila cambiada. MEDIA_ROOT propio vacío permaneció sin cambios; esta vez no hay ocho archivos de prueba ni actores sintéticos, a diferencia del escenario Admin. No se infiere conservación de archivos poblados desde el conjunto vacío.

Gunicorn ejecutó cuatro workers reales, atendió seis peticiones health y terminó con master0 e hijos observados ausentes. El runner focused usa PostgreSQL17/Redis7.4 desechables y los recursos disponibles del host, sin cuotas nuevas. El proceso hijo usa el migrador de la base propia: este ensayo no acredita rol runtime de menor privilegio. La ruta health ejecuta SELECT1 según fuente; no se atribuye conteo SQL del proceso hijo desde el observador del padre.

Las seis salidas CLI fueron JSON de una línea, esquema1 y ámbito durable explícito. Se verificó contenido estable salvo sampled_at, publicación vacía, transacción restituida y 50 ejecuciones SQL observadas por llamada. No mide broker, worker vivo, inventario físico de objetos ni operación con proveedores.

Auditoría original: XML SHA-256 `4542b50bbd862e7719250610f106341512c6347c7a3d15b881dbeb5b716601e4`; fuentes congeladas comparadas contra las del runner y actuales, recursos y temporal propios ausentes, Telegram terminal PASS entregado. Los resultados de revisión y del grafo no se presentan como QA del producto.

Evidencia compacta: [archivo N10B](evidencias/n10-b-referencias-operativas-20261026.tar.gz), 13 miembros, 96149 bytes, SHA-256 `ad31ecad1791dca6d979896300779bb0de9bfefb6b4ef900adb933a44461f9ba`. Contiene instrumento/prerregistro, revisión, corte del grafo, congelación, XML original, propiedades auditadas, imágenes y resumen terminal/recibos; excluye logs y configuración secreta.

Siguiente: conciliar los 77 IDs de N10, en particular once runbooks, superficies Admin restantes y dos referencias del productor de rectificación, reutilizando sólo testigos de alcance vigente. Las 46 disposiciones de comandos conservan sus límites y modos no ejecutados. N11 y N15 siguen pendientes; N02 residual se mantiene diferido al final del desarrollo, N12–N14 condicionados.
