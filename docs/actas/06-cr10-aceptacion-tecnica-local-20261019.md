# CR10 — aceptación técnica local, 2026-10-19

Se acepta CR10 en el alcance técnico local de v1 sintética. Revisor: Codex principal. Corte revisado `81cb4c3`; la imagen se construyó sobre `aa2de37` y sus623archivos de producto siguen iguales. La [matriz de siete criterios](../evidencias/cr10-local-acceptance-matrix-20261019.json) conserva los requisitos literales, casos actuales, procedencia, decisión y límites.

| Criterio | Decisión y evidencia |
| --- | --- |
| 1. Catálogo y previsualización | Aceptado: ES/EN, Chromium, versiones y publicación concurrente, configuración pendiente y ventas inactivas, permiso/MFA/CSRF y ausencia de mutación por GET. |
| 2. Pedidos propios | Aceptado: particular y agencia, snapshots del servidor, aislamiento del comprador, gestión revocada y conflictos de clave; autoridad revalidada tras bloqueo. |
| 3. Eventos y concesión única | Aceptado: firma e importe/moneda sintéticos comprobados por servidor, pending/failed y eventos inválidos sin concesión, replays/carreras PostgreSQL y rollback de auditoría. |
| 4. Exposición pública | Aceptado: patrocinio ES/EN en móvil anónimo, filtros, dos páginas y rotación diaria de40publicaciones/28promociones, sin duplicados ni cambios editoriales. Retirados no reaparecen. |
| 5. Cese y tareas | Aceptado: pausa/caducidad/consentimiento en guardia pública compartida, llamada por elegibilidad comercial; retiro, caducidad del derecho, gestor/comprador revocados, carrera y tarea antigua, cuotas/ventanas y restauración sin reactivar. No se inventa política de reembolso o ampliación. |
| 6. Datos y derechos | Aceptado: auditoría del catálogo y seis tablas de pedido en inventarios perfil/cuenta como evidencia dependiente; terceros aislados y cambios invalidan huellas. Restauración real conserva snapshots y aplica supresión antes de habilitar exposición. Depende del [CR09 aceptado](05-cr09-aceptacion-tecnica-local-20261018.md); plazos/finalidades definitivos y custodia productiva siguen separados. |
| 7. Integración e interfaces | Aceptado:67casos comerciales de regresión común actual, tres controles adicionales separados y Docker actual, con contratos de rutas/formularios/eventos y modo sintético explícito. |

Los67casos actuales de13archivos tienen setup/call/teardown PASS y fuentes idénticas. Los [controles de rotación](../evidencias/cr10-pagination-rotation-terminal-20261018.json) (1PASS) y [móvil público](../evidencias/cr10-public-mobile-terminal-20261018.json) (2PASS) son runs complementarios sobre producto idéntico; **no se presentan como un único run de70casos**. Los controles de pausa/caducidad/consentimiento del mecanismo público y su llamada desde elegibilidad se vinculan expresamente en la matriz. El testigo histórico de worker/Beat real se conserva con tres fuentes comerciales idénticas, sin convertirlo en una nueva prueba de carga.

[Docker actual](../evidencias/cr10-docker-v11-verified-20261019.json): imagen inmutable `sha256:261d4b6d97f581ddf8cfd19318b3455eda8bafafb5de4e151c084d08d2200fbd`,623fuentes iguales, kernel native-sealed con sello propio, once paridades, ocho rutas HTTP, PostgreSQL17 real, cuatro workers, UID10001 y limpieza independiente. Copia privada0600 y SHA256 verificados para restaurar el entregable local. No equivale a capacidad medida dentro de Docker.

Se conservan los ERROR de imagen anterior ausente y del comparador inicial que exigía igualdad de binarios generados en compilaciones distintas. La corrección se ejecutó sobre la misma imagen, sin reconstrucciones especulativas. Telegram terminal PASS y limpieza confirmados; no cambios de aplicación ni nuevas métricas de request por este cierre.

Esta decisión **no activa ventas ni pagos reales y no acepta GS01, BF, BB, C ni producción**. El modo comercial sigue opt-in de desarrollo y deshabilitado en producción; precios/impuestos/condiciones definitivos, identidad/proveedores reales y revisiones jurídica/externa permanecen pendientes de producción. Continúa el objetivo completo con GS01 y su inventario de estados/contratos congelados, después BF/BB y la N3 final de C.
