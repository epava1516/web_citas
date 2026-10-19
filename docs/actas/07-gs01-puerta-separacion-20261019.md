# GS01 — puerta de separación técnica local, 2026-10-19

Se acepta GS01 para continuar B-F/B-B bajo el contrato16. Revisor: Codex principal. **Corte único probado `e99dc962c6403e23e53b7bfb00b2442aef3ac341`**, rama local `codex/mod08-vps-server-20261012`, worktree VPS autorizado. Conserva la integración MOD08 y el commit obligatorio `c46d0e1`, ancestros del corte. El master original y sus cambios locales permanecen preservados; esta acta identifica el corte integrado VPS y no afirma que se haya actualizado o publicado master.

La [matriz de siete requisitos literales](../evidencias/gs01-local-acceptance-matrix-20261019.json) registra decisión, motivo y evidencia. La [auditoría terminal](../evidencias/gs01-common-terminal-audit-20261019.json) verificó fuentes, selección, omisiones, limpieza y recibos, sin inferir aceptación por contar etapas.

| Condición del contrato16 §6 | Decisión |
| --- | --- |
| CR01–CR10 y recorridos esenciales | Aceptado: actas locales y prueba común actual de cuenta/agencia/publicación/descubrimiento/ciclo/derechos/comercio. CR09/CR10 vigentes en actas05/06. |
| Operaciones/estados/contratos conocidos | Aceptado:19familias,165patrones documentados,14contratos congelados y reportes actuales vinculados. |
| Sin cambio coordinado conocido pendiente | Aceptado: asíncrono/lotes ya integrados; residual BF/BB conserva campos/rutas/autoridad/estados/semántica. Hallazgo compartido futuro vuelve a mini-flujo. |
| Errores de permisos/publicación/privados/carga | Aceptado localmente: regresión completa actual, cobertura necesaria y carga válida reproducida con misma aplicación. No borra FAIL/ERROR/INVALID anteriores. |
| Estados y variantes | Aceptado: matriz finita con navegador/servidor,ESEN/roles/recarga,JS/noJS y estados asíncronos/lote. Accesibilidad visual completa sigue BF. |
| Adaptadores externos aislados | Aceptado: recursos propios reales y adaptadores de prueba explícitos; no se acredita proveedor/identidad/pago externos ni producción. |
| Residual asignado | Aceptado: [trece puntos BF/BB](../98-inventario-residual-post-gs01.md), evidencia de salida y regla de retorno compartido. |

## Batería común y omisiones

| Partición | Run | PASS | Subpruebas | SKIP | Fallos |
| --- | --- | ---: | ---: | ---: | ---: |
| Funcional,2workers | `20261019-095237-9bf4f4f2` |3217|4|122|0|
| Capacidad,1worker | `20261019-124016-c5996270` |290|0|8|0|

**3637nodeids únicos,3507PASS más4subpruebas,130SKIP**, selecciones disjuntas sobre el mismo commit,1574huellas de entrada iguales en ambas y4252entradas congeladas auditadas. Los130omitidos son exactamente los de la batería anterior completa, conservados por fuente y digest en el recibo. No se presentan como PASS ni se identifica un perfil con exclusiones como N3 por sí solo.

Se concilia la evidencia necesaria separada: fuentes/contenido revisados de CR09, seis matrices TCP/JSON real mayor de8MiB, matriz de ocho rutas y marca positiva Beat→worker, más carga contractual válida/repetida y recuperación real actual. Las fuentes técnicas antiguas sólo difieren en el cuerpo del test de broker ahora corregido: sus aserciones y el resto del módulo son idénticos y ese test no se invoca en los runs reutilizados. Producto y harness seleccionado siguen iguales. No se repite carga por documentos o por un cleanup de test ajeno al escenario, conforme MOD02.

El intento anterior con8fallos/OOM global y el negativo ordenado de Celery se conservan. La corrección afecta sólo al test: conexión y producer propios, sin cerrar app global; par ordenado y siete timeouts originales pasan, y ahora toda la batería vuelve a pasar. No aumento de timeout ni de cuotas. `memory.events` no registra OOM en esta ejecución. Los clientes/DockerPGRedis/temporales/PIDs propios y las fuentes se verificaron independientemente; recibos Telegram de ambas fases y del pipeline completo son `sent/PASS`.

## Contratos congelados y continuación

Manifiesto de14archivos `docs/contratos/*.md`, SHA256 **`5cb6b6f773b05b9fe09a378415cffc1ad05ed4303e3cd51be309af4e615e7c7c`**, algoritmo y huellas individuales en la [auditoría](../evidencias/gs01-common-terminal-audit-20261019.json). Congelación significa cambios controlados/versionados; cualquier modificación compartida exige contrato, mini-flujo y verificación navegador antes de seguir separado.

El [residual](../98-inventario-residual-post-gs01.md) asigna BF01–06 y BB01–07 y conserva C-S01 como integración final. Primero reutilizar evidencia válida y corregir sólo riesgos/requisitos/defectos demostrados. **GS01 no termina B-F/B-B/C ni acredita entrega global o producción.** MOD09 conserva aceptación provisional de expedientes grandes y deuda mejorable. Identidad/operador/proveedores/textos definitivos/cobertura nacional real/revisión jurídica y seguridad externa siguen preparación de producción. No publicación, contratación ni datos reales.
