# Vinculación de derechos a un perfil sin anuncio

Estado: vínculo y rectificación de nombres sin anuncio verificados localmente;45 pruebas conjuntas, móvil ESEN y Docker en sus alcances documentados. CR-09 sigue abierto. Complementa docs/49 y contratos de derechos. Vincular una referencia no acredita identidad ni autoriza una corrección.

El formulario privado de acciones admite `link_person_id` para operación `link`, destinado a una persona existente sin anuncio. No crea perfiles/cuentas ni asigna un sujeto automáticamente. Conserva lectura auditada vigente, responsable asignado, MFA, permiso de revisión, versión, motivo privado e idempotencia. Estampa sujeto, gestor y versión de gestión bajo locks canónicos Agency→Person→RightsRequest.

No admite persona y anuncio simultáneos. Si la persona tiene anuncio, exige la referencia de anuncio para conservar su historia editorial y controles existentes. Revalida existencia del anuncio después de bloquear Person. No permite sustituir una referencia ya vinculada; conflictos del gestor, sujeto o equipo actual/histórico siguen denegados. El caso permanece sin prueba de identidad y sin revisión editorial de referencia cuando no hay anuncio.

El nuevo campo participa en el digest de acción cuando se utiliza; las solicitudes antiguas sin campo conservan su digest. No hay migración. No se expone selector ni cuenta en el acuse público.

Pendientes: pruebas PostgreSQL/SSR de vínculo, carreras de creación de anuncio y cambio de gestión durante espera; recorrido de rectificación con comprobación proporcionada, propuestas/revisión/comunicación/recepción/ejecución sobre persona sin anuncio; móvil ES/EN, inventario/exportación, Docker y regresión común. Esto no cubre por sí solo derechos de una cuenta sin ningún perfil.


## Evidencia inicial

Batería39353:15 correctas102,35s PostgreSQL/Chromium, sin errores/fallos/omisiones; vínculo sin anuncio/CSRF/replay/COI y vínculos/asignación anteriores. Repetición10471:2 correctas/1 fallida32,94s por preparación de revisión publicada inexistente, no fallo de producción. Ajustada preparación para omitir relaciones editoriales cuando no existe anuncio; nueva batería53918 de6 casos en curso, incluye ejecución de particular/agencia y carreras de gestor/anuncio tras espera real. Identidad sigue simulada.


53918 terminal0:6 correctas49,49s PostgreSQL, sin errores/fallos/omisiones. Vínculo sin anuncio y rectificación de nombres particular/agencia aprobada/comunicada/recibida con comprobación fresca aplica sin crear anuncio ni revisión; conserva correo y session_version. Cambio manager_version o creación de Listing durante espera Person observada deniega vínculo sin acción/versión cambiadas. Identidad sigue simulada. Cuenta sin ningún perfil, SSR móvil ESEN, runtime/CI y resto CR09/contrato pendientes.


Docker vínculo sin anuncio: build85920/recreate12447 terminal0. Check limpio, migrate--check sin pendientes/sin migración nueva, UID10001 y Caddy health200. Hashes rights_scope/rights_actions/rights iguales host/app/worker/Beat; evidencia normalizada. Ruff/diff limpios. Batería conjunta32502 sigue activa, fuente congelada; no commit ni aceptación común antes de terminal. CI6972785 run37246617009 in_progress confirmada, anterior a estos cambios. SSR móvil ESEN y demás CR09/contrato siguen pendientes.


32502 terminal0:45 correctas431,58s PostgreSQL/Chromium, cero fallos/errores/omisiones. Vínculos/asignación/cuenta/destino/carreras/revisión pasan conjuntamente sobre cambios actuales; runtime/hash ya comprobados. Añadidas pruebas móviles Chromium ESEN login+MFA→vínculo SSR de perfil sin anuncio→resultado visible→reload y persistencia, XML /tmp/rights-person-linking-mobile.xml en curso. Solo ampliación de pruebas, fuente funcional sin cambios. No sumar baterías ni aceptar móvil antes de terminal.


87211 terminal0:2 móviles correctas33,86s (6 excluidas), Chromium390x844 ESEN. Login/MFA reales→vínculo de persona sin anuncio por formulario SSR→resultado observado→reload/persistencia; sin overflow, una acción, sin revisión referenciada y ámbito unverified. No sumar a45 conjuntas como suite47; no altera fuente funcional ya comprobada en Docker. Sin pytest activo. Permanece pendiente recorrido integral de cuenta móvil, derechos de cuenta sin ningún perfil y resto CR09/contrato; CI6972785 aún in_progress.
