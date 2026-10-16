# CR09 — preparación por proceso: control completado, política no adoptada

Run `094009-f0c77801`, basea7e2234 más test/prerregistro congelados. **1PASS121,95s** significa diagnóstico/paridad completos, no ROI aprobado. [Muestras y comprobaciones](cr09-process-preparation-20261016.json). No se modifica producto.

Nueve procesosPython/Django nuevos, órdenesABC/BCA/CAB, una conexión física por proceso. A/B sólo preparación estática; C añade una lectura WSGInativa de cada una de las seis rutas antes de ready; todos ejecutan doce lecturas posteriores.10ksintéticos yPGpropio, GCnormal; no Gunicornfork/TCP/concurrencia/subida/Beat. BuffersPG no reiniciados. El tiempo de arranque y el ciclo completo se registran, sin hacerlos desaparecer de la evaluación.

| Métrica media | Referencia A/A | C | Lectura |
|---|---:|---:|---|
| Primeras6, wall por petición | 212.424ms | 174.665ms | −17.78% |
| Primeras6, CPU por petición | 111.423ms | 104.713ms | −6.02% |
| Arranque→ready | 1.140s | 2.273s | Incluye preparación |
| Ciclo completo | 3.551s | 4.191s | Aumenta con C |

A/A estable:4,32%wall/0,58%CPU; mejora en3/3bloques; preparación extra máxima1,317s dentro del tope5s. **Falla el ahorro mínimo20% de las primeras6**:17,78%. No se cambia a posteriori el umbral ni se usa otra ventana más favorable para aprobar. La conexión por proceso permanece propia y los comandosSQL se limitaron a lecturas/control transaccional durante las llamadas; no es auditoría de writes dentro del servidorDB. Dirty permaneció vacío.

## Fallo original y correctiva del comparador

El primer intento `093510-2f7d404e` conserva1FAIL por hashHTML crudo desigual, antes de evaluarROI. Fuentes y limpieza verificadas; [recibo del fallo y limitación](cr09-process-preparation-original-failure-20261016.json). El arnés no había guardado las muestras antes del assert, por lo que no se infieren sus números. La fuente original queda preservada.

El detalle genera un target de denuncia firmado con marca temporal. El comparador corregido verifica firma real/max_age7200 y payload exacto de listing/revision obtenido deDB; sólo sustituye ese token verificado al compararHTML. Todos los demás bytes se mantienen exactos; las rutas sin target conservan comparación cruda. Se retienen hashes crudos y comparables, payloads, HTMLsintético inicial/JSON/stderr por proceso antes de comprobar igualdad. El nuevoPASS acredita este alcance y no supone retirar controles de seguridad del producto.

Freeze completo contrastado antes de documentar, controlador/hijo porPID/start_ticks terminados, temporal retirado, contenedores propios ausentes y cgroup vacío. Python3.12.15/dependencias congeladas/PG17.11/kernel native-sealed y cuotas anteriores. Ningún recurso normal/producción/proveedor utilizado.

## Decisión

No adoptar esta preparación de rutas ni ejecutar otro corto limpio con ella. El beneficio parcial no alcanza el criterio y aumenta el ciclo completo; aún no hay prueba operativa con cuatro workers. Se conserva el hallazgo de preparación desigual como explicación parcial posible, sin convertirlo en causa única ni insistir con más rondas de calentamiento. El siguiente análisis debe buscar reducción del trabajo real por petición y revisar el alcance ya probado antes de proponer otra variante. Último p95limpio1,052089655sFAIL; CR09/N3/contrato completo abiertos.
