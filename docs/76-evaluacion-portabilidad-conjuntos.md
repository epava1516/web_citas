# Evaluación de portabilidad por conjuntos

Estado: inicio de implementación, no autorización de entrega ni cierre de solicitudes.

## Fundamento y decisiones

El artículo20 RGPD exige tratamiento automatizado basado en consentimiento o contrato y datos que conciernan al interesado facilitados al responsable. Deben respetarse derechos de terceros. Fuente primaria consultada: [RGPD EUR-Lex, artículo20](https://eur-lex.europa.eu/eli/reg/2016/679/oj/spa). La interpretación incluye determinados datos observados y distingue los inferidos; referencia [directrices WP242 rev.01 respaldadas por EDPB](https://www.edpb.europa.eu/documents/guideline/guidelines-on-the-right-to-data-portability-under-regulation-2016679-wp242_en). No atribuir base contractual a todo contenido por aceptar condiciones de uso; valorar tratamiento y origen del dato concretos.

Primera pieza implementada: rights_portability.checked_assessment exige nueve conjuntos existentes de copia, decisiones pending/eligible/excluded y base/origen/automatización/relación con interesado/revisión de terceros/motivo/evidencia. Elegible exige consentimiento o contrato, origen facilitado u observado y condiciones booleanas verdaderas. Desconocidos permanecen pendientes; exclusión exige explicación/evidencia. Es validación de declaraciones, no acredita la realidad de estas ni autoriza exportar. No integra todavía modelo, auditoría, autorización ni interfaz.

## Flujo completo pendiente

Persistir evaluación cifrada ligada a caso portability/prueba/fuente/versiones originales sesión-MFA/política, con clave global y motivo privado; consulta auditada previa, autoridad fresca y responsable asignado. Revisión independiente debe comprobar evidencia y decisiones a nivel de conjuntos y elementos cuando el origen sea mixto. Un conjunto completo no se vuelve elegible solo porque una parte lo sea: separar filas/campos y justificar terceros antes de incluirlos. Estado desconocido no se convierte automáticamente en exclusión final.

Generación servidor solo de elementos elegibles y revisados, formato estructurado con criterio y pendientes públicos mínimos; impedir cliente que añada campos/conjuntos. Conserva recorridos de acceso separados y partial/simulation mientras falten fuentes o identidad real. Entrega directa a otro responsable requiere viabilidad/canal autorizado, sin llamadas externas ni contratación por esta implementación. Descargar/replay revalida evidencia/identidad/fuente/caducidad; revisión de finalización es posterior y no se presume por generar copia.

Verificar perfil/cuenta, campos mixtos, origen agencia distinto del interesado, favoritos observados, datos inferidos y datos de tercero; permisos/COI/MFA, cambios de fuente/prueba/política, rollback y carreras observadas PostgreSQL; HTTP y móvil ESEN. Añadir inventario/purga/Docker y regresión conjunta. Este documento mantiene abierto todo el contrato.

Implementación inicial persistente: RightsPortabilityAssessment0084 y save_assessment, fuente/prueba/acción PROTECT, versiones originales sesión/MFA, cifra evaluación y motivo, caduca<=24h/prueba. PostgreSQL verifica replay y rechazo tras cambio de fuente, con expediente intacto. Batería12 (11 unidad+1 integración)31,17s. Persistencia no equivale a aprobación ni entrega; interfaz/revisión/purga/inventario/runtime pendientes.

Revisión independiente inicial0085: lectura y decisión protegidas, review_portability específico, autor excluido, lectura completa de caso y consulta propia obligatorias, firma guardado original y firmas de consulta/decisión originales verificadas. Aprobación rechaza conjuntos pendientes, no consume prueba ni entrega. POSTprivado y listado50 conectados;2 pruebas PostgreSQL/HTTP38,07s incluyen alteración MFAoriginal de decisión/sesiónoriginal de lectura, rollback. Inventarios de estas dos dependencias/móvil/carreras/runtime0085/selección granular aún pendientes.

Inventarios de revisión en preparación: incluir Read/Review como dependencias por sujeto, sin mostrar evaluaciones ni motivos; la cuenta excluye el procedimiento actual. Además de las huellas y las versiones originales, el inventario de decisión debe incluir read_id y outcome para detectar cambios de vínculo o resultado aunque permanezca el resto de campos. El censo aumenta a53; no interpretar un censo vacío como prueba de ámbito no vacío.

## Exclusión con condiciones desconocidas

La validación rechaza una exclusión que solo contiene explicación y evidencia textual sin una condición negativa explícita. Se admite fundamento ajeno a consentimiento/contrato, origen inferido/de tercero, tratamiento no automatizado o datos que no conciernen al interesado. Origen mixto y revisión de terceros pendiente no justifican excluir todo el conjunto: requieren evaluación granular. Esta validación comprueba consistencia de declaraciones; el revisor debe contrastar el fundamento y la evidencia, y no acredita cumplimiento jurídico.

Selección granular inicial verificada mediante ocho pruebas unitarias: referencias de fila ligadas a contenido, caminos escalares explícitos, omisión del resto y rechazo de fuente alterada, duplicados, contenedores y campos inválidos. No está persistida/aprobada ni habilita entrega.
