# Acta CR-07 — aceptación técnica local

Estado: verificado local. Código funcional6625454; documentación/probe reproducible4daa733. No aceptación de producción, rendimiento nacional ni GS-01.

## Requisitos y evidencia

- Listado/ficha ES/EN SSR conectados; categorías/servicios, atributos, tarifas y contactos elegidos. Descripción alternativa y lang real cuando falta traducción. Emails privados no incorporados.
- GET múltiples con OR por dimensión/AND entre dimensiones, servicios any/all; geografía dependiente y validación de ascendencia/CP públicos. Recarga móvil conserva selecciones y cambio territorial elimina hijos incompatibles.
- PostgreSQL full-text sobre revisión aprobada, relevancia ponderada, fecha real/UUID estable. Veinticuatro por página; prueba25 snapshots verifica24+1, Next/Previous, filtros persistentes y ausencia de duplicados.
- Elegibilidad completa antes de conteos/paginación; revocación elimina ficha/derivados/resultados. Privados/borradores no aparecen en búsquedas. no-store y acceso privado a originales.
- Comprobaciones específicas age/contact/agency, sin marca genérica. Procedencia compartida entre elegibilidad/etiquetas/filtro; cambiar nombre del proveedor no acredita procedimiento simulado. Proveedores reales no integrados.

Regresión completa `uv run pytest -q`:149 passed381.02s, PostgreSQL/Chromium, sin skips. Sesión39016 terminalexit0; código funcional no cambiado durante ejecución. Ruff/format/check/migraciones/diff-check pasan; nuevas comprobaciones/documentación no cambian lógica de aplicación.

Docker app/worker/beat reconstruidos, UID10001, migrate sin pendientes y collectstatic actualizado. `uv run python scripts/probe_demo_discovery.py` contra Caddy/Gunicornlocalhost18080 supera búsqueda, filtro/recarga, geografía dependiente, ficha/tarifas/edad simulada, imagen cargada y credenciales privadas404. La muestra principal conservada; contactos antiguos sin procedimiento se muestran sin acreditar.

## Límites y siguiente entrega

Búsqueda inicial revalida todos los candidatos antes de contar, correcta en privacidad pero requiere optimización/carga B-B. Selectores con muestra sintética; dataset nacional/licencia pendiente externo. SEO/estilo/a11y finales B-F/B-B. Promociones CR-10. No se acredita cumplimiento jurídico o verificación externa por esta acta.

Siguiente CR-08: favoritos privados y ciclo de vida según contratos/09; aún sin implementar. GS-01 pendiente hasta CR-10 y estabilización conjunta.
