# Prompt autónomo para Claude principal — MOD-07

## Documento histórico de relevo — 2026-10-24

Este prompt conserva el relevo MOD07 del 2026-10-09; no es una orden actual de invocación, pausa o dirección exclusiva. El relevo posterior autorizado en AGENTS devolvió a Codex la dirección y ejecución local de MOD08. Para continuar prevalecen las instrucciones posteriores, el [contrato de ejecución vigente](16-contrato-ejecucion-desarrollo.md) y [seguimiento17](17-seguimiento-desarrollo.md). El bloque se preserva íntegro como antecedente; sus procesos, colas, límites de progreso y próximos pasos no se reanudan desde esta página.

Autorización vigente por aclaración del usuario; sustituye la propuesta acotada. Copiar solo el bloque. Codex sigue pausado y no ha invocado a Claude.

```text
Completar autónomamente la entrega técnica local restante de web_modelos conforme a MOD-07. Claude principal puede leer/editar, usar shell/Docker propio, probar, corregir, hacer commits/integración local y aceptar con evidencia. No esperar aplicación de Codex ni detenerse tras propuestas o hitos. El goal Codex sigue pausado; este goal Claude continúa hasta el cierre completo.

Leer primero AGENTS.md, /home/felidae/proyectos/arquitectura_codex/docs/AI_ENGINEERING.md completo, docs/16-contrato-ejecucion-desarrollo.md, docs/17-seguimiento-desarrollo.md, docs/relevo-claude-20261009.md y docs/evidencias/relevo-local-20261009.json. Después matrices83/88, contratos14/15, seguridad11,ci-local,evidencias18 y objetivos-capacidad-local-20261009.json. MOD-07 sustituye para Claude principal «Claude propone; Codex aplica» y la parada tras propuesta. V1 solo rige delegaciones por su adaptador: no alterarlo ni cambiar el contrato externo.

Orden CR09→CR10→GS01→BF/BB→C. Cierre exige matrices satisfechas, recorridos reales/contratos/documentación, actaGS01, frontend/backend terminados, N3 sobre la misma versión integrada, carga y restauración exigidas y acta técnica local. Producción separada. No inventar porcentajes ni sumar versiones como aceptación.

Primera acción: reconciliar Git/huellas y revisar críticamente P1–P8 y el controlador sin commit; no aplicar la propuesta externa a ciegas. Leer flags/mounts no prueba límites kernel de storage/logs/memoria. Verificar montajes,limpieza exacta,timeouts/salidas parciales. Validar con N1/N2 propios reales antes de cargar. Después continuar p95 binario, etapas pendientes, censo/cobertura, N3 y toda la secuencia, sin pedir aprobación por hito.

Base12467fd; revisar HEAD actual y cambios documentales. Preservar seis fuentes incompletas y propuesta GraphQL independiente; no activarla. N2 confirmado63PASS sin fallos/errores/skips: no capacidad/N3. Controlador no ejecutado,RuffF401. Limpieza13PASS/1FAIL: GC emitió2/3peticiones, fuentes intactas, causa sin diagnosticar. Conservar negativo y resolver por hipótesis finita.

Aceptados: BASE/CR01–08, lecturaCR09 y componentes de matriz88 en sus alcances. Verificaciones de conservación/restauración/correo/urgencias y capacidad escalar son parciales. CR09 integral y fases posteriores pendientes. Último p95 binario: guardado4,065/3,802s≤5; revisión2,372/2,395s>2, no reensayado tras63PASS. Etapas posteriores/presupuesto global NOT_PROVEN.

Objetivos inmutables:2expedientes simultáneos independientes;1500revisiones,16MiB JSONUTF8 necesario y64MiB originales/caso,±1%,sin padding/duplicación artificial/truncado. Total4CPU/8GiBRAM/20GiBstorage efectivo,swap0; pico global disjunto con cachés≤6GiB,RSS por proceso app≤1GiB. Preparar≤60s/op; página≤50filas,p95HTTP≤2s,primera apertura aparte; guardar/aprobar p95≤5s; generar≤120s; final/inspección/aprobación/cierre≤30s/op; paquete≤8MiB,p95TCP≤5s,cuerpo completo/hashes íntegros. ≥20muestras nuevas/caso/variante,nearest-rank,sin replay/mezclas. AusenciaNOT_PROVEN; instrumento inválidoINVALID; incumplimiento válidoFAIL. No reducir criterios para PASS.

CI local sin gasto,PG17/Redis7.4 reales propios,nativos pinned,Chromium ES/EN/móvil,datos sintéticos. Registrar selección/HEAD/huellas/recursos/timeouts antes; congelar fuentes; guardar XML/logs/negativos/skips; retirar solo recursos propios. No simuladores como evidencia real ni repeticiones rutinarias. Preservar trabajo ajeno/dudoso y consumo histórico; no reset/stash automático ni historia reescrita.

No push/publicación/proveedores/compras/datos reales ni tocar servicios normales. Consultar solo por cambio material de alcance/objetivos/coste,acciones externas/datos reales o recursos ajenos sin alternativa propia válida. Corregir fallos compatibles y continuar. No completar el goal por propuestas,tests parciales o controlador listo.
```
