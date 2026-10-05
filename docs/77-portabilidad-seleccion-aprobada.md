# Selección granular aprobada de portabilidad

Estado: diseño de integración; implementación y aceptación pendientes. Complementa docs76 y mantiene abiertos CR09 y el contrato completo.

## Persistencia y vínculos

La selección será un borrador cifrado independiente de la evaluación por conjuntos. Referenciará solicitud, autor, acción auditada, prueba, evaluación y aprobación concreta de esa evaluación. Conservará huellas de fuente, evaluación, consulta y decisión, versiones originales de sesión/MFA, versión propia, caducidad y fecha de purga. Las claves foráneas serán PROTECT; la versión será positiva y única por solicitud/autor. La expiración no superará la de la evaluación ni de la prueba. No almacenar valores seleccionados en metadatos o logs.

Cada entrada identifica conjunto, referencia HMAC de fila y caminos JSON Pointer escalares. La firma de guardado liga el selector completo, prueba, fuente, evaluación aprobada y versiones originales. Cambiar cualquier campo o referencia invalida la aprobación; un borrador posterior deja inutilizable la selección anterior para generación. No sustituir una firma inválida por una firma nueva durante un replay.

## Evaluación de elementos mixtos

La evaluación de conjuntos actualmente implementada no permite marcar mixed como eligible. Para portar parte de un conjunto mixto será necesaria evaluación por elemento/campo, con base, origen, automatización, relación con interesado, revisión de terceros, motivo y evidencia propios. Su revisión independiente debe aprobar esos hechos y la selección exacta. No basta aprobar el conjunto, ni una lista de campos elegida posteriormente por el cliente. No excluir automáticamente todos los elementos cuando solo algunos conciernen a terceros.

## Operaciones y autoridad

Guardar exige responsable asignado, permisos, MFA, ausencia de conflicto, consulta completa, prueba vigente y evaluación aprobada revalidada dentro de la misma transacción. La auditoría precede al descifrado. Se comprobarán fuente, prueba y autoridad de nuevo antes de confirmar. El guardado no cambia el estado del expediente ni consume la prueba ni crea exportación.

Consultar el borrador requiere POST auditado; GET muestra solo referencias y estados autorizados. Un revisor distinto del autor consulta la selección y la fuente pertinente antes de decidir. La decisión firmada liga el ID exacto de consulta, selección cifrada y resultado. El uso de una aprobación anterior no se admite después de una nueva selección.

Generar revalida ambas aprobaciones, sus consultas exactas, selección, fuente, prueba y autoridad. El servidor proyecta únicamente hojas explícitas aprobadas. La descarga revalida los mismos vínculos, expiración y política vigente. La respuesta final y el cierre siguen siendo acciones separadas con su propio criterio de aceptación.

## Integridad, retención y pruebas

Agregar borradores, consultas y decisiones al inventario por sujeto y al censo de dependencias. Excluir el propio procedimiento cuando corresponda a inventario de cuenta. Las huellas incluirán selección opaca, vínculos exactos, resultados y versiones sin descifrar contenido. Purga vacía el cuerpo cifrado y conserva metadatos auditables; probar ejecución efectiva de worker/Beat además de invocación directa.

La aceptación requiere PostgreSQL real para perfil y cuenta, replay y conflictos globales, corrupción de firmas/cuerpo, caducidad, permisos/sesión/MFA revocados tras espera observada, fuente o prueba cambiadas, aprobación de selección ajena rechazada, consulta obligatoria y autor excluido. Verificar HTTP con CSRF y GET privado, ES/EN móvil, inventario no vacío, purga y Docker actualizado. Probar que un campo no seleccionado, un contenedor o un selector añadido tras aprobación nunca se entregan. Conservar distinción entre datos sintéticos, simulación de identidad y validación real de producción.

## Avance de implementación

Modelo0086 y servicio save_selection inicial añadidos. La acción selection_save audita el uso de la evaluación aprobada antes de descifrar y firma una huella de la selección/version, además de fuente, prueba, evaluación y épocas. Borrador cifrado y huella HMAC ligados a metadatos originales; replay exige coincidencia exacta y vigencia. Censo54 verificado con PostgreSQL; inventario no vacío de la nueva selección aún pendiente. No hay consulta/revisión independiente de selección ni entrega autorizada todavía.

Purga inicial programada cada60s con lote100 SKIP LOCKED. Conserva vínculo de auditoría y huellas al vaciar ciphertext y marcar purged_at. La caducidad ya impide replay antes de que se ejecute la purga. Integración de purga e inventario no vacío en prueba; la ejecución real de worker/Beat todavía requiere verificación separada.

Consulta inicial de autor añadida: inspect_selection usa operación auditada selection_read antes de descifrar, firma ID/huella/ciphertext y versiones actuales de sesión/MFA; valida después firma original de guardado, prueba/fuente/vínculos y proyecta hojas explícitas. No es la revisión independiente prevista: todavía solo puede consultar el autor asignado. Nueva acción no consume prueba ni cambia el caso, y se revierte si falla validación. Regresión de consulta/replay/firma MFAoriginal en curso, todavía no aceptación del recorrido completo.

Lectura independiente inicial0087 incorporada: selección/acción/prueba protegidas, fuente/huella/épocas originales. Revisor requiere permisos específicos, MFA, ausencia de conflicto y lectura completa de expediente/respuestas; autor excluido. selection_inspect se registra antes del descifrado; se revalidan evaluación aprobada y firma del borrador, proyectando únicamente selección explícita. Censo55 e inventarios incluyen consulta sin exponer contenido. Pendiente resultado de integración y todavía no hay decisión independiente de selección ni entrega.

Decisión independiente inicial0088 añadida. Aprobación/rechazo únicos por selección, consulta propia obligatoria y decisión firmada ligada al ID exacto de consulta. Replay usa consulta original aunque haya otra posterior; manipular enlace invalida firma. validate_evidence liga firma a actor/caso/versiones originales/huellas/prueba/resultado, sin autorizar entrega por sí mismo. Inventarios incluyen decisión y censo56; resultado de pruebas pendiente.

Consumo inicial de aprobación: selección_use liga la aprobación exacta y la firma de decisión, revalida aprobación de evaluación y selección, firma original de consulta/guardado y vigencia. Último borrador global del caso obligatorio para decisión/uso; una selección posterior invalida la anterior aunque esté aprobada. Rechazo no habilita proyección para entrega. El servicio consume_selected devuelve proyección a llamador interno autorizado, sin exportación ni cierre ni consumo de prueba. Batería de integración pendiente.

Pantalla independiente conectada y verificada mediante cliente Django/PostgreSQL (2 pruebas46,66s): GET privado sin valores, consulta POST auditada, decisión sin valores y CSRF403. Listado50 en expediente filtrado por autoridad, excluye autor. Móvil/Chromium, preparación guiada y entrega pendientes.

Revisión independiente móvil verificada ES/EN con PostgreSQL/Chromium390px: contraseña/TOTP, consulta de expediente y selección, aprobación, GET privado posterior y sin desbordamiento. Dos pruebas49,09s. Evaluación y borrador preparados mediante fixture sintética backend; preparación guiada y datos mixtos permanecen pendientes.

Catálogo inicial para preparación guiada: consulta auditada de conjunto elegible resuelto, una fila y50 hojas escalares por página, referencia HMAC y caminos RFC6901. Auditoría selection_catalog firma conjunto/índice/página y evaluación/fuente/prueba/épocas; autoridad/fuente/prueba finales. No selecciona, guarda ni aprueba automáticamente. Unitarias4 correctas; integración PostgreSQL pendiente. Próxima interfaz debe preservar elecciones previas al editar páginas, ligar formulario firmado a la consulta exacta y rechazar datos fuera de la página/source/version antes de guardar.

Edición por páginas inicial: formulario firmado30min sin valores privados, vinculado a actor/caso/épocas/evaluación/consulta exacta/campos y base del borrador. Servidor reconstruye página auditada y verifica campos elegidos. Modificación afecta solo hojas de esa página y preserva el resto del selector completo. Nueva clave sobre base antigua rechazada; replay de guardado confirmado devuelve versión original sin reemplazar último borrador. Preparación y guardado ya tienen servicio inicial, pruebas PostgreSQL pendientes; interfaz y reinicio explícito ante base expirada o evaluación sustituida permanecen pendientes.

Pantalla de preparación guiada conectada: catálogo por conjunto/registro/página con casillas, POSTauditado y guardado de página, GET sin valores. Prueba PostgreSQL/cliente Django1 correcta37,06s, incluye preservación de páginas/replay/CSRF con sesión válida y tokens alterados controlados409. Preparación móvil, reinicio explícito y datos mixtos siguen pendientes.

Preparación y revisión móvil verificadas en dos sesiones distintas ES/EN: responsable entra con contraseña/TOTP, consulta campos y guarda checkbox; revisor entra por separado, consulta y aprueba. PostgreSQL/Chromium390px,2 pruebas54,22s, GET posteriores privados/caso intacto. La evaluación aprobada previa sigue fixture sintética backend. Reset de borradores caducados/evaluación sustituida y campos mixtos pendientes.

Reinicio explícito inicial de borrador: confirmación obligatoria, referencia/version/huella de base y motivo privado. Nueva selección vacía firmada a evaluación aprobada vigente; auditoría previa selection_reset liga base y clave del reset y conserva historial. Operación sobre una base purgada no descifra su contenido. Nueva clave contra base obsoleta rechazada; replay recupera versión confirmada sin reemplazar último borrador. Batería de integración pendiente; pantalla y variante de evaluación sustituida todavía no verificadas.

Reinicio de selección verificado backend/HTTP con PostgreSQL: base purgada, confirmación requerida, replay, referencia obsoleta rechazada; evaluación posterior bloquea reutilizar base antigua hasta reinicio confirmado y catálogo nuevo queda operativo.1 prueba39,74s de integración ampliada, no equivalencia a móvil ni concurrencia. Formularios de reinicio tienen IDs propios para labels.
