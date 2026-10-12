# MOD-08 — cobertura temprana con Memray, fallo y evidencia recuperada

[Datos y stacks saneados](mod08-vps-memray-cobertura-temprana-20261012.json).
SHA9b149cb945010fc61dcfa93e5ab8683258d79a29. Sonda anterior
20261012-080135-d933f15c pasa1test49.641s, launcher0; PGrol restringido reconecta,
GunicornHTTP200, Memray1.20.0 Python3.12.15, dependencias originales, fuentes/cleanup
auditados. [Fallos previos](mod08-vps-memray-http-20261012.md) conservados.

Diagnose20261012-080436-d42bb751 no completado: primer resumen excede2M registros
y registra FAIL. No se aumentó ese límite. La aplicación ya había consumido la
respuesta cuando falla el resumen; el flujo podía continuar. Codex observa el
fallo, conserva la traza y señala SIGINT sólo al pytest propio identificado por
label yargv exactos. Teardown/archivo/cleanup pasan, resultadoERROR1FAIL477.734s;
cero errores/skips, fuentes1414 sin cambios. CotaRAM2016485376bytes<6GiB.
No perfil tardío ni latencias aceptables derivadas de este recorrido incompleto.

Traza temprana completa15,285,897bytes, SHA256
72e55154ab62c560368baa4d9dcb35e2a143f8ca99dacf6ee00d83a16bd5ca72.
Se copió mediante cat propio en bloques1MiB, máximo256MiB, antes de retiradaapp.
Docker cp falló, se conserva recibo de transferencia exitosa alternativa.
Archivo binario privado ignorado, sin heap/SQL/locals en documentación.

Replayoffline separado propio1CPU/512MiB, swap0, rednone, rootreadonly, capdropALL.
Un primer arranqueUID1000 falló por permisos; se usó UID/GID reales1002/1004.
Memraystats procesó todos10,286,265registros. Primer análisis de todos los stacks
excedió10Kclaves; se mantuvo el límite y se filtró sólo solicitudes>=64KiB antes
de resolver stacks. Así escanea todos los registros con78stacks grandes en7.718s.
La limitación de filtros queda explícita. Bindreadonly de binarios exactos corrige
las advertencias de rutas; memfd sellado /proc/self/fd/11 no puede resolverse
offline y se conserva esa advertencia. No sustituir símbolos por otrosbinarios.
Ambos contenedoresoffline ausentes, independientes del cleanup del recorrido.

| Métrica de una petición temprana instrumentada | Valor |
|---|---:|
| Asignaciones/reasignaciones positivas acumuladas | 1,906,665,240bytes |
| Pico retenido durante Tracker | 176,870,481bytes |
| Asignaciones atribuidas a _read_image_blob | 939,524,656bytes |
| Asignaciones atribuidas a canonical_bytes | 318,672,423bytes |

No CPU, bytes deIO ni p95: asignaciones solicitadas pueden contar crecimiento
y contracción del mismo buffer. _read_image_blob hace64solicitudes de
10,485,794bytes de reserva mientras los archivos devuelven unos4MiB: evidencia
de sobreasignación en stream.read(10MiB+1), no permiso para omitir lecturas frescas.
Stack grande939,473,128bytes: read_image_blob→image_contents→audited_images→
selection_review.record→coverage_inspect_page→inspect_batch.

Fuente canónica: init ycontrolsalida inspection_source atribuyen66,194,184bytes
acumulados cadauno, en stacks distintos. Ambos son controles deliberados; no
suprimir el control de salida o asumir que toda serialización es redundante.
Fuente compartida sí se propaga; no hay prueba de reconstrucciones ordinarias
múltiples. Las89894asignaciones de Model.__init__ no son89894modelos.
fast_canonical._check:64 llama kernel.try_check, las256330asignaciones no prueban
fallback Python. Se rechazan esas interpretaciones.

Queda investigar CPU de rutas dominantes y reducción segura de copias/
materialización JSON. Repetidos descifrados de selección localizados estáticamente;
no memoizar aprobación, claves ni autoridad. Cualquier corrección requiere pruebas
negativas actuales y measure sin instrumentos, repetir sólo siPASS.
No N3/capacidad global/aceptaciónHTTP. Los últimos p95 reales siguen siendo
3.547708/7.115129/7.099972s, previos a la corrección de copiasdelcodec.
