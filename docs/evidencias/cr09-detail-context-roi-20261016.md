# CR09 — contexto nativo de detalle: paridad y ROI aislados

Prototipo sólo en tests; `apps/` no cambia. Sustituye la hidratación/guard individual del detalle por PublicationContext de una revisión actual, mantiene publicly_visible(context=...) y render/presentación originales. Prefiltro escalar excluye pausado/vencido/sinaprobación/revisiónajena antes de materializar hijos, sin sustituir el guard completo. No se usaPublicationState para conceder acceso ni cambia todavía el aislamientoRC.

## Evidencia

Paridad `094738-3d159a2a`:1PASS47,22s,18comparacionesESEN (válido, teléfono/contenido/consentimiento/tarifa/autoridad inválidos, normalización, revisiónajena y pausado) yUUIDausente. Status/cuerpo exactos; se fija sólo el componente temporal deTimestampSigner y permanecen firma/payload nativos. [Recibo](cr09-detail-context-parity-20261016.json).

ROI `095050-c4a52ac2`:1PASS125,57s,288lecturas medidas+108warm,10ksintéticos/PGreal propio. A/Bcallbacknativo idéntico; Cprototipo,ABC/BCA/CAB,6warm+16medidas por brazo/ruta/bloque. WSGIHandlerreal, sin capturaClient ni plantillas instrumentadas. GCnormal;collectantesdelwarmúnicamente; backendPIDestable por brazo. Ambos brazos fijan el mismo componente temporal firmado. NoTCP/Gunicorn/concurrencia/Beat/subida; DBcpu/RSSnoobservados.

| Ruta | Referencia A/A | C | Ahorro wall | Ahorro CPU | SQL |
|---|---:|---:|---:|---:|---:|
| es | 83.480ms | 60.701ms | 27.29% | 22.29% | 36→22 |
| en | 80.736ms | 56.246ms | 30.33% | 24.52% | 36→22 |

Ambas rutas superan la condición prerregistrada para continuar controles: A/A<=10%wall/CPU, ahorro wall>=10%, regresiónCPU<=5% y no-regresiónwall>=2/3bloques (aquí3/3). Se mantiene el cuerpo en todas las lecturas, Dirtyvacío y misma políticaGC. [Muestras completas](cr09-detail-context-roi-20261016.json).

Fuentes congeladas contrastadas independientemente antes de documentar; controlador/hijo porPID/start_ticks terminados, temporales y contenedores propios ausentes, cgroup vacío. Python3.12.15/dependenciascongeladas/native-sealed/PG17.11 y presupuestos anteriores. Sin producción/datos reales/proveedores.

## Decisión y controles necesarios

Hay ROI aislado para continuar, **no autorización técnica de integración todavía**. PublicationContext adelanta/agrega lecturas que el guard nativo consultaba en sentencias separadas; bajoRC pueden observar commits concurrentes en momentos distintos. N1secuencial no demuestra frescura equivalente. Antes de integrar: revisar contrato y carreras de autoridad/privacidad/consentimiento/catálogo/fotos/revisión, expiración durante guard, restauración de configuración en éxito/error y transacción heredada. Si se necesita otra política de snapshot, debe justificarse y medirse como cambio distinto; no afirmar que esta prueba ya la cubre.

Las fotos/presentación de salida mantienen lecturas originales tras el guard, y la revisión que se renderiza es la validada en el contexto (incluidas normalizaciones); no se copia el booleano sobre otra instancia. La revisiónajena se rechaza aunque existaFKválida. Faltan controles de ausencia de documento/consentimiento y variantes de catálogo fuera del fixture inicial, además de candidatos y referencias históricas.

Este ahorro corresponde a dos rutas concretas de detalle, no al conjunto del requestmix ni al p95. No se extrapola a una mejora global del27–30% ni se lanza carga limpia por superar una microcomparación. Producto sigue7ec6f51; última carga limpia1,052089655sFAIL. CR09/N3/global abiertos.
