# Acta CR-08 — aceptación técnica local

Estado: verificado local. Código funcional6ebbb09; pruebas/probes844630c y818c5f7, más dos comprobaciones finales sin cambios de aplicación. No GS-01 ni preparación real de producción.

## Cobertura comprobada

- Favoritos privados únicos por cuenta/anuncio: acceso autenticado, GET sin mutación, alta concurrente/idempotente y eliminación propia. Cuenta ajena no consulta/elimina favoritos. Tras quitar exposición, referencia genérica propia eliminable sin texto/contactos/UUID público anterior. PostgreSQL y navegador móvil.
- Ciclo de vida conectado SSR: disponible4h, cancelación, pausa/reanudación, renovación confirmada desde últimos7d, caducidad y retirada. Renovación conserva IDs/revisión, treinta días y fecha editorial real; reanudar conserva fechas. Renovar pausado no publica.
- Clave/payload/versión: reintento exacto no extiende periodo ni republica tras retirada, versión obsoleta/conflicto409. Moderación/transferencia/revocación/coincidencias invalidan formularios; aprobación nueva limpia disponibilidad.
- Retirada cancela borradores/revisiones pendientes del gestor, moderación atrasada no publica. Tarea atrasada comprueba fecha/estado actuales; carrera renovación/caducidad conserva periodo nuevo. Caducidad concurrente genera un único evento.
- Agencia/editor: MFA requerido, solo persona asignada, acceso ajeno404, miembro revocado pierde acceso, propietario mantiene gestión. Representado conserva revocación/transferencia de flujos anteriores.
- Historia referencia revisión aprobada exacta y distingue sistema de gestor; panel20 eventos del gestor actual sin identidad de actores anteriores. no-store y rutas privadas redactadas en logs.

## Evidencia integrada

`uv run pytest -q` sobre844630c:166 passed450.45s, PostgreSQL/Chromium, sin skips; sesión89046 terminalexit0. Durante ejecución solo se añadieron documentación/probes independientes, sin cambios de lógica de aplicación. Dos límites finales —disponibilidad agotada sin Beat, reanudación conservando fechas, renovación pausada— passed14.47s. No presentar estos resultados como168 ejecutados en una sola suite; integración final C deberá volver a ejecutar conjunto completo sobre su commit.

Docker app/worker/beat reconstruidos, UID10001, migraciones0012 y static/check al día. Worker/Redis aplica caducidad en0.463s; dos tareas reales tienen resultados1/0 y un evento. Beat sin envío manual aplica caducidad en52.001s; logs de planificación/worker y estado PostgreSQL coinciden. Probes crean registros técnicos sintéticos siempre inelegibles, no acreditan verificación real ni datos de producción. Chromium/Caddy confirma favoritos, entrada genérica en pausa, disponibilidad/pausa/reanudación/cancelación y recarga, con muestra publicada y sin disponibilidad al terminar. No reseteo de la muestra.

Ruff/format/check/migraciones/diff-check limpios. Registro detallado docs/18; probes/scripts y comandos README. Celery ignora resultados: primera observación prematura corregida a estado DB/logs, sin aceptar fallo como éxito.

## Pendientes y siguiente etapa

CR-09 denuncias/derechos/reclamación sin cuenta; CR-10 promociones. Retención y supresión jurídica/backup todavía deben conectarse y verificarse, no resueltas por retirar anuncios o conservar eventos. Dataset/proveedores reales/operador/moderación humana y demás gates externos pendientes. Estilo/idiomas de estados/a11y/SEO y carga/performance posteriores. Próximo CR-09 según contratos/10 y fuentes primarias revisadas; no separar frontend/backend todavía.
