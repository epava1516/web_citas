# B00-308 — Precedencia histórica y estado del grafo

Fecha: 2026-10-23. Corrección documental; sin pruebas de aplicación ni nueva aceptación técnica.

B00-308: corregida la precedencia histórica de producto, decisiones y seguridad, y el resumen del grafo que aún mantenía B07 pendiente. Sin nuevas fuentes acreditadas: 225 de 295 conciliadas, 70 pendientes. Nueve de los 18 puntos de beta cerrados; B00 sigue abierto y B15 opcional.

## Correcciones verificables

Se leyeron completos [producto01](01-producto.md), [seguridad03](03-seguridad-privacidad.md) y [decisiones05](05-decisiones.md). Producto01 ya tenía una advertencia de precedencia correcta; se hicieron explícitamente históricos los títulos de sus requisitos, modelo preliminar y condiciones iniciales. No se sustituyeron sus requisitos originales como si hubieran sido formulados hoy.

Decisiones05 mantenía afirmaciones de planificación y ausencia de implementación en presente. Se acotaron al corte inicial del 3 de octubre y se añadió la precedencia actual: DEC-037 sustituye el catálogo profesional de DEC-032 y limita la equivalencia con referencias; DEC-038 remite al diseño opcional B15 del contrato14§6.1. DEC-032 se conserva sin reescribir el antecedente. No se decide entre PostgreSQL y objetos ni se adopta como decisión la recomendación técnica conversacional.

Seguridad03 ya remitía a evidencias locales, pero una frase seguía afirmando que ningún control estaba implementado. Se aclara que la matriz es histórica, sin declarar todos los controles aceptados ni eliminar sus evidencias requeridas. La aceptación se contrasta por requisito y alcance en seguimiento17 y matriz88.

El generador local `seal_graph.py` seguía escribiendo ocho puntos cerrados y B07 pendiente. Se corrigió contra [acta16](actas/16-beta-b07-aceptacion-local-20261023.md): nueve cerrados, B01–B07 y B12–B13. B00, B08–B11 y B14–B17 siguen pendientes; B15 opcional. El ajuste no reabre ni revalida la carga B07.

## Evidencia y límites

Las copias previas, huellas y diffs específicos están en `artifacts/beta-promotion-fix-20261020/b00-308-corrections.json` y `b00-308-before-*`. Se conserva el ledger sin cambios: 225/295 y 70 pendientes. La consulta inicial del grafo fue orientativa y limitada por presupuesto de salida; las correcciones se basan en lectura directa de los documentos completos y el acta de aceptación pertinente.

Se actualiza sólo la semántica dirigida de los documentos indicados y el encabezado vigente de seguimiento17; no se atribuye una lectura nueva del resto del corpus ni un refresco AST, visual o semántico exhaustivo. Las comprobaciones documentales y de integridad no son pruebas funcionales, revisión jurídica vigente o aceptación beta. Continúa la conciliación de fuentes pendientes y el roadmap completo.
