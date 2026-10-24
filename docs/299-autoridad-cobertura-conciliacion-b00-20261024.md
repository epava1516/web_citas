# B00-340 — Autoridad de revisión de cobertura y conciliación final

Fecha:2026-10-24. Investigación local con identidad y material sintéticos; no aceptación B00.

B00-340: corregida autoridad antes del descifrado de cobertura tras bloqueo PostgreSQL. Reproducción conservada1PASS/4FAIL; regresión afectada25PASS/0FAIL/0ERROR/0SKIP. B00aceptado en conciliación local por acta17, sin aceptación global de rutas privadas.

## Hipótesis y criterio inicial

En [context](../apps/safety/rights_access_coverage_review.py) la autorización precede al bloqueo de RightsAccessCoverage. La inspección descifra su cuerpo y reautoriza posteriormente. Eso no demuestra una fuga; se investiga si una revocación durante esa espera debe impedir incluso el primer descifrado. El contrato conserva autoridad fresca y acceso privado auditado; las comprobaciones finales existentes pueden impedir devolver contenido o confirmar acciones aunque haya descifrado previo.

La [reproducción](../tests/test_rights_access_coverage_authority_races.py) construye cobertura mediante preparación de información, revisión independiente, exportación, prueba sintética renovada, declaraciones y referencias reales locales. No sustituye autorización ni base de datos. Dos conexiones PostgreSQL, bloqueo de la fila de cobertura y pg_blocking_pids verifican la espera real. Durante ella se conserva el control válido o se revoca permiso respond_rights_request, versión de sesión, versión MFA o is_active. Un observador de checked_body cuenta sólo descifrados del cuerpo de cobertura y delega el descifrado real; no registra contenido. Se exige denegación sin descifrado ni acción persistida en las cuatro revocaciones, y contenido/auditoría válidos en el control.

## Prerregistro de ejecución

Una selección explícita de cinco casos, un worker, perfil focused del runner propio; PostgreSQL/Redis/nativos propios, sin carga ni proveedor real. Native-source /tmp/web-modelos-librdb-v2.4.0, timeout900s. Fuentes de aplicación sin corregir y selección congeladas desde lanzamiento hasta resultado terminal. El runner notificará por Telegram después de limpieza; sin wrapper duplicado. No es prueba previsiblemente de horas y no requiere pausar el objetivo.

La reproducción se evalúa sólo tras comprobar que el control válido llega a inspección y que los intercalados son reales. Un fallo de fixture, infraestructura, timeout o fuentes cambiadas no confirma defecto. Conservar negativos; corregir sólo tras evidencia y repetir el alcance afectado. Prerregistro y huellas en artifacts/beta-promotion-fix-20261020/b00-340-preregister.json. Antes de congelar se refresca AST de la prueba nueva y semántica de este documento/encabezado17; se retienen las76Meta y once referencias corregidas, sin AST/semántica globales.

## Conciliación contractual

La revisión completa del corpus capturado queda en [298](298-conciliacion-nodos-corpus-capturado-b00-20261024.md),295disposiciones y cero lecturas pendientes capturadas, con originales/cuerpos ausentes explicitados. B00 sigue requiriendo conciliar AD01–AD11 con contrato, DAFO y actas actuales. Se prepara contraste independiente de esa matriz sin ejecutar pruebas ni cambiar producto. Nueve de18puntos beta cerrados; B15 opcional; apertura y G01–G08 separados.

## Reproducción terminal y corrección

Runner20261024-042112-f97c14c6 terminó con etiqueta ERROR por pytest no conforme:1PASS/4FAIL/0ERROR/0SKIP en cinco casos. El control válido inspecciona/audita cobertura; las cuatro revocaciones deniegan resultado y no confirman acción, pero el observador demuestra un descifrado del cuerpo tras la espera. Los fallos son exactamente las cuatro aserciones de descifrado, no errores de fixture o bloqueos sin observar. Fuentes invariables, PostgreSQL/Redis propios retirados, temporal ausente y Telegram terminal enviado. Auditoría b00-340-reproduction-audit.json conserva límites y hashes; no se interpreta como entrega externa de contenido.

Se añade authorize_reviewer(user,case) al final de context, después del bloqueo y validación de fila/prueba, antes de crear auditoría y descifrar. Devuelve el actor fresco y conserva las comprobaciones finales. La aplicación cambia sólo en ese punto; no modifica permisos, estados, cifrado, contratos, plazos o aceptación histórica.

Regresión preregistrada: archivo nuevo completo(5casos), test_audited_coverage_preserves_open_request_and_rejects_stale_replay(4variantes), localización de revisión de cobertura(4) y respuesta móvil(12),25casos esperados con tres workers, bases/medios/broker propios por worker, timeout1200s. Cubre control/revocación, revisión independiente, replay, consumo, HTTP/CSRF, cuenta/perfil, ES–EN y navegador. No ejecuta toda la suite de derechos ni capacidad; B16 conserva candidata común. Sources frozen desde lanzamiento hasta terminal, resultado exigido25PASS/0FAIL/0ERROR/0SKIP, limpieza e integridad verificadas y aviso Telegram único del runner.

## Resultado terminal de la regresión

Regresión20261024-042842-acce5865:25PASS/0FAIL/0ERROR/0SKIP, tres workers y los cuatro selectores exactos. Se verificaron cinco casos nuevos, revisión/consumo/replay/HTTP/CSRF, cuenta/perfil y navegador ES–EN. Fuentes iguales al prerregistro, servicios/temporal/procesos propios retirados y Telegram enviado. [Auditoría](evidencias/b00-coverage-authority-regression-20261024.json). Se acepta esta corrección local, conservando los cuatro fallos anteriores como negativos. La conciliación B00se cierra por [acta17](actas/17-beta-b00-aceptacion-local-20261024.md), sin aceptación global de autoridad en toda ruta privada.
