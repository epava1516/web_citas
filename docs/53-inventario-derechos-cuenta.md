# Inventario de derechos de cuenta por finalidad

Estado: especificación con implementación parcial; aceptación integral pendiente. Copia propia en docs/54 e inventario/planes/ejecución en verificación en docs/55. Complementa docs/51 y la matriz CR-09; no sustituye revisión jurídica ni aprueba conservación definitiva.

## Regla de ámbito

Una cuenta propia se identifica exclusivamente por RightsRequest.account_subject comprobado. Ser propietario, editor o moderador no convierte los datos de los modelos, miembros, denunciantes o solicitantes en datos exportables de esa cuenta. Una FK con el usuario como actor prueba una intervención, no titularidad de todo el registro.

El inventario debe identificar recurso, finalidad, campos propios, relaciones ajenas, base de conservación registrada, responsable de revisión, estado y operación posible. No confundir inventario interno de conservación con copia descargable. El digest vincula fuente y decisión; la copia usa una proyección explícita y revisada, nunca model.values() indiscriminado.

## Fuentes y tratamiento técnico requerido

| Fuente | Finalidad operativa | Información propia candidata | Límites de copia y ejecución |
| --- | --- | --- | --- |
| User | Cuenta y acceso | Nombre/apellidos, correo, username, fechas, rol y estado de acceso | No proyectar hash de contraseña, secreto MFA, contador TOTP, credenciales o permisos internos; rectificación limitada a campos acordados |
| LegalAcceptance/LegalDocument | Evidencia de aceptación | Documento, versión, idioma, acción y fecha de aceptación del propio usuario | No inferir consentimiento de otra persona; conservar referencia documental con decisión de finalidad |
| Favorite | Preferencias privadas | Referencia pública del anuncio y fecha de favorito propios | No copiar contenido privado o retirado del anunciante; supresión de preferencia no elimina anuncio |
| AccountToken/RecoveryCode | Seguridad y recuperación | Inventario interno de existencia/estado/caducidad minimizado | Ningún digest, código, secreto o enlace en copia; ejecución invalida mecanismos con evidencia de operación |
| Agency/AgencyMember/AgencyInvitation | Gestión de organización | Relación propia, rol/estado y fechas pertinentes | No copiar miembros, modelos, destinatarios de invitaciones o evidencia de organización completa por ser dueño; transferencia de propiedad exige su propio procedimiento |
| RightsRequest y sus acciones/pruebas/respuestas | Tramitación de derechos | Solicitud propia, actuaciones/respuestas destinadas al sujeto y fechas | Casos por account_subject comprobado o solicitante propio se revisan por separado; anonimato y datos de revisores/terceros minimizados; motivos internos no publicados automáticamente |
| Report/Complaint/Appeal | Moderación y reclamación | Intervención propia cuando identificada y revisión humana autoriza acceso | No revelar identidad de otros intervinientes o todo expediente; no enlazar denuncias anónimas por coincidencia de texto/contacto |
| RepresentationAction/VerificationCheck y gestión editorial | Representación y publicación | Intervenciones atribuibles a la cuenta cuando proceda | Ausencia de Person no autoriza asumir sujeto de modelo; separar historia del gestor y datos del modelo, sin autoridad editorial desde ámbito de cuenta |
| Sesiones, tareas y registros operativos | Operación y seguridad | Inventario de categorías/estado y datos atribuibles con fuente verificable | No afirmar que existe atribución cuando sesión/log solo guarda dato opaco; no exponer tokens ni entradas compartidas; integrar política de backups/WAL/restauración |

## Recorrido de copia

1. Consulta completa/auditada del expediente y comprobación independiente vigente.
2. Fuente bloqueada con User y expediente en el orden del ámbito de cuenta; escritores de aceptaciones/favoritos deben cooperar o tener una estampa que detecte cambios.
3. Proyección propia de cuenta, aceptaciones y favoritos; otras categorías se enumeran como pendientes de revisión hasta conectarlas. La descarga sigue marcada parcial si falta información pertinente.
4. Revisión de redacción sin permitir insertar identidad de otra cuenta o relaciones adicionales. Acceso y portabilidad conservan tipos distintos; una copia JSON no acredita por sí sola portabilidad íntegra.
5. Snapshot cifrado con ámbito de cuenta explícito, canal, versión, expiración y auditoría de descargas. Revalidar ámbito/estado antes de entregar y después de cualquier espera de locks.
6. Purga caducada mediante worker/Beat real, con evidencia de contenido no vacío; copias de seguridad y conservación quedan en su política propia.

## Recorrido de conservación y supresión

Decidir y ejecutar por finalidad/recurso. El tombstone de cuenta no puede borrar ni reasignar modelos por una cascada lateral. Si hay propiedad de agencia, obligaciones o evidencia protegida, registrar restricción/conservación y procedimiento pendiente de propiedad, sin afirmar supresión completa. Retirar identificadores de acceso y datos ejecutables debe preservar un registro minimizado de la actuación, sus decisiones y sus límites.

Limitación/oposición de cuenta requiere una operación propia y verificable sobre las finalidades afectadas; pausar publicación de un Person no cubre una cuenta sin perfil. El acceso al acuse/canal de derechos debe continuar conforme al procedimiento incluso tras desactivar acceso ordinario. Restauraciones y reintentos no deben resucitar datos suprimidos ni reactivar tratamientos restringidos.

## Evidencia requerida

Pruebas PostgreSQL de fuente modificada mientras espera User, preferencias/aceptaciones concurrentes, cuenta ajena, ámbito perfil frente a cuenta, propietario de agencia y claves repetidas; navegador ES/EN/móvil; descarga/purga real con datos sintéticos; Docker y CI del mismo commit. Aceptación final requiere consumidores e inventario completo por finalidad, ejecución y respuesta final: este diseño no los da por terminados.

## Auditoría de consumidores durante regresión

La admisión de proof de cuenta requiere distinguir consumidores generales y exclusivos de perfil. privacy_holds.hold, rectification_uploads y los inventarios/planes de supresión/publicación aún dereferencian Person después de authorized_proof. Antes de aceptar esta entrega, añadir rechazo explícito de ámbito incompatible y pruebas negativas; después conectar los consumidores propios de cuenta. No tratar el rechazo temporal de una operación editorial como ejecución de limitación/supresión de cuenta. Fuente congelada durante batería60099; observación de código, todavía sin corrección aplicada.


Guardas aplicadas y negativos verificados tras terminal de regresión38: consumidores exclusivos de perfil usan locked_profile_case; cuenta no accede a operaciones editoriales ni a copia de perfil. Ver docs51 para resultados y limitaciones. Inventario propio y ejecución por finalidad siguen pendientes, no cubiertos por estas guardas.
