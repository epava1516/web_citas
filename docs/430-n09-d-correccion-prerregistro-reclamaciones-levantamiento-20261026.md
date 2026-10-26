# N09D — corrección prerregistrada de reclamaciones y levantamiento

Plan anterior al cambio de aplicación. Base `f65a530`; diagnóstico [429](429-n09-d-prerregistro-reclamaciones-levantamiento-20261026.md). N09 sigue abierto: 139 IDs, 8/13 bloques obligatorios aceptados. Las baterías válidas de N09A/B/C no se repiten por esta corrección ni por instalar herramientas.

## Evidencia original preservada

Run `20261026-062847-a8dd3f53`: **6 FAIL, 87,487 s JUnit**, cero ERROR/SKIP, 1.767 huellas estables, limpieza y Telegram comprobados. Auditoría independiente `artifacts/recorridos-n09-d-20261026/baseline-audit.json`: seis esperas PostgreSQL observadas con PID bloqueante propio, revocación confirmada antes de liberar, hilos/conexiones cerrados. Seis defectos de aplicación confirmados, sin cambiar sus oráculos para aceptar el resultado.

| Operación | Resultado después de revocar | Petición con espera inducida |
| --- | --- | ---: |
| Inspección de reclamación |200; nueva auditoría de acceso|223,083 ms|
| Foto de revisión enlazada, GET real |200; 10.314 bytes de imagen y nueva auditoría|121,502 ms|
| Asignación de reclamación |302; expediente y acción modificados|111,182 ms|
| Resolución sobre anuncio rechazado |302; expediente, acción, resolución, aviso, anuncio y revisión modificados|646,690 ms|
| Propuesta de levantamiento |302; propuesta, respuesta, aviso, acción y expediente modificados|471,644 ms|
| Ejecución de levantamiento |302; medida desactivada y propuesta, acción, anuncio y expediente modificados|446,458 ms|

No son latencias normales ni mediciones de capacidad. La imagen local sintética fue consumida con límite de 1 MiB y cerrada; se conserva longitud/hash, sin contenido ni ruta física. Los dos levantamientos ejercitan realmente `restriction` y el simulador, sin identidad ni proveedor reales. El fixture original `prepared(kind)` fija internamente restriction: sus etiquetas no acreditan tres tipos distintos. Se conserva ese fixture y se documenta el límite; no se modifica retrospectivamente evidencia válida.

## Candidato acotado

Cinco archivos de aplicación: nuevo `apps/safety/complaint_authority.py` y cambios en `complaints.py`, `complaint_actions.py`, `complaint_resolutions.py`, `privacy_release.py`. Sin modelos, migraciones, configuración, servicios, proveedores, CI ni cambios al contrato. El helper de reclamaciones evita duplicar sus reglas entre vistas y servicios; el de levantamiento mantiene sus cuatro permisos propios.

Capturar una vez los epochs session_version/mfa_version originales; consultar un User nuevo en admisión y después de los locks canónicos, antes de leer contenido privado, abrir archivos, aceptar replay o escribir. Exigir existencia, cuenta activa/no borrada, MFA y epochs originales, permiso base y extras de operación actuales. En las dos vistas afectadas comprobar además account_version/mfa_version de sesión y usar request.user fresco; fuente sin permiso no se muestra, pero un revisor de intake conserva su acceso legítimo al intake. No exigir privilegios de fuente ajenos al comportamiento actual.

Servicios: act requiere review_complaint, además manage_complaint_assignment para unassign y resolve_complaint para reassess; su source_permission dinámico se evalúa sobre el usuario fresco. resolve requiere review_complaint y resolve_complaint, mantiene source_permission y COI. Los helpers de reassessment no adquieren nuevos locks. La rama report puede invocar decisions.act con sus propios locks/guardas; no atribuir al diagnóstico de listing cobertura concurrente de esa rama. Propose/execute requieren review_rights_request, execute_rights_request, review_privacy_hold y respond_rights_request, con comprobación posterior al último lock Hold/Proposal/Hold y anterior a actor_check/replay/efectos. authorized_proof del consumidor no adquiere otro lock de proof.

Mantener orden de locks, bindings de expediente/persona/foto/fuente, independencia, lecturas auditadas, ACK y proof posterior, firma/cifrado, versiones, motivos, CSRF y semántica de replay autorizado. Sin lock del operador ni promesa de serialización universal tras la última lectura; las consultas adicionales son coste de seguridad, sin mejora de rendimiento atribuida.

## Selección prevista antes de congelar

- Los seis diagnósticos originales de 429, sin editar instrumentos ni helper compartido de 419.
- Nuevo instrumento de negativos con 44 entradas: inspect6, photo7, claim6, resolve7, propose9, execute9. Para todas: permiso base, cuenta inactiva/borrada, MFA deshabilitado, incremento de epoch de sesión y MFA; photo añade permiso review_listing, resolve añade resolve_complaint, y cada levantamiento añade los otros tres permisos. Usar actor/cache legítimos y mutaciones ORM externas, sin parchear autorizaciones. Vistas mediante RequestFactory y sesión legítima explícita, sin afirmar transporte/middleware/concurrencia; servicios mediante sus entradas públicas.
- Cuatro replays revocados de servicio: claim, resolve, propose y execute. Preparar primero una ejecución legítima, conservar su resultado como referencia, revocar permiso y exigir PermissionDenied con snapshots intactos al repetir la clave/payload originales. No basta que un replay no escriba.
- Regresión original completa en test_complaint_intake.py, test_complaint_assignment.py, test_complaint_linking.py, test_complaint_listing_linking.py, test_complaint_resolutions.py, test_complaint_messages.py, test_complaint_localization.py, test_complaint_resolution_localization.py y test_privacy_release.py. No editar esos módulos. Sus casos de fuente/COI/IDOR/lectura de imágenes, claves/versiones, concurrencia, idiomas/móvil y simulador son regresión funcional; distinguir interposición controlada y esperas reales.

Cerrar enumeración/número exacto de originales antes de freeze; 54 casos nuevos/diagnósticos más originales. Guard explícito, serial, no PRODUCTION, PostgreSQL/Redis propios desechables; runner oficial, notificación terminal tras limpieza, recibo verificado. Lint y revisión propia antes de refrescar AST/semántica, corte y congelación. Cualquier ajuste de selección previo se registra; no recortar una batería después de fallar.

Aplicar django-expert/reviewer, django-access-review, security-review y variant-analysis dentro de este alcance, incluyendo rutas autenticadas y permisos actuales después de esperas. Differential-review producirá revisión escrita del diff, callers e historia relevante; code-security aporta guías pertinentes, sin sustituir pruebas de autorización. Cinco skills ya anunciadas en el catálogo actualizado; MCP Semgrep no expuesto en este hilo. Versiones locales comprobadas: Semgrep1.182.1, Bandit1.9.4, pip-audit2.10.1 y Gitleaks8.30.1. No se ejecutaron escaneos por instalarlas. Instalación y cambios laterales permanecen fuera de commits de desarrollo.

Aceptación pendiente: selección completa válida, snapshots sin efectos en denegaciones, seis esperas reales403, regresiones autorizadas preservadas, tabla antes/después con tiempos y límites, grafo/evidencias/seguimiento actualizados. Este documento no acepta el candidato ni cierra N09, N02, N10 o N15. Alpha, sin apertura.

Enumeración estática anterior a freeze: originales63 (intake13, assignment5, linking5, listing_linking6, resolutions10, messages13, localization2, resolution_localization2, privacy_release7). Total previsto **117 = 6 esperas + 44 entradas negativas + 4 replays + 63 originales**; confirmar colección efectiva al ejecutar, sin omitir casos. El negativo de permiso base de levantamiento es review_rights_request y sus otros tres permisos son execute_rights_request/review_privacy_hold/respond_rights_request.
