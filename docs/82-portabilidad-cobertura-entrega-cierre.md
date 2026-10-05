# Portabilidad: vincular cobertura, entrega y respuesta final

Estado: diseño técnico de siguiente integración; no implementado ni aceptado. Continúa CR-09 y el contrato completo. La regresión actual 0093 permanece congelada.

## Hallazgos comprobados en código

- `rights_responses.issue` admite únicamente `progress` y `representation_complete`; no existe respuesta final de portabilidad.
- `rights_portability_export.generate` incrementa la versión del expediente una vez. `validate_export_binding` valida selección y prueba históricas usando la versión anterior, y exige que la exportación pertenezca a la versión actual.
- El payload existente declara `partial=True`, `simulation=True` y revisión final pendiente. Su contenido se reconstruye al verificar la firma: cambiar estos literales sin versionar invalidaría exportaciones anteriores.
- La cobertura aprobada 0093 conserva lecturas originales y prueba/fuente de su versión. Su aprobación aún no se consume al generar una entrega ni autoriza cerrar el expediente.

## Integración requerida

1. Añadir consumo auditado de cobertura aprobada antes de usar su contenido. Validar autor responsable, revisor independiente actual, permisos, épocas originales, prueba/ámbito/canal, caducidad, última cobertura/selección, firma de la decisión y IDs originales de todas las lecturas. Compilar cobertura estricta nuevamente. No confiar en `complete` del borrador.
2. Vincular la exportación a esa aprobación mediante evidencia persistente protegida, con hashes del cuerpo cifrado, selección, fuente, decisión y lecturas originales. La generación parcial existente conserva su contrato; la entrega con cobertura debe tener esquema/firma versionados y validación compatible de exportaciones anteriores.
3. Separar validación histórica de ejecución de autorización actual. Después del incremento de versión, reconstruir la fuente histórica con la versión original para verificarla, sin tratar una prueba histórica como prueba actual para emitir una nueva respuesta final.
4. Preparar respuesta final específica con referencia protegida a exportación y cobertura, estado de entrega/acuse y explicación pública de alcance y exclusiones. Las notas/evidencias privadas, HMACs, valores de terceros y contactos operativos no se copian al texto público.
5. Exigir autorización y lectura vigentes de expediente/respuestas en la versión de cierre. Si requiere nueva comprobación de identidad/ámbito, iniciarla explícitamente; no alterar la prueba original ni asignar artificialmente su versión.
6. Revisión independiente de la respuesta final ligada a su texto cifrado, versión, entrega y cobertura exactas. Registrar aceptación y cierre atómicos con clave global: reintento idéntico no duplica respuesta, aviso ni transición; revocación durante una espera deniega sin efectos.
7. Preservar plazos, cronología, auditoría y acuses históricos. El cierre no debe romper la descarga autorizada de la entrega durante su vigencia: revisar expresamente su dependencia actual de `case.version`, implementando una compatibilidad histórica limitada y autorizada, sin omitir validaciones.
8. Mantener marcada cualquier identidad/comunicación sintética. Una aprobación técnica sobre fixtures no acredita revisión legal humana ni preparación real de producción.

## Evidencia de aceptación necesaria

- PostgreSQL: generación ligada a cobertura completa, denegación de parcial/rechazada/obsoleta, corrupción de firma/cuerpo/IDs, replay y caducidad.
- Concurrencia observada: generación y cierre ante cambio de permiso/sesión/MFA/prueba/ámbito/canal/fuente/aprobación, con conexiones distintas y bloqueo identificado.
- HTTP/Chromium ES/EN perfil/cuenta: preparación, lectura independiente, entrega privada y revisión/respuesta/cierre; GET sin cuerpos privados, CSRF y móvil.
- Descarga/acuse antes y después del cierre, sin ampliar acceso a sujetos ajenos ni reactivar transporte caducado.
- Inventarios no vacíos de nuevas dependencias, purga por worker/Beat reales, restauración y conservación de auditoría.
- Regresión conjunta de implementación y Docker sobre fuente estable; documentar limitaciones de CI separadamente.

No añadir la opción de cierre al formulario hasta que el recorrido completo y sus validaciones estén implementados.

## Reintentos de respuesta final y permisos actuales

La inspección de `rights_responses.issue` muestra que la recuperación de una respuesta existente por clave sucede antes de las comprobaciones de versión y lecturas completas. Ese orden no debe copiarse como autorización suficiente del nuevo cierre: una firma histórica acredita qué se emitió, pero no los permisos actuales del solicitante de un reintento.

El nuevo flujo debe cargar el actor vigente después de adquirir los bloqueos, comparar las épocas originales de sesión/MFA y comprobar permisos, asignación y ámbito antes de devolver incluso una respuesta ya registrada. Un reintento admitido debe conservar exactamente la respuesta, el aviso, la transición y sus referencias originales; no exigir una segunda transición ni crear lecturas que sustituyan las que autorizaron el cierre. La validación de entrega histórica y la autorización actual de consulta siguen siendo controles distintos.

Pruebas específicas pendientes: repetir la misma clave después del cierre y comprobar ausencia de efectos adicionales; repetirla tras revocar permiso, sesión o MFA y comprobar denegación; reutilizarla con otro actor, expediente, texto, entrega o cobertura y comprobar conflicto. Ejecutar también revocaciones durante un bloqueo PostgreSQL observado. Esta sección es una condición de implementación y aceptación futura, no una corrección ya aplicada al servicio existente.

## Escalabilidad de la puerta de revisión: pendiente comprobado por inspección

`require_complete_reads` recorre cada lectura y llama `inspect_page`; esa función consume una inspección de selección y reconstruye `source_copy` antes y después. Con P páginas y S tamaño de fuente, la revalidación repite trabajo sobre la fuente aproximadamente P veces. Es una inferencia del código, no una medición de latencia ni una prueba de carga. La batería de volumen existente contiene 1500 revisiones, pero todavía no pasa por esta puerta de cobertura.

Antes de aceptar grandes historiales, validar todos los registros originales bajo una única fuente bloqueada y una autorización fresca, reutilizando la fuente y las estructuras preparadas dentro de la transacción. La refactorización debe verificar cada firma original, propósito, page_digest, prueba, actor y épocas sin crear lecturas de sustitución. Conservar la revalidación de autoridad/fuente al final. No resolverlo aumentando indiscriminadamente el timeout Gunicorn actual de45s, omitiendo páginas o aceptando únicamente contadores.

Añadir mediciones PostgreSQL con historial grande y binarios, número de consultas, duración y memoria de la revisión completa. Documentar recursos y distinguir tiempo instrumentado de latenciaHTTP. Si se decide procesar en worker, el trabajo debe volver a comprobar autoridad/fuente/prueba al ejecutar y antes de registrar resultado, con estado visible y sin aprobación anticipada. Esta optimización permanece pendiente; las pruebas correctas de expedientes pequeños no acreditan el rendimiento de historiales grandes.
