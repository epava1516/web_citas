# B13 — Conciliación literal final y verificación de candidata

Estado: B13 aceptado técnicamente en local por acta15; ocho puntos cerrados de18. Requisitos tomados de [roadmap103](103-roadmap-beta-clasificados-20261020.md), [contrato16](16-contrato-ejecucion-desarrollo.md) y [OP005](12-operacion-seguridad.md), sin reducirlos a la prueba que pase más fácilmente.

| Requisito local literal | Evidencia a comprobar | Límite que debe conservarse |
| --- | --- | --- |
| Caída worker/broker y recuperación |141 y repetición final26: procesos/Redis propios, outbox PostgreSQL, despacho y replay idempotentes | No reboot ni muerte a mitad de tarea; entrega final simulada |
| Revisión, denuncia y retirada urgente |144/B06 y repetición final:14drills y2casos ES/EN con publicación obsoleta/promociones | Personal y canales reales no se acreditan |
| Rotación de secretos |142/148/149/151/154/159: Fernet, Django, dominio, PostgreSQL/Django, Redis/Kombu, proxy | Readers no se retiran por muestra; dominio revoca canales, no migra bindings; no live reload universal |
| Restaurar DB y medios en aislamiento |152 y cinco restauraciones finales reales | Sin listener/worker sobre clon; no offsite/PITR/infraestructura real |
| Derechos/sesiones/grants/publicación antes de exponer |152: reconciliación, invalidación y rebuild con publication_authorized=false;155ledger inválido bloquea3CLI | No fabricar checkpoints; flags no sustituyen aislamiento externo |
| Rollback de aplicación |158:5a0751c1→66c6d381→5a0751c1,11tablas,medios,recibos,escrituras/3workers/TCP | Mantener correo explícito permitido; retorno carece de guardia nueva; no producción HTTP |
| Estrategia de migraciones |145/146/158 y tres testigos finales:upgrade/legacy/guardia etiqueta | Conservar esquema; no downgrade a alfa ni borrar filas/columnas para hacer arrancar código |

## Conjunto final prefijado

26casos,4workers, runner oficial y PostgreSQL/Redis propios. Cuatro parámetros de test_recovery_pg_restore más promoción/restauración real:5. Caída de servicios:2. Retirada beta:2. Drills urgentes:14. Migración de contenido romántico, bloqueo de descenso con etiqueta elegida y upgrade de estado almacenado:3. Selectores exactos conservados en el resultado del runner. Ninguna prueba de capacidad; cortoB07FAIL y900s bloqueado.

Se exige PASS de los26sin omisiones, resultado terminal tras limpieza y fuentes idénticas; conservar cualquier warning con su causa, sin declarar una ejecución libre de avisos si no lo es. Contrastar cada propiedad con JUnit y los artefactos reales de restauración/servicios. Inventariar las diferencias de fuentes respecto de las evidencias de rotación y su ámbito de reutilización; no sumar casos repetidos como únicos ni declarar un N3 completo por26casos.

Los21casos de159 y el ciclo158 ya tienen auditoría terminal sobre el mismo runtime726. La aceptación requiere revisar también sus pruebas y los runbooks, no sólo el texto result=PASS de un JSON. La matriz final debe señalar qué familias/bindings no admiten transición automática y mantener aislamiento hasta verificar sus operaciones. No convertir un pendiente técnico en responsabilidad humana de B17.

## Apertura y límites separados

Personas, sustitutos y cobertura real G03/G06/G07 se asignan en B17, como exige explícitamente B13 para apertura. Custodia, proveedor, producción, revisión jurídica/externa y canales reales no se acreditan aquí. Rollover de ledger, retirada completa de claves, revalidación de todos los bindings o recuperación sin clave no se declaran implementados ni pasan a verificados por una aceptación local de ensayos. Si la revisión encuentra un requisito local sin prueba suficiente, B13 seguirá abierto y se trabajará en él.

## Resolución

Conjunto26PASS auditado, con3avisos conocidos de Celery ysinomisiones. Los siete requisitos locales quedan comprobados en la [matriz literal](evidencias/b13-local-requirement-acceptance-matrix-20261021.json) y [acta15](actas/15-beta-b13-aceptacion-local-20261021.md). Nuevos casos de revocación21y ciclo158 son ejecuciones separadas sobre runtime726igual; fuentes de test/dependencias y compatibilidad del resto de evidencia de rotación verificadas. No suma global de casos repetidos ni N3 completo. Los límites técnicos explícitos y controles de apertura de arriba no se convierten en implementados por el cierre local.
