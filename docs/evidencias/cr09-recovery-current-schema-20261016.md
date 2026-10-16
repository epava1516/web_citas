# Restauración real con esquema conservador0022 actual

`20261016-134915-8495c346`, fuente bcdd9b4 con test ampliado incluido en los hashes iniciales: **3PASS72,59s/0FAIL/ERROR/SKIP**. Una restauración PostgreSQL/medios real y dos variantes de finalidad publication incluida/excluida. Fuentes y limpieza verificadas independientemente. [Recibo completo](cr09-recovery-current-schema-20261016.json).

Motivo concreto: el anterior9PASS000952-d23d1fae conserva tests y módulos recovery_apply/recovery_media idénticos, pero sus hashes de publication_state y migraciones0020–0022 difieren de los actuales. No bastaba trasladar ese resultado a la restauración del nuevo esquema. La ampliación comprueba en la base restaurada el registro0022, ausencia de helpers rechazados y `prosrc` exacto de MARK0020 y tres funciones originales de dependencia. No modifica aplicación, plazos ni permisos.

| Métrica del pequeño fixture sintético | Anterior000952 | Actual134915 |
|---|---:|---:|
| Crear copia PG/medios | 0,872903s | 0,784828s |
| Restaurar y reconciliar | 5,090638s | 5,076870s |
| Edad máxima observada de la copia al terminar | 6,717184s | 6,601110s |
| Archivo pg_dump | 1.052.520bytes | 1.053.336bytes |

No atribuir estas diferencias a optimización o hardware; una observación por versión, fixtures pequeños y fuentes de esquema distintas. El test exige restauración≤8h y edad de copia≤1h en este ensayo; no prueba cadencia de backup, pérdida de transacciones en un incidente real ni RPO/RTO productivos.

## Relación con finalidades y excepciones

| Recurso del backup anterior a supresión | Reaplicación y control |
|---|---|
| Credenciales, sesiones y preferencias | Checkpoint independiente sintético posterior al backup; autoridad antigua rechazada sin efectos. Tokens/códigos/favoritos del sujeto retirados, sesión antigua no autenticada. Otro usuario preservado. |
| Copia temporal del sujeto | Finalidad transient_copy del recibo reaplicada; no se interpreta como permiso para destruir las fuentes de otros sujetos o evidencias excluidas. |
| Publicación/perfil | Proyección del sujeto ausente antes de refrescar; reconstrucción no elegible y sin texto/fechas, detalle404. Variante con finalidad publication excluida preserva la copia exacta y terceros. |
| Medios originales/derivados | Inventario íntegro y SHA antes de copiar/restaurar. Borrado físico tras autoridad vigente; archivos restantes coinciden exactamente con inventario menos rutas autorizadas. Repetición no borra más. |
| Registro y checkpoint de recuperación | Fuera del dump/medios de negocio restaurados; comparación con referencia esperada. Separación local no acredita custodia externa ni supervivencia del servidor. Tombstone/recibo no es un backup. |
| Estado derivado MOD05 | Incoherencia deliberada sólo en DB restaurada propia, marcado global, triggers actuales y comando real `refresh_publication_state --all` comprobados. No se autoriza publicación por haber completado la reconciliación. |

Se mantienen los controles anteriores de caso/sujeto/ámbito/rollback y medios compartidos en sus evidencias separadas; no afirmar que se repitieron los seis tests recovery_apply intactos. El pequeño ensayo actual no sustituye el escenario comercial de restauración previo ni demuestra todas las finalidades/archivos históricos o todas las dependencias de la versión final.

Limpieza: prueba confirma DROP de la DB adicional propia, runner y pytest ausentes porPID/start_ticks, temporal retirado, contenedores PG/Redis ausentes y unidadMainPID0/ControlGroupvacío. Sin datos reales, proveedores ni servicios normales. Se conserva el fallo original de proyección como antecedente; no hubo nuevo fallo funcional en esta selección.

Pendientes: versión común/N3, completar asociación por recurso/finalidad de las fuentes históricas pertinentes y sus excepciones; custodia/autoridad/cadencia operativa de producción permanecen separadas. P95 del directorio sigue0,862172866sFAIL. No aceptación globalCR09.


## Ampliación final: copia temporal restaurada

Ejecución135551-2e40c644: **1PASS54,54s**, [recibo](cr09-recovery-restored-copy-20261016.json). El test ahora exige carga cifrada, imágenes y partes presentes en el dump restaurado antes de reaplicar; después verifica carga vacía/purged_at, imágenes/partes vacías, mismasfilas y action/proof inalterados. Resuelve un hueco de aserción directa, no un defecto demostrado de aplicación. El anterior3PASS verificó esquema y variantes de finalidad con su fuente anterior; no afirmar que incluía estas nuevas aserciones ni sumar selecciones comoN3.

| Métrica fixture | Esquema134915 | Copia ampliada135551 |
|---|---:|---:|
| Crear copia | 0,784828s | 0,751641s |
| Restaurar/reconciliar | 5,076870s | 5,030987s |
| Edad máxima observada | 6,601110s | 6,542368s |

No comparación causal de velocidad. Cubre bytes cifrados residentes en DB, no restauración de un repositorio S3 ni política productiva. Caso anterior135343-3326cf83 falló al serializar UUID del test antes de lanzar el hijo; se [conserva](cr09-recovery-restored-copy-original-20261016.json), se corrigió str(export.pk) y ambas limpiezas fueron verificadas. La DB adicional propia se eliminó mediante finally; runner/pytest/temporal/contenedores ausentes.
