# Revisión independiente de información de acceso

Estado: diseño de implementación; todavía no habilitado. Continúa docs73 y CR09; el contrato completo mantiene su alcance.

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


## Evidencia del guardado original

Extraer la validación de firma del guardado a una función de evidencia separada de record. Su entrada debe contener el borrador bloqueado, la fuente/prueba actuales y el cuerpo descifrado tras auditoría. Comprobar request/actor/action/proof, operation copy_info_save, versión y firma original; recuperar versiones de sesión/MFA de evidencia persistente, no del usuario que revisa. Los borradores actuales no almacenan esas versiones fuera de la firma: antes de implementar el segundo revisor se necesitan campos de evidencia para nuevas versiones, con migración sin inventar valores para registros antiguos. Los antiguos quedan consultables por su autor según el flujo existente, pero no deben aprobarse independientemente con valores supuestos.

El contrato de migración requiere compatibilidad temporal con0079 y despliegue de app/worker/Beat coordinado. Inventarios detectarán los nuevos campos sin proyectar motivos ni contenido. La caducidad de la consulta nunca supera borrador/prueba; una aprobación histórica no revive contenido purgado. No usar approved como sustituto del gate completo de respuesta final.
