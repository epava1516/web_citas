# Contactos registrados de la propia cuenta en copias privadas

Estado: entrega técnica parcial verificada localmente con69 pruebas conjuntas y Docker. CR-09 permanece abierto; no acredita alcance integral de acceso/portabilidad.

Las proyecciones de perfil y cuenta incorporan account_activity.personal_contacts mediante una función común. Selección estricta PhoneClaim.individual=cuenta del titular y agency=null; el gestor, editor o solicitante nunca sustituyen al sujeto del perfil. Un teléfono de agencia no se incluye como teléfono propio aunque figure en un anuncio.

Cada fila contiene phone, verified_at, verification_procedure y scope=account_owned_claim. Una atribución a la cuenta no equivale a teléfono personal comprobado: verified_at=null permanece visible como pendiente. No se incluyen retos, códigos, credenciales, tokens ni identificadores de otras personas. No se deduce pertenencia por coincidencia con un contacto publicado.

La sección personal_contacts participa en inspección, decisiones cifradas versionadas y compilación completa por páginas. Permite conservar el teléfono original o vaciarlo; nunca reemplazarlo por otro, añadir filas o modificar estado/procedimiento de verificación. La redacción afecta únicamente a la copia, no al registro original. La huella de fuente contiene esta proyección, por lo que deriva de contactos invalida decisiones anteriores.

Verificación84227 activa /tmp/copy-personal-contacts.xml/log: dos variantes de perfil/cuenta, contactos propios verificados y pendientes, exclusión de gestor/agencia, rechazo de inyección, generación desde decisiones con teléfonos redactados, regresión de aislamiento de copia. Fuente congelada hasta terminal. Docker todavía2a4c4f9 sin esta ampliación.

Pendiente: variantes de fuente/replay/caducidad, edición móvil de esta sección, regresión conjunta y runtime. Invitaciones/membresías/historial de cuenta, otras evidencias, información adicional y distinción acceso/portabilidad siguen pendientes; incluir contactos no completa el derecho ni el contrato.

84227 terminal0:13 correctas105,98s PostgreSQL,2 warnings xunit2 históricos de propiedades; /tmp/copy-personal-contacts.xml.36386 terminal0:3 correctas47,25s /tmp/copy-personal-contacts-source.xml, confirma aislamiento perfil/cuenta, redacción entregada y cambio de verificación invalida lectura previa sin decisión. Baterías separadas, no sumar como suite única16. Ruff/diff limpios; fuente descongelada, runtime aún2a4c4f9 y regresión conjunta/entrega pendientes.

18608 terminal0:2 móviles ESEN correctas47,29s PostgreSQL/Chromium, /tmp/copy-personal-contacts-mobile.xml. Login/MFA real→consultar personal_contacts→redactar teléfonos por formulario→guardar→GET limpio→generate_pages sin cuerpo copy→descarga anónima sin teléfonos, original intacto.77370 regresión conjunta activa /tmp/copy-personal-contacts-final-common.xml/log, fuente congelada hasta terminal; recuperar mismo handle y no reiniciar por timeout.71562 build Docker en curso.

71562 build terminal0;82520 recreación app/worker/Beat terminal0;41000 check/migrate-check/makemigrations/health200 terminal0. Cinco fuentes host/app/worker/Beat idénticas, UID10001; evidencia copia-contactos-propios-runtime.json. Sin migraciones nuevas.77370 continúa activa confirmada por polling; recuperar mismo handle, /tmp/copy-personal-contacts-final-common.xml/log. No editar fuente ni aceptar batería/commit hasta terminal.

77370 terminal0:69 conjuntas correctas527,85s PostgreSQL/Chromium, XML contrastado69/0fallos/0errores/0skips;2 warnings históricos record_property/xunit2. Evidencia copia-contactos-propios-regresion.json. Aislamiento/contactos/compilación/generación/carreras/móvil/decisiones/inspección/exports/cuenta incluidos. Fuente descongelada, sin proceso local activo; Docker actual con5 hashes iguales app/worker/Beat, UID10001/check/migraciones/health200. Entrega técnica parcial lista para commit/push; CR09 integral pendiente. Siguiente docs72 relaciones de cuenta. CI2a4c4f9/run37331808322/job111836511100 terminal failure antes de pasos por facturación/límite GitHub; sin pruebas CI ejecutadas.
