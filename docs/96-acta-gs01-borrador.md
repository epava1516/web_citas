# Acta GS-01 — borrador de comprobación (no emitida)

Fecha: 2026-10-10. Redacta: Claude principal (MOD-07). Estado: **BORRADOR, puerta no superada**. Criterios: [contrato16 §6](16-contrato-ejecucion-desarrollo.md#6-puerta-de-separación--gs-01). Estado vigente: [seguimiento17](17-seguimiento-desarrollo.md). Este documento no acepta CR09, CR10 ni GS01; solo prepara el acta para que se emita sobre un único commit integrado cuando las condiciones se cumplan.

## Condiciones y estado

| Condición (contrato16 §6) | Estado | Evidencia o bloqueo |
| --- | --- | --- |
| CR-01 a CR-10 con recorrido real y pruebas esenciales | **No cumplida** | BASE y CR01–08 verificados; CR09-REND-LECTURA aceptado (`1a10ecf`). CR09 integral abierto: capacidad de expedientes (matriz 83) pendiente de MOD-08 e integración `codex/mod08-integration`. CR10 en preparación ([contratos11](contratos/11-promociones-preparacion.md)), sin aceptación. |
| Pantallas MVP con operaciones/estados servidor y contratos documentados | **Parcial** | Rutas: 164 patrones documentados, 0 omitidos, exigido por `tests/test_route_inventory.py` ([contratos12](contratos/12-rutas-complementarias.md)). Falta revisar estados/formularios de CR10 tras su cierre. |
| Sin cambios coordinados conocidos en modelo, permisos, campos, estados, rutas, tareas o presentación | **No cumplida** | MOD-08 cambia generación (pieza 5, Celery), almacenamiento (6/8), evidencia (11) y revisión por lotes (12, contrato funcional). Deben integrarse y documentarse antes del acta. |
| Errores de permisos, publicación, datos privados y cargas corregidos | **Pendiente de batería única** | Correcciones registradas en seguimiento17; falta N2/N3 sobre la versión integrada. |
| Estados carga/vacío/error/pendiente y variaciones de rol/idioma probados; no hace falta endpoint nuevo para la UI | **Parcial** | Pruebas móviles ES/EN por flujo existen; falta inventario de estados por pantalla (se completará con BF-prep sin endpoints nuevos). |
| Integraciones externas aisladas, sin implicar gate de producción | **Cumplida en diseño** | Adaptadores simulados identificados; ningún proveedor real ni publicación. Verificación simulada nunca declarada real. |
| Inventario residual asignado a frontend o backend sin cambiar contrato compartido | **Pendiente** | Se elaborará tras integrar MOD-08 (ver abajo). |

## Inventario residual preliminar

| Tarea | Área | ¿Cambia contrato compartido? |
| --- | --- | --- |
| Sistema visual común (tokens, componentes, responsive, foco, contraste) | BF | No: solo CSS y plantillas, sin campos ni rutas. Rama `claude/bf-design-system`. |
| Estados vacío/error/pendiente homogéneos en paneles, agencia y moderación | BF | No, si usa estados ya expuestos por las vistas. |
| Progreso de generación asíncrona (pieza 5) | Cruzado | **Sí**: estado/progreso nuevo; mini-flujo cruzado con prueba navegador antes de GS01. |
| Revisión por lotes auditada (pieza 12) | Cruzado | **Sí**: contrato funcional de lectura; actualizar contratos internos antes de GS01. |
| Optimización de consultas e índices, reintentos, retención | BB | No, sin cambio de semántica. |
| Backups, restauración, alertas, Docker/producción | BB | No. |

## Para emitir el acta

1. Integrar MOD-08 en master (dirección Codex) y cerrar capacidad CR09 con veredicto PASS válido.
2. Aceptar CR10 con su batería integrada.
3. Completar el inventario de estados por pantalla y el residual definitivo.
4. Ejecutar N3 sobre un único commit y registrar aquí commit, pruebas, contratos congelados (hash de `docs/contratos/`) e inventario residual.
