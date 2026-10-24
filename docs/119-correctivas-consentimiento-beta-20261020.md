# Correctivas de consentimiento vigente y preflight de pruebas

Fecha:2026-10-20. Estado: focal de consentimiento verificada y auditada; sin aceptación beta.

La regresión155011 reveló peticiones sintéticas con publishing dev-1 cuando bootstrap activa dev-romantic-1. accept_consent y self_consent contrastan la versión legal antes de bloquear Person. Esos payloads no alcanzaban las guardas de revocación, publicación borrada y concurrencia que las pruebas pretendían verificar. No se modifica la autorización de producto.

Se actualizan únicamente los payloads vigentes en manager_review, manager_appeals, organization_manager_localization, contact_erasure y representation_erasure: consultan publishing activo por idioma del endpoint. Se mantienen409, sincronización entre hilos, independencia del revisor, ausencia de nuevos grants y persistencia. test_verification añade un POST dev-1 que conserva consentimiento y no crea grant antes del positivo vigente; el rechazo de documento antiguo sigue siendo obligatorio.

Focal prevista: esos cinco archivos, browser_manager_appeal y test_verification completos; PostgreSQL/Redis/Chromium reales locales, dos workers, snapshots e índice de broker aislado. Registrar terminal, fuentes, limpieza y Telegram antes de aceptar. No sustituye común afectado ni regresión amplia.

## Eficiencia de pruebas verificada

scripts.local_ci_requirements comprueba la imagen RustFS fijada al recoger casos con object_store; el fixture también comprueba solicitudes dinámicas. Docker inaccesible, timeout o imagen ausente producen ERROR temprano; no hay descarga automática ni SKIP. Se conserva almacenamiento real y --pull=never. Seis unitarias PASS9,27s; negativo real de colección EXIT4 en9,64s sin ejecutar casos; imagen exacta descargada y prueba S3 real immutable/read/rotation/purge/replay PASS12,18s, contenedor retirado. Recibos Telegram1792520342405749897-1979186,1792520373463110152-1984516 y1792520415971648673-1990867 sent. El negativo esperado no se declara PASS funcional.

No hay comparación nueva dos frente a cuatro procesos ni porcentaje de aceleración medido. La configuración oficial ya admite paralelismo por archivos con base/medios/broker aislados. Capacidad conserva ejecución aislada y recursos/topología de producto. B00residual y B07–B17 siguen pendientes; corto TCP20RPS FAIL y900s bloqueado.

## Terminal de consentimiento

182339-516d52a7:34PASS/0FAIL/0ERROR/0SKIP en136,15s, siete archivos completos. Auditoría beta-consent-focused-terminal-audit-20261020.json verifica fuentes actuales iguales a congeladas,622fuentes de producto idénticas a la regresión negativa155011, PostgreSQL/Redis propios retirados, temporal y procesos ausentes, recibo1792520787830851494-2021052 sent. Sólo cambian payloads de pruebas y un negativo legal añadido; autorización de producto intacta. No sustituye regresión amplia ni capacidad.
