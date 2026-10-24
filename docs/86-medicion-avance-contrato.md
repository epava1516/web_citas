# Medición del avance del contrato

## Alcance temporal de las estimaciones — 2026-10-24

La revisión v10 y los estados abiertos de abajo conservan su fecha y denominador históricos; no son una medición del producto adaptado hacia beta. CR09 tiene [aceptación técnica local](actas/05-cr09-aceptacion-tecnica-local-20261018.md) y el [alfa fue consolidado](actas/10-entrega-tecnica-local-alpha-20261020.md) en sus respectivos cortes. El avance actual se consulta en [seguimiento17](17-seguimiento-desarrollo.md) y el [roadmap beta](103-roadmap-beta-clasificados-20261020.md), sin convertir el número de puntos cerrados ni las fuentes conciliadas de B00 en porcentaje de esfuerzo. No se recalculan o sustituyen aquí los pesos, grados, fallos o cifras de v10.

Actualizado documentalmente: 2026-10-09. Revisión vigente **v10**, sin cambio por organización ni por aceptación local posterior de lectura. [Cálculo original](evidencias/avance-ponderado-v10.json). El estado y la cola se consultan en [seguimiento17](17-seguimiento-desarrollo.md); los pendientes, en [matriz83](83-auditoria-pendientes-cr09.md).

## Método y límites

Estimación de ingeniería por alcance/complejidad, con pesos y grados de terminación explícitos: `avance = suma(peso × grado /100)`. Cada nivel suma100% de peso. No mide horas, cobertura de pruebas, seguridad jurídica ni aceptación formal; un grado100 de componente no cierra una fase por sí mismo.

Mantener pesos/denominador estables y justificar cambios de grado con alcance nuevo entregado, su versión y evidencia. No incrementar por commits, número de tests, correcciones repetidas, velocidad o documentación. Un cambio de alcance/peso se registra conforme al contrato; no cambiar el denominador para lograr avance.

La consolidación contractual v1.6 separa aceptación local y preparación de producción en matriz83. Esta aclaración no es alcance nuevo verificado ni recalcula v10: sus cifras conservan su corte de evidencia y no indican que entradas reales de producción impidan verificar los mecanismos locales. Cualquier actualización futura de grados necesita entrega/evidencia nueva y justificación con los mismos pesos.

Las cifras82% CR09/56% contrato eran estimaciones sin desglose verificable y se conservan solo en el historial. Las revisiones v1–v9 tienen sus cortes y evidencia originales; v10 prevalece. BASE/CR01–08 son9/15 hitos verificados localmente:60% del número de hitos, no60% del esfuerzo ni preparación de producción. CR09 integral permanece abierto.

## Avance verificable dentro de CR09

| Bloque | Peso | Grado estimado |
| --- | ---: | ---: |
| Portabilidad y respuesta privada | 15% | 90% |
| Purga de contenido caducado | 5% | 100% |
| Flujos de denuncias y derechos por finalidad, verificación y autoridad | 20% | 85% |
| Conservación y destrucción por finalidad | 10% | 50% |
| Restauración de datos y medios | 15% | 85% |
| Sesiones, cachés, colas, logs y recursos externos | 10% | 60% |
| Comunicaciones y destinatarios | 8% | 70% |
| Atención urgente y escalado | 7% | 70% |
| Rendimiento de expedientes grandes | 5% | 55% |
| Aceptación integral CR09 | 5% | 0% |

Resultado exacto: **CR09 72,50% avanzado /27,50% pendiente**. El bloque de flujos conserva denuncias/autoridad y diferencias entre derechos; purga 100 se limita a su entrega, conservación 50 y aceptación integral 0 mantienen sus pendientes. [Componentes/evidencia88](88-matriz-cierre-derechos.md), [condiciones83](83-auditoria-pendientes-cr09.md).

## Contrato completo

| Hito | Peso | Grado estimado |
| --- | ---: | ---: |
| BASE | 5% | 100% |
| CR01 | 4% | 100% |
| CR02 | 6% | 100% |
| CR03 | 6% | 100% |
| CR04 | 5% | 100% |
| CR05 | 8% | 100% |
| CR06 | 6% | 100% |
| CR07 | 6% | 100% |
| CR08 | 4% | 100% |
| CR09 | 15% | 72,5% |
| CR10 | 5% | 90% |
| GS01 | 3% | 0% |
| BF | 10% | 0% |
| BB | 10% | 0% |
| C | 7% | 0% |

Resultado exacto: **contrato 65,375% avanzado /34,625% pendiente**; presentación65,38% avanzado. CR09 pesa15% del contrato. CR10 técnico 90 refleja preparación comercial local y reserva aceptación/dependencias; no acepta CR10, GS01 o fases posteriores. Proveedores, identidad, revisión jurídica y gates productivos siguen separados de evidencia sintética.

## Evidencia de la revisión v10

Transporte seleccionado binario 9437486bytes y JSON 8653938bytes desde selección/cobertura/revisión nativas hasta cierre/replay y descarga TCP local, con huellas/contenido exactos. [Binario](evidencias/portabilidad-binario-cerrado-tcp0110.json), [JSON](evidencias/portabilidad-json-cerrado-tcp0110.json). Dos dimensiones de alcance aumentaron rendimiento 45→55; no se acredita capacidad/concurrencia/p95 productivos, proveedores o N3.

La aceptación local posterior de CR09-REND-LECTURA en `1a10ecf` conservó explícitamente los porcentajes. Registrar requisito → implementación → versión → prueba → evidencia → pendiente antes de cualquier valoración nueva; no sumar resultados de fuentes distintas como una batería común.

## Historial de ponderación

[Copia íntegra anterior](17-historial/2026-10-09-86-medicion-avance-contrato-antes-organizacion.md): conserva baselinev1, revisionesv2–v10, razonamiento, fórmulas y próximos pasos históricos. Los JSON de cálculo originales permanecen intactos en `evidencias/`. [Inventario de copias](historial-documentacion.json).
