# B13 — Restauración y retirada bajo contrato beta, 2026-10-21

Estado: auditoría y reproducción preparadas; B13 no aceptado. Siete de18puntos cerrados. [Matriz141](141-continuidad-moderacion-beta-b13-20261021.md).

## Brecha concreta del comando

rights_object_delivery.invalidate_restored_deliveries invalida globalmente grants y bytes de caché privada. No hay llamador en el comando apply_recovery_ledger. La purga asociada a exportaciones sólo limpia grants de las copias purgadas, no todos los restaurados. Antes de exposición, la caché transitoria debe quedar invalidada independientemente de que una copia esté dentro de los propósitos borrados.

Reproducción focal preparada en test_recovery_command: fixture explícita de grant no consumido y bytes sintéticos, sin afirmar entrega autorizada al destinatario; la ejecución borra sólo medios, por lo que su copia transitoria queda fuera de esa purga. El comando debe marcar el grant purgado, borrar bytes y conservar la auditoría de descarga. Se espera un fallo antes de corregir la integración. Root de caché en tmp_path propio, sin tocar volúmenes o servicios normales.

## Ampliación prevista de restauración

El ensayo pg_dump/pg_restore y medios existente comprueba supresión posterior al backup, checkpoint independiente, rechazo de rollback de autoridad, invalidez de sesión antigua, medio eliminado, persona par preservada y publicación cerrada. No se amplía su aceptación alfa automáticamente al contrato beta.

Se preparará cobertura adicional de transición de claves: guardar con clave antigua, restaurar con activa nueva y lectores anteriores explícitos; claves MFA/safety y sus fallbacks deben propagarse al proceso aislado. La generación de cola restaurada debe ser nueva respecto al origen, procedente de configuración externa a la copia. Cache/grants y sesiones requieren reconciliación antes de exposición; recovery flag no sustituye aislamiento. El proceso de ensayo no levanta servidor HTTP ni workers sobre la copia, usa otra DB y otro MEDIA_ROOT bajo el runner local.

Retirada urgente debe comprobar restrict efectivo en el contrato romántico, no sólo dismiss. Revisar denuncia/asignación/lectura previas y las superficies públicas, incluida proyección deliberadamente obsoleta y perfiles pares intactos. No pagos ni proveedores reales.

## Límites y pruebas

Primero ejecutar sólo el caso del comando en PostgreSQL aislado y preservar el negativo. Tras corregir, ejecutar los selectores afectados y restauración real plain/encrypted, con y sin transición de claves, más namespace y moderación pertinentes. Fuentes y grafo congelados por corte, resultados terminales y limpieza con Telegram confirmado. No ensayo de horas ni nueva batería de capacidad.

No se declara B13 cerrado: credenciales/rotación restante, consumidores HMAC, retención externa y rollback de aplicación/migraciones mantienen su alcance. RPO/RTO de fixtures no son garantía productiva ni custodia/offsite/PITR acreditados.

## Primer negativo: preparación de inventario

035307-6755261a:1FAIL/0PASS/0ERROR/0SKIP,47,184sJUnit. Añadir el grant después del plan cambió correctamente el inventario de recursos y la ejecución de supresión rechazó el plan antiguo. No alcanzó el comando ni acredita la brecha de producto. [Auditoría del negativo](evidencias/b13-restored-grants-fixture-negative-20261021.json): fuentes, limpieza y TelegramERROR confirmados. Se corrige la fixture re-inventariando y revisando el plan mediante los servicios normales tras añadir la caché; no se debilita la guardia ni se altera producto. Repetición de reproducción pendiente.

## Brecha reproducida y corrección preparada

040020-7d75048f:1FAIL/0PASS/0ERROR/0SKIP,48,418sJUnit. Con inventario y plan re-revisados por servicios normales, el comando completó efectos pero dejó el grant purged_at=None. [Reproducción auditada](evidencias/b13-restored-grants-reproduced-20261021.json), fuentes/limpieza/TelegramERROR confirmados. Este corte sí acredita la omisión; el anterior sólo acreditaba la guardia de inventario.

apply_recovery_ledger ahora invoca invalidate_restored_deliveries después de verificar/reconciliar el ledger y terminar la tanda de medios. El resultado conserva publication_authorized=false y no elimina auditoría de descarga. Errores de caché/DB/validación mantienen aislamiento y no producen JSON parcial; un root de caché con symlink se prueba como error, seguido de reintento idempotente. No se modifican las guardias de recuperación ni el motor de invalidación existente.

El caso real de restauración se amplía a cuatro variantes: plain/encrypted × misma clave/transición retenida. Crea antes del plan una copia/grant legítimos de un perfil par, con descarga validada y stage local; la supresión posterior del otro sujeto no debe borrar esa copia en origen. La copia DB/medios incluye el grant. En el clon, tras reconciliar, el comando elimina grants/bytes, conserva copia y auditoría del par, y clear_recovery_sessions elimina todas las sesiones restauradas. La caché/sesión del DB origen permanece intacta como control de aislamiento. Se comprueba lectura safety y semilla MFA antigua, propagando claves/fallbacks por entorno del hijo; generación de cola nueva desde fuera de la copia. Ningún servidor HTTP ni worker se levanta sobre el clon, y el almacenamiento es local explícito. Las comprobaciones de rutas son Client WSGI, no tráfico TCP ni prueba de ingress productivo.

Nueva retirada urgente ES/EN: denuncia enlazada, acuse, asignación y lectura auditada preceden restrict. Listado, ficha/foto, favoritos y sitemap ocultan el perfil romántico patrocinado con proyección obsoleta y después de refrescar, con promociones activadas/desactivadas. Perfil par, auditoría y evidencia comercial permanecen intactos; replay no duplica restrict. No pago real ni guardia humana acreditados.

Selección prevista32casos con4workers:4restore,1extensióncomercial,1comandorecovery,6namespace,2worker/Beatgate,2retirada beta,14urgentdrill y2testigos de restricción/restauración de grant existentes. Todas las fuentes congeladas tras grafo105; sin aceptación B13 por este alcance.

## Verificación positiva local

041741-ed5d7449:32PASS/0FAIL/0ERROR/0SKIP,111,253sJUnit,4workers. [Auditoría terminal](evidencias/b13-restoration-withdrawal-terminal-audit-20261021.json): cinco restauraciones reales (cuatro variantes y extensión comercial), grants invalidados y bytes eliminados, auditoría/copia del par conservadas, todas las sesiones del clon eliminadas y caché del origen preservada. Lectores anteriores MFA/safety y namespace nuevo comprobados; cinco bases restauradas eliminadas. Retirada urgente ES/EN verificada en todas las superficies previstas. Fuentes frescas, contenedores/temporal/PID propios ausentes y Telegram PASS confirmado. Único cambio de producto existente frente al censo143: comando apply_recovery_ledger.

B13 sigue abierto: consumidores HMAC transitivos, retención y credenciales externas, procedimientos restantes de rotación y rollback de aplicación/migraciones. Siete de18puntos cerrados; sin aceptación productiva ni publicación.
