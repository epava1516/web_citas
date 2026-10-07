# Revisión extensa con Claude del rendimiento público

2026-10-07. Dos rondas solicitadas por el usuario en conversación lateral, mediante el adaptador original AI_ENGINEERING1.0.1. Fuente congelada bb4af0c; sin tocar código, configuración, runtime o cola operativa del hilo principal. Este informe aporta revisión, no una nueva cola ni aceptación funcional.

[Ronda1](evidencias/claude-rendimiento-ronda1-0110.json):247,974s. [Ronda2](evidencias/claude-rendimiento-ronda2-0110.json):180,439s. Ambas child0/wrapper0, JSON válido/tool-free; sin pruebas o archivos modificados por Claude.428,413s de ejecución acumulada. [Contraste independiente Codex](evidencias/claude-rendimiento-sesion-extensa-codex0110.json). El informe anterior de invocación6 sigue no aceptado por formato; no se cambia retrospectivamente.

Claude retiró sus propuestas de LRU entre peticiones y aislamiento distinto. Aceptó que el tiempo SQL cliente anterior no predice el nuevoSQL, que O(N) no demuestra imposibilidad y que200ms es una media de servicio ponderada para4workers20RPS, no un límite por listado. Codex corrigió además la falsa invariancia de fotos/relaciones aprobadas y la propuesta de generar miles de valores whatsapp únicos (es booleano).

## Hallazgos y límites

1. definitions() usa inspect.unwrap antes de calcular la huella. Un wrapper semántico instalado en runtime con functools.wraps puede conservar la misma definición observada. Codex verificó el mecanismo en Python estándar: original y wrapper se desenvuelven a la misma función, aunque pk=None pase y un PK sintético sea rechazado. No se ejecutó todavía la reproducción Django/PG de divergencia de elegibilidad/count.
2. PublicationContext.details_valid/contacts_valid/rate_valid y otros helpers nativos no figuran en la lista de clases/funciones de la huella. Inspección confirma la cobertura ausente; hace falta comprobar la paridad al cambiar una regla para una fila fuera de la página solicitada. Revalidar24filas no demuestra el count completo.
3. Una proyección con datos repetidos puede ahorrar validaciones por memo, mientras que descripciones/Telegram distintos reducen hits. No se conoce todavía la magnitud. Un diagnóstico diverso debe usar textos y handles sintéticos válidos y conservar el fixture contractual.
4. supported() calcula la huella dos veces por request; su coste específico todavía no está medido. No memoizarlo automáticamente sacrificando detección de cambios.

Las dos primeras son lagunas de la comprobación de definiciones observadas por fuente, no exposición reproducida en PostgreSQL ni fallos demostrados del escenario actual. Los perfiles transparentes no deben provocar que una comparación mida silenciosamente el fallback nativo; atribución de ruta es necesaria para interpretar la medición, pero no detecta por sí sola un wrapper semántico que la huella acepte.

## Síntesis para el hilo principal

La secuencia recomendada es: regresiones pertinentes de la huella y reparación si confirman divergencia; matriz comparable100/1000/10000 con ruta/memos/fallback/hidratación/huella identificados; diagnóstico adicional de diversidad válida separado. Mantener gates funcionales, población completa antes de count/orden/página24, normalizaciones, autoridad/revocación y recursos sintéticos propios. No clonar una base de una ejecución activa ni competir con sus mediciones.

Los criterios prefijados de la prueba corta incluyen generador/contabilidad/pendientes además de latencia/errores.900s solo si permite avanzar. No se modifica contrato, mezcla, uploads, p95<800ms, errores<1%, timeout/drain ni elINVALID previo. No instalar pg_stat_statements como requisito; EXPLAIN separado si evidencia delSQL afectado lo justifica. No backend nuevo aplicado ni mejora/capacidad/porcentaje atribuida por esta revisión.
