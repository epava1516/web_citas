# Revisión independiente de información de acceso

Estado: implementación parcial de servicio, interfaz e inventarios; aceptación conjunta pendiente de regresión97746. Continúa docs73 y CR09; generación y cierre siguen pendientes y el contrato completo mantiene su alcance.

## Autoridad y consulta

Aplicar el patrón existente de processing_review: bloqueos canónicos del expediente/persona/anuncio, usuario recién consultado, sesión/MFA originales, permisos de consulta/ejecución y permiso específico de revisión, exclusión por conflicto de interés. El segundo revisor no necesita reemplazar al responsable asignado; no puede ser el autor del borrador. Debe haber consultado las páginas vigentes del expediente y sus respuestas mediante los accesos auditados existentes. Ningún GET entrega cuerpo ni motivo del borrador.

Crear consulta persistente ligada a borrador, acción auditada, segundo revisor, versión del expediente, prueba, fuente, huella del ciphertext y política documental/huella. Registrar antes de descifrar. Validar también la firma original del guardado usando la autoridad y versiones originales como evidencia, sin exigir que el segundo revisor suplante al autor ni reutilice su sesión. La autoridad actual del segundo revisor se comprueba antes de entregar; la del autor no se convierte en autorización del lector.

## Decisión

Modelo de decisión independiente con FK PROTECT a borrador y consulta, acción auditada, resultado approved/rejected, motivo cifrado y las mismas referencias/huellas. Una decisión por versión inmutable de borrador; replay exacto no añade lecturas ni decisiones. Claves incompatibles o cambios de fuente/prueba/política/cuerpo/versión devuelven conflicto controlado. Una consulta antigua no permite aprobar un borrador nuevo. El propio autor recibe403 incluso si tiene todos los permisos.

Aprobar requiere diez apartados revisados, textos con procedencia explícita y política vinculada verificable; cualquier pendiente impide aprobación. Para portabilidad, la aprobación integral requiere además evaluación propia por conjunto de datos, base y origen revisados, automatización y protección de terceros. Mientras no exista esa evaluación, solo se admite rechazo o consulta; no equiparar aprobar información de acceso con aprobar portabilidad.

La aprobación de este documento es operativa, no revisión jurídica de la política ni resolución del expediente. No incrementa estado/versión del caso, consume prueba ni permite cerrar por sí sola. Generación/descarga/respuesta final deberán exigir decisión vigente y conservar vínculo exacto; esa integración sigue pendiente.

## Interfaz y pruebas

Ruta privada de revisión por expediente/borrador, GET vacío y POST inspect/review con CSRF, key UUID, versión, motivo y resultado. ES/EN, errores400/403/409, no-store/noindex, cuerpos y motivos sensibles. Después de decidir solo metadatos; recarga idempotente y GET limpio.

Verificar aprobación completa y rechazo, autor denegado, falta de lectura, permiso revocado, tercero/gestor excluido, pendiente bloqueado, política ausente/cambiada, ciphertext corrupto, prueba caducada/purgada, replay y carreras con espera PostgreSQL observada. Probar cuenta/perfil/representado, móvil y ambos idiomas. Añadir dependencias a inventarios y censo; su conservación sigue a la finalidad auditada, sin prometer borrado de backups.


## Evidencia del guardado original implementada en0080

Extraer la validación de firma del guardado a una función de evidencia separada de record. Su entrada debe contener el borrador bloqueado, la fuente/prueba actuales y el cuerpo descifrado tras auditoría. Comprobar request/actor/action/proof, operation copy_info_save, versión y firma original; recuperar versiones de sesión/MFA de evidencia persistente, no del usuario que revisa. Los borradores actuales no almacenan esas versiones fuera de la firma: antes de implementar el segundo revisor se necesitan campos de evidencia para nuevas versiones, con migración sin inventar valores para registros antiguos. Los antiguos quedan consultables por su autor según el flujo existente, pero no deben aprobarse independientemente con valores supuestos.

El contrato de migración requiere compatibilidad temporal con0079 y despliegue de app/worker/Beat coordinado. Inventarios detectarán los nuevos campos sin proyectar motivos ni contenido. La caducidad de la consulta nunca supera borrador/prueba; una aprobación histórica no revive contenido purgado. No usar approved como sustituto del gate completo de respuesta final.

d857348 push confirmado, remoto master exacto. Backend de evidencia original0080 iniciado: session/MFA originales nullable, nuevas versiones guardan valores reales de su autor, sin backfill histórico. validate_saved_evidence exige transacción y valida request/actor/action/version/proof/source/caducidad/purga/esquema/firma/política usando evidencia original; no autoriza acceso ni descifra cuerpo por sí mismo. Inventarios incluyen campos.7187 batería borradores/evidencia original activa /tmp/information-original-evidence.xml/log: alteraciones sesión/MFA y datos históricos desconocidos deben rechazarse; cambio de sesión actual no altera validez criptográfica de evidencia histórica ni habilita acceso. Fuente congelada hasta terminal. Runtime0080/formulario segundo revisor/permiso específico/consulta auditada/decisión/generación/cierre pendientes.


## Persistencia de segunda revisión implementada

RightsCopyInformationRead: acción OneToOne, borrador FK PROTECT, prueba FK PROTECT, source_digest, information_digest (HMAC del ciphertext), policy_digest, created_at. El actor, propósito cifrado y versión del expediente proceden de la acción. No conservar una segunda copia del contenido privado en la lectura.

RightsCopyInformationReview: acción OneToOne, borrador OneToOne PROTECT, consulta FK PROTECT, prueba FK PROTECT, las tres huellas, resultado approved/rejected y fecha. Permiso review_copy_information propio; constraint del resultado y relación única por borrador. Toda decisión requiere consulta del mismo revisor/expediente/versión/huellas vigente. Motivo cifrado en RightsAction; consultas y decisiones son operaciones distintas y claves globales incompatibles se rechazan.

Estas relaciones son evidencia dependiente del sujeto del borrador: añadirlas a inventarios de perfil y cuenta con exclusión del procedimiento actual, actualizar censo y probar filas presentes. No resolver su conservación por borrado en cascada ni exponer contenido a través del inventario.

7187 terminal0:13 correctas99,53s PostgreSQL, /tmp/information-original-evidence.xml. Evidencia original nueva recuperable y alteraciones/null históricos rechazados; sesión actual del autor no sustituye evidencia histórica. Modelos Read/Review añadidos con PROTECT, decisión OneToOne, permiso propio y resultado constrained; migración en generación. Servicio/interfaz/inventarios/pruebas de revisión aún pendientes, no segunda revisión habilitada.

43502 migración0081 generada terminal0. Servicio rights_information_review.record implementado inicial: autoridad fresca/permiso propio/COI/lecturas caso-respuestas, autor excluido, audit antes de descifrar, evidencia original/prueba/fuente/política actuales, consulta previa propia, aprobación solo access sin pendientes y política vinculada, decisión única/replay controlado/final revalidación. No cierre ni consumo de prueba.42857 primeras2 pruebas aprobación/rechazo/replay/self denial activas /tmp/information-independent-review.xml/log; fuente congelada hasta terminal. Modelos aún no incorporados a inventarios/censo; HTTP/móvil/carreras/purga/runtime0080–81/regresión y generación/cierre pendientes.

42857 terminal0:2 primeras correctas39,37s PostgreSQL, /tmp/information-independent-review.xml: aprobación completa/rechazo pending, autor403, lectura previa requerida y replay sin duplicados/caso abierto. Inventarios Read/Review incorporados: perfil por information.request.person, cuenta por sujeto explícito o perfil del titular excluyendo procedimiento actual; huellas incluyen referencias/acción/motivo cifrado sin descifrar. Censo49.77078 ampliación revisión/inventario/censo activa /tmp/information-review-inventory.xml/log; fuente congelada. Aislamiento no vacío de cuenta/autoridad revocada/corrupción/carreras/HTTP/móvil/runtime/regresión/generación/cierre pendientes.

77078 terminal0:3 correctas48,09s PostgreSQL, /tmp/information-review-inventory.xml. Perfil Read/Review presentes y opacos, censo49; cuenta no vacía aún pendiente. Ruta privada /<idioma>/moderation/rights/<case_id>/information/<information_id>/review/ conectada GET sin cuerpo/POST inspect-review, CSRF/no-store/noindex y errores400/403/409; autor excluido también en GET. Batería ampliada HTTP ESEN en ejecución /tmp/information-review-http.xml/log; fuente congelada. Descubrimiento desde cola/etiquetas campos/móvil/carreras/cuenta/runtime/regresión/generación/cierre pendientes.

32634 terminal0:2 HTTP correctas40,32s PostgreSQL, /tmp/information-review-http.xml. POST inspect/replay/GET limpio y permiso revocado403. Descubrimiento desde rights_inspect implementado: permiso/autoridad propios, excluye autor/purgados/caducados, referencias/versión/fecha solamente, paginación50; enlaces al revisor y labels humanos ESEN en cuerpo auditado.68525 batería descubrimiento activa /tmp/information-review-discovery.xml/log; fuente congelada. Móvil/volumen real/cuenta/corrupción/carreras/runtime/regresión/generación/cierre pendientes.

68525 terminal0:2 correctas38,66s PostgreSQL, /tmp/information-review-discovery.xml. Links de expediente/reference-version y GET sin cuerpo verificados; labels humanos renderizados.66748 ampliación auditoría/corrupción/prueba revocada activa /tmp/information-review-audit-corruption.xml/log; monkeypatch exige acción inspect antes de descifrar, corrupción/proof fallidos deben409 sin acciones parciales. Fuente congelada hasta terminal. Móvil/cuenta/carreras/runtime/regresión/generación/cierre pendientes.

66748 terminal0:2 correctas41,84s PostgreSQL, /tmp/information-review-audit-corruption.xml. Auditoría inspect existe antes de descifrar; corrupción y prueba revocada409 sin acciones parciales.16167 build terminal0;66884 migración Docker terminal0;51848 recreación en curso.49888 ampliación4 casos perfil/cuenta access-portability/inventario no vacío activa /tmp/information-review-account-scope.xml/log; fuente congelada. Clones solo prueban inventario, no workflows aceptados. Móvil/carreras/runtimecheck/regresión/generación/cierre pendientes.

49888 terminal0:4 correctas54,05s PostgreSQL, /tmp/information-review-account-scope.xml. Cuenta access/portability: pending bloquea aprobación, consulta/rechazo propios y aislamiento inventario no vacío (procedimiento actual/otro titular excluidos, evidencia propia previa incluida, cambio de motivo opaco detectado).10594 check/migraciones/health terminal0; runtime10 hashes host/app/worker/Beat/UID10001, copia-revision-independiente-runtime.json.31003 móviles segundo revisor ESEN activas /tmp/information-independent-mobile.xml/log; loginMFA real→consultar caso→link borrador→inspect→aprobar→replay, fuente congelada. Ruff del test nuevo detecta E402 ubicación constante REASON, corregir tras terminal. Carreras/regresión/generación/cierre pendientes.

31003 terminal0:2 móviles ESEN correctas44,74s PostgreSQL/Chromium, /tmp/information-independent-mobile.xml; login/MFA→caso→link→inspect→aprobar→recarga sin duplicado, caso abierto y sin overflow. E402 corregido tras terminal, Ruff/formato test nuevo correctos. Contrato10 actualizado.30177 carreras decisión activas8 casos /tmp/information-independent-races.xml/log: tres PIDs/espera de caso observada, replay/conflicto/permiso/prueba/sesión/MFA/fuente/política. Fuente congelada hasta terminal. Regresión conjunta/purga-pendiente/histórico/cobertura completa/generación/cierre pendientes.


## Condición para consumir una aprobación

La futura generación debe validar también la relación de consulta almacenada en la decisión: mismo borrador, revisor independiente, prueba, versión y huellas. No basta con encontrar outcome=approved. Comprobar la firma de ambas acciones, vigencia del cuerpo/prueba/política y que el borrador seleccionado sea la versión vigente aplicable; una decisión histórica no sustituye la revisión de una versión nueva. Revalidar al generar y descargar, con rollback ante cambios. Esta condición no está implementada por el actual servicio de registro, que no genera respuestas.

Las comprobaciones actuales de interfaz no prueban volumen grande ni todas las variantes históricas/purga. Añadir pruebas de purga y datos originales desconocidos en la segunda revisión antes de aceptar entrega; la verificación directa del helper de evidencia no sustituye su recorrido HTTP completo.

30177 terminal0:8 carreras correctas74,86s PostgreSQL, /tmp/information-independent-races.xml. Replay una decisión, claves distintas un ganador, cambios permiso/prueba/sesión/MFA/fuente/política deniegan ambas sin acciones parciales tras espera observada/tres PIDs. Añadidos HTTP de histórico sin evidencia y purga; batería afectada activa /tmp/information-review-purged-historical.xml/log. Fuente congelada; regresión conjunta/generación/cierre pendientes.

95241 terminal0:4 correctas53,86s PostgreSQL, /tmp/information-review-purged-historical.xml. Histórico con sesión original desconocida y purga rechazan HTTP409 sin acciones parciales, manteniendo cuenta/perfil/portability checks. Regresión conjunta ampliada activa /tmp/information-independent-final-common.xml/log; fuente congelada hasta terminal. CI d857348 run37345461749/job111882791907 terminalfailure sin pasos; anotación confirma pagos recientes fallidos o límite insuficiente. No pruebas CI ejecutadas, no fallo funcional acreditado; no modificar facturación/contratar runners.


## Estado de entrega

Modelos0080–81, servicio, ruta privada y enlaces desde expediente están implementados localmente. Verificación por partes: perfil/cuenta, aprobación/rechazo/replay, autor excluido, GET limpio, corrupción/prueba revocada/purga/evidencia histórica desconocida; móvil ESEN y ocho carreras de decisión con espera PostgreSQL observada. Runtime0081 con diez hashes host/app/worker/Beat idénticos/UID10001/check/migraciones/health. No sumar resultados separados como batería común:97746 sigue en ejecución y su XML final aún no existe.

No acreditar con este bloque acceso integral, elegibilidad de portabilidad, respuesta final, memoria acotada, conservación/restauración ni producción. La integración de exportación se define en docs75 y todavía no está implementada.

97746 terminal0:90 conjuntas correctas600,27s PostgreSQL/Chromium; XML90/0fallos/0errores/0skips. Política/borradores/revisión independiente/perfil-cuenta/carreras/móviles/inventarios/exports/compilación/mensajes/respuestas incluidos. Evidencia copia-revision-independiente-regresion.json, runtime0081 con10 hashes/UID10001/check/migraciones/health ok. Fuente descongelada; entrega parcial lista para commit/push. No aceptación integral CR09; siguiente docs75 generación/descarga con vínculo revisado, portabilidad y respuestas/cierres pendientes.
