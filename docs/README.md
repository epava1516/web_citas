# Documentación del proyecto

Fecha de inicio: 2026-10-03. Idioma: español.

## Índice

- [Producto y alcance](01-producto.md)
- [Arquitectura y operación](02-arquitectura.md)
- [Seguridad, privacidad y moderación](03-seguridad-privacidad.md)
- [SEO y competitividad](04-seo.md)
- [Decisiones y preguntas pendientes](05-decisiones.md)
- [Marco legal y plan de cumplimiento](06-marco-legal.md)
- [Referencias de producto y competencia](07-referencias-competencia.md)
- [Publicaciones por categoría, etiquetas y tarifas](08-fichas-categorias.md)
- [Taxonomía, ubicación y búsqueda](09-taxonomia-ubicacion-busqueda.md)
- [Unicidad y prevención de duplicados](10-unicidad-antiduplicados.md)
- [Plan de seguridad, implementación y validación](11-plan-seguridad-validacion.md)
- [Operación de seguridad e incidentes](12-operacion-seguridad.md)
- [Decisiones para cerrar el contrato de desarrollo](13-cierre-contrato-desarrollo.md)
- [Contrato funcional v1: decisiones consolidadas](14-contrato-funcional-v1.md)
- [Apartado legal público y condiciones de publicación](15-apartado-legal-publico.md)
- [Contrato de ejecución: desarrollo cruzado y terminación separada](16-contrato-ejecucion-desarrollo.md)
- [Seguimiento y reanudación del desarrollo](17-seguimiento-desarrollo.md)

## Convenciones

Esta carpeta es la fuente de referencia de la planificación. Actualizar los documentos cuando cambien los requisitos; no limitarse a añadir notas de conversación.

La especificación vigente consolidada es `14-contrato-funcional-v1.md`, definida tras delegación del usuario. Sustituye propuestas/preguntas históricas sobre los puntos que cierra; las decisiones previas expresas del usuario tienen prioridad. No representa implementación o acreditación de cumplimiento.

Para ejecutar: `16-contrato-ejecucion-desarrollo.md` define el orden completo y los gates, con `15-apartado-legal-publico.md` incorporado al alcance; `17-seguimiento-desarrollo.md` indica dónde continuar. El nuevo orden empieza por flujos frontend/backend cruzados y pruebas tempranas, luego permite terminación separada con contratos estables y termina con integración común.

- **Confirmado:** requisito expresado por el usuario.
- **Propuesto:** recomendación pendiente de acordar.
- **Pendiente:** información o decisión todavía no resuelta.
- **Descartado:** alternativa rechazada, indicando el motivo.

Usar identificadores estables REQ-xxx para requisitos, DEC-xxx para decisiones y PRE-xxx para preguntas. Las decisiones técnicas significativas se documentarán en `adr/` con contexto, alternativas, consecuencias, fecha y estado. No registrar secretos, documentos de identidad ni datos personales reales aquí.

No considerar una propuesta aprobada por el mero hecho de estar documentada. Diferenciar controles implementados de controles planificados y citar fuentes para afirmaciones normativas.

- [Evidencias de desarrollo](18-evidencias-desarrollo.md)
- [ADR base técnica](adr/001-base-tecnica.md)
- [Contrato de cuentas y legal](contratos/01-cuentas-legal.md)

- [Contrato agencias y MFA](contratos/02-agencias-mfa.md)

- [Contrato verificación y representación](contratos/03-verificacion-representacion.md)
