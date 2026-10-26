# N09O — referencia local de purga de exportaciones verificada

Estado: siete perfiles finitos aceptados localmente como referencia del consumidor;
sin cambio de aplicación ni mejora atribuible. N09 sigue abierto con139IDs y8/13
bloques obligatorios aceptados. Alpha/noindex. [Prerregistro458](458-n09-o-prerregistro-purga-exportaciones-20261026.md).

Run: `20261026-172951-c83b9a2e`,7PASS/0FAIL/ERROR/SKIP,118,070sJUnit de QA,
1.782huellas del runner intactas. PostgreSQL17/Redis7.4propios, parser nativo
fijado yTask.run serial. Auditoría independiente PASS:17fases,1.117archivos locales
retirados y1.119intentos unlink. Todos los modelos restantes, medios yatributos
no autorizados permanecen iguales por snapshots/hash; pines yreplay preservados.
Contenedores exactos ausentes ytemporal del runner retirado; Telegram terminal
yde auditoría con delivery=sent. No quedan pruebas activas de este lote.

Selección:0/1/10/100/1001vencidos con contenido pequeño Fernet real, filas
Image/Part ydelivery local. Orden exactoPK comprobado;1001se consume1000→1→0.
Son clones de fixture tras un seed nativo; no1001autorizaciones o paquetes completos.
Filas originales/acciones/FK/contenidos no seleccionados permanecen sin cambios.

Lock: tres vencidos, una fila bloqueada por conexiónPGdistinta. La otra conexión
completa2mientras el holder sigue en transacción; después1yreplay0. Cierres de
conexiones, finalización de thread yliberación de lock confirmados.

Fallo: OSError controlado antes del segundo unlink. Primer archivo desaparece,
segundo permanece, todas las filas SQL coinciden con su snapshot anterior.
Restituir unlink consume2exports yborra el archivo restante; replay0. La llamada
missing_ok al archivo previamente retirado cuenta como intento sin nueva baja.
No caída abrupta ni fallo real de proveedor; el rollback SQL no restaura archivos.

## Tabla anterior y posterior

| Escenario | Referencia Task.run | SQLexecute observados | Posterior | Mejora atribuible |
|---|---:|---:|---|---|
| Volumen 0 | 6.549 ms | 1 | Sin candidato | No evaluable |
| Volumen 1 | 17.710 ms | 8 | Sin candidato | No evaluable |
| Volumen 10 | 35.484 ms | 17 | Sin candidato | No evaluable |
| Volumen 100 | 124.235 ms | 107 | Sin candidato | No evaluable |
| Volumen 1001 | 2097.922 ms | 1007 | Sin candidato | No evaluable |
| Lock: 2 de 3 | 33.249 ms | 9 | Sin candidato | No evaluable |
| Fallo en segundo unlink | 6.893 ms | 3 | Sin candidato | No evaluable |

Segunda fase de1001:21,629ms/8SQL; replay0:16,607ms/1SQL. Tras lock:
12,752ms/8SQL; recuperación del fallo:21,975ms/9SQL. Una muestra por fase,
caché calentada ydatos pequeños; sin p95, CPU/capacidad/SLA, proveedor o
comparación causal. SQLexecute yunlink se solapan con wall yno se suman.
Preparación, snapshots, asserts yQA quedan fuera de Task.run. Se conserva la
implementación: no iniciar optimizaciones marginales sobre esta referencia.

Incidencia: la comprobación documental previa detectó una adición lateral a340/341
sobre la limpieza final obligatoria deartifacts enN15. La shell continuó por no
condicionar el lanzamiento al éxito del comando anterior. Se conserva el incidente,
sin afirmar preflight completo ni raíz congelada porroot antes del lanzamiento.
El runner oficial sí capturó antes de ejecutar sus1.782huellas, luego verificadas
íntegras; el protocolo458yel grafo de prerregistro tenían sus hashes previos,
también inalterados. La adición no cambió escenario, instrumento ocriterioN09O.
Por ello se aceptan los oráculos ymedidas finitos auditados, no una conformidad
documental previa inexistente. Antes del siguiente hito, refrescar la semántica
lateral; futuras secuencias usan check=True ocondición estricta. No repetir QA
válida para subsanar una actualización exclusivamente documental.

Revisión: escritor nativo aislado,worktree26MiBsin evidencias históricas. Reporte
inicial con formato no canónico rechazado ycorregido; root revisó el instrumento,
reforzó conjunto ordenadoPK,digests porfase yJSONsinNaN. Ruff ygrafo focal PASS;
AST del instrumento ysemántica458, sin reemplazar la reconstrucción finalN15.
Sin cambios de aplicación,migraciones,servicios oCI. Consumo nativo desconocido,
ClaudeV1nuevo0; historial anterior conservado.

Conciliación: matriz de trabajo139/139sin disposiciones aceptadas todavía. Se
contrastaron25casos originalesPASS de cuentas/fotos/rectificación yla identidad de
fuentes; cambios posteriores de productores requieren conciliar sus evidencias
aceptadas N03/N07/A–H, no equiparar todos los bytes al run histórico. Alias anidados
yBeat no suman ejecuciones. Los supuestos humanos/proveedor siguen separados.

Custodia: [archivo saneado](evidencias/n09-o-purga-exportaciones-20261026.tar.gz),
SHA256 `d23796eb98949dbb826b0cd7f4ccaaf1eaddc0c4405d75b210e571799aaf7ae2`,14miembros con manifiesto comprobado.
No contiene logs crudos,entorno,credenciales,payloads,grafo completo ni contenidos
laterales. Auditoría local detallada enartifacts/recorridos-n09-o-20261026/;
N15conserva su obligación posterior de resumen duradero yvaciado completo deartifacts.

Límites: PostgreSQL yarchivos locales reales; Task.run no demuestra worker/Beat,
S3,proveedor,retención natural,generación/descarga actuales ocapacidad con paquetes
grandes. No extender estos resultados aautoridadHTTP. N09pendiente de puentes
y139disposiciones; N10/N11/N15pendientes,N02restante al final,N12–N14condicionados.
