# Acta10 — Entrega técnica local: Alpha consolidado, 2026-10-20

**Se acepta C01–07 y se consolida el Alpha técnico local del MVP**, conforme a contrato16 §8/11 y MOD09. Revisor: Codex principal. Versión integrada probada: `3887db16f4ba0a4a06e79f3c23990543aaf8f59d`, rama local `codex/mod08-vps-server-20261012`. La documentación de cierre se añade después sin cambiar producto, pruebas, dependencias o contratos. La aceptación incluye los límites y omisiones aquí descritos; no equivale a ausencia de defectos ni a todas las circunstancias imaginables.

[Matriz literal de siete criterios](../evidencias/c-local-acceptance-matrix-20261020.json), [auditoría común terminal](../evidencias/c-final-common-terminal-audit-20261020.json), [entorno/versiones](../evidencias/c-final-environment-20261020.json). Las actas CR09/CR10/GS01/BF/BB anteriores siguen conservadas; ahora la N3 ordinaria ampliada y las comprobaciones de entrega corresponden al corte integrado indicado, con reutilización histórica por alcance expresamente justificada.

## Batería común y comparación

| Fase | Seleccionados únicos | Aprobados | Omitidos | Fallos | Duración pytest |
| --- | ---: | ---: | ---: | ---: | ---: |
| Funcional, dos workers | 3358 | 3236 + 4 subpruebas | 122 | 0 | 2 h 25 min 46 s |
| Capacidad, después en serie | 298 | 290 | 8 | 0 | 51 min 42 s |
| Total, conjuntos disjuntos | **3656** | **3526 + 4 subpruebas** | **130** | **0** | **3 h 17 min 28 s** |

Runs funcional `20261019-204004-686b929a` y capacidad `20261019-230638-fca1e724`: mismo HEAD,1580fuentes técnicas iguales entre lanes y4311entradas de congelación de fuentes/instrumentos/documentos comprobadas antes de editar el cierre. JUnit cuenta cuatro subpruebas más que el inventario de nodeids, no cuatro casos nuevos. Se verificaron journals, setup/teardown, restricciones PostgreSQL, navegador real, informes de ordenación de ambos workers, resultados terminales y recibos de Telegram de cada lane y del conjunto.

| Comparación observada | GS01 anterior,3637casos | C final,3656casos | Diferencia |
| --- | ---: | ---: | ---: |
| Funcional | 2 h 46 min 59 s | 2 h 25 min 46 s | −12,7 % |
| Capacidad | 51 min 46 s | 51 min 42 s | Sin cambio material |
| Suma pytest | 3 h 38 min 45 s | 3 h 17 min 28 s | **−21 min 17 s / −9,7 %** |

La suma compara las etapas pytest; no incluye preparación, compilación ni tiempo de envío/limpieza. Es una diferencia observada con selección ampliada e historia/carga del host distintas, no una estimación causal aislada de cada cambio ni latencia de request. El flujo1500 conserva todas sus inspecciones/aprobación/cierre/JSON/WebP/ZIP; su call actual780,297s y copia1280actual3,838s están en el JUnit. El helper conserva la vía individual por defecto; no generalizar lotes pequeños que no mostraron beneficio. La ordenación por duración cambia archivos completos, conserva casos y orden interno y no añade workers. Capacidad conserva ejecución serial.

Las130omisiones coinciden exactamente con GS01: diagnósticos/perfiles de recursos propios y seis escenarios de revisión de contenido con evidencia separada; no se cuentan como aprobados. Las cuatro exclusiones ordinarias del runner —dos cargas HTTP contractuales, fichero TCP y fichero JSON histórico grande— se concilian con sus testigos específicos de producto idéntico. [Vinculación de testigos reutilizados](../evidencias/c-final-reused-witnesses-binding-20261020.json). No declarar cero omisiones ni reunir runs distintos como si fueran el mismo commit.

## Decisión de los siete criterios

| Criterio | Evidencia examinada y decisión local |
| --- | --- |
| C01 conjunto común | Ambas lanes terminales PASS, mismo3887db1,3656nodeids disjuntos,130omisiones históricas conciliadas, sin fallos. Se acepta el alcance ordinario N3 más los testigos requeridos separados y justificados. |
| C02 recorridos/roles/idiomas | [19familias](../evidencias/c-final-current-states-binding-20261020.json) vinculadas a callPASS actual y huellas actuales. Particular/agencia con dos personas/MFA, borradores/fotos/envío, moderación/publicación, búsqueda/filtros, denuncia/urgencia y retirada; cuenta y recorridos ESEN,390/1280px en navegador. Autoridad por objeto, revocación y errores probados; no producto cartesiano exhaustivo de pantallas/roles/anchos. |
| C03 carga/recursos/activos | Dos cargas limpias de18000requests y15subidas,0errores, p95 .334852340/.332467304s, reutilizadas por621fuentes producto/lock iguales; testigos de rutas/TCP/JSON/Beat conciliados. BF05 Docker/Caddy mide5activos,16vistas,24imágenes por separado. No nueva medida de request, CDN real o Core Web Vitals de campo. MOD09 provisional conservado. |
| C04 despliegue/recuperación/OP | Imagenv11 inmutable,623fuentes iguales, UID10001, native-sealed, PG real/migraciones/runtime y ocho rutas; restauraciones completas dump+medios plain/encrypted y comercial actualmente PASS. Negativos de clave/manipulación y reconciliación antes de exposición verificados. TLS/PROXY local y rollback estáticos reales, OP001–009 por alcance de auditoría100. Perfil Compose es ejemplo/configuración, no despliegue completo ni público. |
| C05 seguridad/privacidad | [11grupos IMP](../evidencias/c-final-security-current-binding-20261020.json) con callPASS actual;27fuentes revisadas y15de revisión anterior conservadas por huella; mapa de autoridad/finalidad/retención y OP.44dependencias Python runtime sin avisos conocidos en el corte auditado. No nuevo defecto bloqueante identificado en el alcance revisado. Revisión independiente externa queda pendiente. |
| C06 textos/aceptación ESEN | LegalDocument/LegalAcceptance versionados y traducciones sintéticas examinadas; signup rechaza versión antigua/falta aceptación; formulario abierto dev-2→dev-3 rechaza400 y no registra aceptación; conserva aceptación anterior. Navegador ESEN y bootstrap sólo desarrollo. Operador/textos/políticas reales y revisión jurídica no se aceptan por esta prueba. |
| C07 entrega y separación | Esta acta y matriz registran requisitos→implementación→versión→prueba→evidencia→límite. [Acta11productiva](11-preparacion-produccion-pendiente-20261019.md) separada: G01–08 pendientes. |

## Fuentes, entorno, fallos y limpieza

Python3.12.15, Django5.2.17, pytest9.1.1, xdist3.8.0, Playwright1.63.0, psycopg3.3.6, Gunicorn23.0.0, Celery5.6.3; lock congelado. Imagen PostgreSQL17.11 identificada por digest. Kernel native-sealed con huella propia; Cython3.0.12 corresponde al constructor sellado, no a un paquete instalado en el venv de aplicación. [Entorno completo](../evidencias/c-final-environment-20261020.json).

Controlador4CPU0–3/3584MiB/swap0/pids512, PG1CPU4/1536MiB/swap0/pids128/WAL256–80, Redis0,2CPU5/128MiB/swap0/pids64; native runtime real. Se mantuvieron límites y ausencia de perfiladores en las cargas limpias reutilizadas. La instrumentación funcional de etapas no se presenta como medida limpia de request. Ambas lanes sin OOM; contenedores exactos por label, temporales y PIDs/start-ticks ausentes tras terminar. Avisos terminales y pausas por Telegram confirmados. Ningún servicio normal, proveedor o producción intervenidos.

Se conservan: [primer C con fallo de argumento entre tests](../evidencias/c-final-shared-restore-failure-20261019.json), [correctiva3PASS](../evidencias/c-restore-corrective-terminal-20261019.json), [segundo C interrumpido deliberadamente](../evidencias/c-final-interrupted-by-priority-20261019.json), error de lanzamiento previo a tests y hallazgo PYTEST_ADDOPTS filtrado. El ensayo final usa argv explícito y recibos de ambos workers; no se atribuye ordenación al ensayo anterior. Los fallos antiguos de rendimiento/instrumentos permanecen negativos, sin convertirlos retroactivamente en PASS.

## Límites y siguiente revisión

**Alpha técnico local consolidado; producción no autorizada ni preparada.** No publicación/push/proveedores/pagos reales, datos de sujetos ni operador real. Integraciones externas de verificación/correo/pagos continúan simuladas e identificadas; recursos locales PostgreSQL/Redis/RustFS/Docker/Caddy/worker se ensayaron realmente en sus alcances. G01–08 mantienen identidad/política/textos, geografía nacional verificada, responsables/guardia, secretos/DNS/backup/offsite/custodia, revisión jurídica e independiente y autorización de despliegue pendientes.

MOD09 conserva deuda de rendimiento extremo y objetivos originales2s/5s para mejora futura; no reabrir como bloqueo por este cierre. FAISS/índice por Hamming para CC05 está [propuesto en97](../97-propuesta-indice-similitud-fotos-cc05.md), sin implementación ni métrica. No atribuir diferencias del portátil al código: cambiaba su perfil energético al alternar cargador.

Siguiente tarea acordada: consultar todas las fuentes del proyecto en Open Notebook como un solo corpus, preservando sus referencias, para encontrar omisiones/contradicciones/correcciones. Esta auditoría documental posterior **no se declara realizada** por consolidar el Alpha; cualquier hallazgo se evaluará y verificará antes de corregir. Mantener intactos los libros IRIS en el servicio anterior NotebookLM. Las ocho invocaciones Claude V1 y su consumo previo se conservan; este cierre no añadió invocaciones.
