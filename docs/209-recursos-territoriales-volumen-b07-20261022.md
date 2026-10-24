# B07 — Preparación de observación territorial a volumen

Estado: diagnóstico217 terminado y auditado; observación instrumentada, sin aceptación de capacidad.

B07-216: habilitado observador de recursos en diagnóstico corto territorial10000, separado de capacidad limpia.56guardas PASS; espera de preparación acotada1800s sólo en corto, captura600s/600muestras/8MiB intacta. Sin cambio de producto, sin ejecución grande ni cierre B07;8de18.

## Evidencia reutilizada y hueco

El [corto203](202-corto-territorial-kernel-b07-20261022.md) ya prueba la mezcla territorial limpia a10000. No repetirlo como confirmación. [209](205-identidad-reposo-observador-b07-20261022.md) acredita identidad y reposo del instrumento a10; [211](206-backlog-nativo-despacho-b07-20261022.md) acredita dos marcas y worker real pequeño; [215](208-escala-territorial-49pendientes-b07-20261022.md) acredita equivalencia funcional49 a100/1000/10000 con reparación manual. Ninguno observa CPU/RSS de servicios propios en esta mezcla grande. La siguiente ejecución es instrumentada y no reemplaza203 ni acepta B07.

## Cambios del instrumento

El lanzador y parser admiten `--service-resources` con modo funcional o corto; contractual, upload-calibration y preflight siguen rechazados. Backlog sigue restringido al escenario funcional pequeño. Cuotas, propiedad, rutas, política del cliente, GC, Beat y workers se conservan.

El observador conserva espera de topología600s. Una vez identificada la topología, permite hasta1800s desde inicio para recibir la primera fase en corto (600s funcional). La captura tiene límite separado600s desde la primera fase y conserva600muestras/8MiB, periodo0,5s y tres muestras posteriores. No muestrea preparación sin señal ni atribuye sus recursos a carga. La nueva prueba simula700s de preparación sin dormir ese tiempo; no es verificación Docker ni medición real.56guardas del lanzador/lector pasan, incluidos rechazos de modos y fases incompletas; Ruff PASS confirmado.

## Protocolo217 antes de congelar

Una sola ejecución instrumentada:10000publicados7000/3000,2000derechos sintéticos por servicios nativos,42slots/30rutas seleccionadas, ESEN,60s/20rps/1200dinámicas y1upload. Imágenes locales inmutables, kernel nativo y perfil8CPU/8GiB/swap0; observador host externo al presupuesto y coste propio separado. Sin proveedores, personas reales ni publicación.

```bash
.venv/bin/python scripts/run_notified.py --name 'B07 recursos territoriales217 instrumentado' -- .venv/bin/python scripts/run_vps_capacity.py beta-http-short --territorial --service-resources --cpu-budget 8 --app-image sha256:6936424d8c105237645efd3424be6ef31c74f7cb32904db3c963ddf9a7e1f44e
```

Antes: actualizar grafo dirigido y comprobar documentos, imagen local y628fuentes producto; congelar protocoloSHA, mapas completos y fuentes afectadas. No ejecutar hasta terminar esas comprobaciones. Ejecución persistente sin otra batería/build; avisos Telegram y relevo/compactación/reactivación del mismo objetivo si se pausa por espera larga. Conservar terminal negativo, sin repetición automática.

Después: auditar JUnit/report/launcher y hashes antes de editar protocolo. Exigir contabilidad y guardas del corto sin rebajarlas,1200dinámicas conciliadas/400porcategoría600poridioma,upload persistido, rutas/frías completas, generador válido, cuotas reales. Verificar seis identidades mínimas con PID/startticks/cgroup exactos, muestras completas porfase y≥3posteriores, intervalos CPU positivos y contadores no decrecientes, RSS/memoria y presupuesto/almacenamiento sin atribución exclusiva. Informar percentiles observados como instrumentados, no comparación causal con203. Confirmar límites de artefactos, retirada de contenedores/temporales/procesos y recibos. Cualquier error invalida aceptación del instrumento para este corte; no altera203 ni los negativos históricos.

Persisten backlog grande con worker/colas, mezcla de estados TCP y PRODUCTION/checked según [matriz180](180-matriz-cobertura-b07-censo-geografico-20261021.md). No900automático, aceptación global ni cierre por documentación.

## Recuperación del entorno

B07-216 recuperación: imagen reconstruida y732fuentes verificadas,628producto intactas; preflight real8CPU READY_NOT_CAPACITY con limpieza confirmada.217 pendiente de congelación y ejecución; B07 abierto8de18.

[Auditoría de preflight](evidencias/b07-image-recovery-preflight-20261022.json). Archivo de base verificado por SHA256; dependencias iguales y overlay actual construido sin red. Primer build falló por referencia FROM de ID, corregida usando etiqueta local propia; primer preflight INVALID por RustFS ausente. Ambos negativos conservados. RustFS recuperado por digest exacto; segundo preflight `20261022-072004-e12543e5` terminó READY_NOT_CAPACITY, con S3/Caddy/worker/Beat reales sintéticos. La imagen nueva no tiene la identidad de la antigua ni acepta carga grande.

## Resultado217 auditado

B07-217: diagnóstico territorial instrumentado auditado:1PASS/900,148sJUnit,10000publicados7000/3000 y2000derechos sintéticos;1200dinámicas exitosas y1upload. p95 observado538.876ms; generador máximo15,662ms.182muestras (62previas/117carga/3reposo), seis identidades verificadas;628producto, fuentes, cuotas8CPU/8GiB, limpieza, Telegram, compactación y reactivación del mismo objetivo confirmados. Sin aceptación de capacidad ni cierre B07;8de18.

[Auditoría217](evidencias/b07-resources217-territorial10000-20261022-audit.json). Intervalo de carga observado59,617s: aplicación1,910cores y PostgreSQL1,532cores; reposo posterior1,042s: aplicación0,038cores y PostgreSQL0,0013cores. Son intervalos parciales, sin atribución causal ni comparación limpia con203. Memoria conservadora1743192064bytes; almacenamiento4865392640bytes. Observador externo:6,301sCPU,982,667s de vida y RSS terminal23781376bytes; este RSS no es pico exclusivo y la duración incluye preparación.

Los dos primeros intentos de auditoría fallaron por selección del recibo terminal e importación local del auditor; corregidos sin repetir la carga. Se conservan ambos negativos. El protocolo original y sus huellas permanecen archivados antes de esta actualización. Siguen pendientes backlog grande con worker/colas, mezcla de estados TCP y PRODUCTION/checked.
