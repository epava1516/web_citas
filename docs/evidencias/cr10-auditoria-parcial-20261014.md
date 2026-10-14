# Correspondencia parcial CR10

Contrato11 tiene siete criterios. Esta matriz vincula selecciones ejecutadas,
no acepta la fase antes de CR09 ni pagos reales.

| Criterio | Selección pertinente | Límite pendiente |
|---|---|---|
| 1 Catálogo incompleto no vendible | promotion_catalog / catalog_localization / conflict_localization | Fuente corregida de recarga en bloque 3; gate final pendiente |
| 2 Pedido propio particular/agencia y autoridad | promotion_orders / order_http / order_mobile_agency / order_races | Reconciliación exacta de cada variante/versión |
| 3 Evento sintético y concesión única | promotion_orders / order_races | Pago real fuera de v1; no inferir proveedor |
| 4 Patrocinio/filtros/rotación/paginación | promotion_exposure / localization / order_mobile_agency | Auditar toda cobertura de filtros/rotación, no solo presencia del rótulo |
| 5 Suspensión/autoridad/snapshots | promotion_exposure / bump_races / order_races | Reconciliar variantes de retiro/caducidad/transferencia |
| 6 Datos personales/derechos/restauración | promotion_audit_inventory / order_inventory / recovery | CR09 integral abierto; no deducir conservación jurídica desde fixtures |
| 7 Docker/contratos/gate común | Evidencia histórica Docker y particiones actuales | Versión común y dependencias abiertas |

[Reports exactos: 67 llamadas aprobadas en 13 archivos](cr10-regresion-correspondencia-parcial-20261014.json).
Los archivos de la selección no tienen reports fallidos. Eso no convierte el
bloque 3 globalmente negativo en PASS ni reúne distintas versiones como N3.

Aserciones inspeccionadas: snapshot monetario conserva importe al cambiar tarifa,
pending/failed no conceden, succeeded y replay conceden una sola vez; importe/
firma/actor inválidos y sesión revocada rechazan. Patrocinio usa conjunto visible
filtrado; retirado/caducado desaparece. Autosubida respeta ventana/cupo/replay y
preserva published_at/lifecycle/approved_revision/revision_count. Recuperación
usa el mismo pg_dump/pg_restore real del control CR09, añade huella comercial
conservada y verifica que promoción de sujeto suprimido no se reactiva.

Siguiente: terminar CR09 y reconciliar este mapa con todos los criterios/
evidencias, sin activar ventas ni sustituir ensayos completos con inspección.
