# Publicación por finalidad: calendario y levantamiento

Estado: implementación y pruebas parciales locales; no aceptación integral de CR-09. Referencia: [diseño/evidencias](../66-publicacion-finalidad-diseno.md).

Rutas con prefijo de idioma ES/EN:

| Nombre | Ruta | Métodos | Resultado |
| --- | --- | --- | --- |
| publication_calendar_queue | `/moderation/publication-calendar/` | GET | Fecha y enlace de medidas autorizadas; sin motivos ni totales ajenos |
| publication_purpose_release | `/moderation/rights/{case_id}/publication-purpose/{hold_id}/release/` | GET, POST | GET sin decisiones/motivos; POST de operación auditada |

Autenticación/MFA vigente y autorización específica en servidor. Calendario requiere `review_purpose_calendar` y autoridad de ejecución/revisión del expediente; consulta/propuesta/levantamiento requieren permisos e independencia definidos en el servicio. Conflicto de interés impide acceso incluso con permisos. Botones/enlaces no sustituyen autorización.

Calendario: filtros `attention=due|soon|all` (predeterminado due), `mode` y cursor cifrado ligado a actor/sesión/MFA/filtros y caducidad. Próxima página por fecha/ID, sin exponer detalles privados. Un retorno desde detalle abre el filtro predeterminado; seleccionar all para medidas con fecha futura.

Formulario privado: `key` UUID y `version` del expediente; `operation`; `reason` 20–2000 caracteres. Campos adicionales:

| Operación | Campos adicionales | Efecto |
| --- | --- | --- |
| inspect | — | Auditoría y decisión original validada solo en respuesta POST |
| follow_up | hold_version, next_review_on | Fecha operativa futura hasta90 días; version+1/evento; active y fecha inicial conservados |
| history | history_before opcional | Auditoría previa al descifrado, páginas50 y cursor; GET posterior sin motivos |
| propose | read_id, ground, resume_message_id cuando corresponda | Propuesta/respuesta de progreso; no levanta medida |
| execute | proposal_id | Solo tras recepción y nueva comprobación posterior; levanta medida seleccionada, anuncio pausado y expediente abierto |

Resultados:200 operación válida o replay exacto;400 entrada inválida;403 autorización/CSRF;404 ámbito ausente;409 versión/fuente/evidencia/estado incompatible;405 método no permitido. Respuestas privadas no-store/noindex; logs privados minimizados. Propuesta y levantamiento muestran mensajes distintos. La fecha operativa no es caducidad ni habilita publicación automática.

Mantenimiento: `restore_publication_calendar ID` previsualiza una medida con rollback; `--apply` conserva recuperación validada. No ruta HTTP ni atribución retrospectiva de decisión humana. Valida hechos firmados y secuencia, reconstruye fechas/eventos ausentes preservando timestamps y estado. Salida JSON minimizada; corrupción o ámbito ausente abortan con error genérico.

Proveedores de identidad/entrega siguen sintéticos o desactivados. La entrada inicial ofrece publication únicamente en expediente de perfil y preferencias cuando hay cuenta del sujeto identificada; 9 pruebas HTTP correctas109,23s; 2 pruebas móviles ES/EN correctas56,29s; aceptación conjunta actual pendiente.
