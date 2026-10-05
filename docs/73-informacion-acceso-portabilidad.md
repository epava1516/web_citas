# Información adicional de acceso y distinción de portabilidad

Estado: implementación parcial de borradores e interfaz guiada; aceptación integral pendiente. Continúa CR09 tras las proyecciones de datos de docs69–72; no convierte una copia parcial en respuesta final ni acredita producción.

## Fundamento primario consultado

Consulta2026-10-05: [RGPD, artículos15 y20, BOE](https://www.boe.es/buscar/doc.php?id=DOUE-L-2016-80807).

El acceso comprende copia e información sobre finalidades, categorías, destinatarios, conservación, derechos, reclamación, origen disponible, decisiones automatizadas relevantes y garantías de transferencias. Debe proteger los derechos de terceros. La portabilidad tiene condiciones propias: datos facilitados por el interesado, base de consentimiento o contrato y tratamiento automatizado; incluye transmisión directa cuando sea técnicamente posible. No basta con cambiar una etiqueta sobre una misma copia.

## Diseño de ejecución

Preparar un documento de información ligado a expediente, sujeto, tipo de derecho, versión de fuente y versión de política. Revisarlo mediante formulario ESEN y conservar decisiones cifradas/versionadas, auditoría previa de consulta, prueba vigente y permisos frescos. Definir origen de cada afirmación: configuración comprobada, dato del inventario o decisión del revisor; no inferir bases jurídicas desde el rol de usuario ni una casilla aceptada.

Campos de acceso: confirmación de tratamiento; finalidades y categorías aplicables; destinatarios/categorías y transferencias/garantías; plazo o criterio de conservación por finalidad; origen de datos ajenos al titular; descripción de automatización aplicable; vías de derechos/reclamación. Un dato desconocido permanece pendiente de revisión y bloquea el cierre integral, en lugar de transformarse en una afirmación falsa. La documentación técnica de desarrollo no reemplaza la política operativa aprobada.

Evaluación de portabilidad separada: decidir procedencia y ámbito por conjuntos de datos, indicar origen y base revisados, tratamiento automatizado y protección de terceros; no incluir automáticamente notas internas o datos ajenos. Toda exclusión necesita motivo operativo revisado y respuesta del caso; no ocultar datos de acceso por considerarlos no portables. Preparar formato estructurado y ruta de transmisión directa sin enviar a terceros ni contratar proveedor durante desarrollo.

## Verificación requerida

Perfil y cuenta propia, persona representada sin cuenta y gestor con aislamiento; accesos/replays/versiones/fuente/política obsoletos; referencias/motivos inyectados; campos pendientes no permiten cierre final; casos procedente/parcial/no procedente de portabilidad con justificación revisada. Navegador ESEN/móvil, PostgreSQL y carreras reales cuando consuman prueba o generen respuesta. Integrar la información revisada en generación, descarga y respuestas finales con su propia caducidad y conservación.

Pendientes conexos: completar censo/proyecciones, fuentes históricas y compartidas, originales/metadatos de imágenes según ámbito aprobado, volumen/memoria, conservación y restauración, destinatarios y cierre. No declarar satisfecho el artículo15/20 solo por aprobar esta especificación o por pasar pruebas de una selección de datos.

Backend inicial0078: RightsCopyInformation conserva expediente/actor/acción/prueba/fuente/policy_version/versión y cuerpo cifrado. policy_version es etiqueta de referencia, no acredita política aprobada. Servicio record exige autoridad/lectura/prueba vigentes, versión optimista y clave global; valida todos los campos de acceso con estado pending/reviewed y procedencia, reconsulta prueba/fuente al final y nunca modifica expediente ni permite cierre integral. Acceso exige portability=null; solicitud de portabilidad admite por ahora únicamente evaluación pendiente, sin fingir implementado el workflow de elegibilidad.

Contenido caduca≤24h/prueba; purge_expired_copy_information programada60s vacía lotes100 y preserva metadatos. Inventarios seleccionados incluyen ciphertext/estado sin descifrar; cuenta excluye procedimiento actual, censo seleccionado47 modelos.94289 terminal0:2 correctas30,94s;34764 terminal0:3 correctas41,20s PostgreSQL, /tmp/copy-information-inventory.xml.1075 activa4 casos /tmp/copy-information-validated.xml/log tras reforzar tipos de procedencia; fuente congelada. Sin aplicación de0078 al runtime Docker, sin prueba real Beat.

Pendientes antes de aceptar: formulario ESEN/lectura auditada, revisión independiente y política configurada/versionada verificable, matriz real de elegibilidad/datasets de portabilidad, vinculación a generación/respuesta/cierre, pruebas de cuenta/carreras/móvil/runtime/regresión y ámbito integral del contrato. El borrador almacenado es avance parcial, no satisfacción de artículos15/20.

1075 terminal0:4 correctas40,90s PostgreSQL, /tmp/copy-information-validated.xml. Registro/pending/procedencia/cifrado/replay/versiones/purga/inventario y tipos inválidos comprobados; Ruff/diff limpios. Sin proceso activo, fuente descongelada.0078 no aplicada al runtime, sin frontend/lectura ni aceptación integral.

Interfaz inicial conectada: /<idioma>/moderation/rights/<case_id>/information/, enlace desde preparación de copia. Formset exactamente10 apartados con etiquetas ESEN y field oculto; validación de identificadores distintos, status/source/text sin JSON completo. Referencia de política y motivo privados; guardar confirma solo referencia/versión y limpia cuerpo. Consulta POST por referencia/propósito crea copy_info_read antes de descifrar, luego replay de guardado revalida contenido/firma/prueba/fuente; fallos revierten auditoría incompleta. GET nuevo no recupera texto/motivos.

51880 terminal0:4 correctas39,56s PostgreSQL, /tmp/copy-information-guided-http.xml. Registro/cifrado/replay/temporales, tipos de procedencia y HTTP guiado guardar/leer/replay/GET limpio/corrupción409/revocación403. Fuente descongelada; sin proceso activo. Sigue pendiente cuenta/portabilidad, política aprobada, carreras, móvil, integración con generación/cierre, Docker0078 y regresión común.

98492 terminal0:6 correctas50,40s PostgreSQL, /tmp/copy-information-account-variants.xml. Variantes de cuenta access/portability guardan estado pendiente separado sin cerrar ni incrementar expediente; duplicidad de apartado409 y más de10 filas400 sin registros.35286 carreras reales de guardado activas7 casos /tmp/copy-information-save-races.xml/log: replay/version/permiso/prueba/sesión/MFA/fuente tras espera observada; fuente congelada hasta terminal. Runtime aún df326ca sin0078.

35286 terminal1:6 carreras correctas/1 fallo63,06s. Cambio de fuente durante espera era admitido porque record tomaba fuente actual sin comparación con formulario abierto. Corregido: formulario InformationForm exige source_digest oculto obtenido bajo locks en GET; POST lo compara en servicio mediante expected_source_digest antes de guardar. Guardados internos sin formulario toman fuente actual; no equivalen a revisión de una fuente anterior.84452 batería corregida activa13 casos información/carreras, /tmp/copy-information-source-corrected.xml/log; fuente congelada hasta terminal, recuperar mismo handle. No aceptar las6 carreras previas como cobertura de la guarda nueva.

84452 terminal0:13 conjuntas correctas89,47s PostgreSQL, /tmp/copy-information-source-corrected.xml.6 servicio/HTTP/cuenta y7 carreras con tres PIDs/espera observada: replay una fila, claves distintas un ganador, permiso/prueba/sesión/MFA/fuente cambiados deniegan ambas. Incluye nueva huella del formulario. Fuente descongelada, sin proceso activo. Móvil/lectura concurrente/política aprobada/elegibilidad integral/Docker0078/regresión conjunta/generación/cierre pendientes.

66327 terminal0:14 carreras correctas104,31s PostgreSQL, /tmp/copy-information-read-save-races.xml. Guardado y lectura serializados con espera observada/tres PIDs; replay único y revocaciones permiso/prueba/sesión/MFA/fuente/purga deniegan lectura sin auditoría parcial. Fuente descongelada.40892 build terminal0;55148 migración Docker0078 terminal0. Recreación92685 pendiente; cuenta/inventario no vacío y regresión conjunta aún pendientes.


## Política verificable — siguiente integración

La referencia de texto libre actual no habilita respuestas finales. Vincular cada decisión destinada a entrega a una versión concreta del documento de privacidad en LegalDocument, con idioma y huella de contenido; comprobar que sigue publicada y vigente antes de aprobar, generar y descargar. Cambiar el texto, desactivar la versión o cambiar de política invalida la aprobación previa y exige nueva revisión. Conservar evidencia histórica de la referencia sin sustituir versiones silenciosamente.

LegalDocument.active y published_at identifican publicación técnica, no aprobación jurídica. La aprobación operativa de la información necesita acción auditada de un revisor independiente y autoridad vigente; no inferirla de una aceptación LegalAcceptance ni de la existencia de texto legal. Los datos específicos del expediente no se rellenan automáticamente desde la política genérica. Mantener borradores pendientes para datos desconocidos y separar evaluación de portabilidad por conjunto. Este diseño aún requiere modelo/contrato/interfaz/pruebas coordinados; no habilita generación ni cierre por sí mismo.

Runtime0078 verificado: check sin incidencias, migrate-check, makemigrations sin cambios y health ok; siete hashes host/app/worker/Beat iguales, UID10001. Evidencia copia-informacion-runtime.json. Purga mediante llamada de test no acredita ejecución real de Beat.79667 regresión conjunta sigue en ejecución; no aceptada todavía.

79667 terminal0:24 conjuntas correctas171,32s PostgreSQL/Chromium; XML24/0fallos/0errores/0skips, /tmp/copy-information-common.xml. Guardado/lectura/carreras/móvil/censo e inventario cuenta no vacío: excluye expediente propio y terceros, incluye evidencia anterior del titular y detecta cambio opaco sin descifrar. Evidencia copia-informacion-regresion.json; runtime0078 verificado. Fuente descongelada. Entrega parcial lista para commit; política verificable/revisión independiente/elegibilidad/generación/cierre/CR09 integral y resto contrato pendientes.
