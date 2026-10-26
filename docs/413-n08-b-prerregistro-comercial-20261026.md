# N08B — prerregistro de la referencia comercial local

Estado: preparado antes de medir; no aceptación ni mejora de aplicación. N08 sigue abierto, con 7/13 bloques obligatorios aceptados. Base `0d7a3a3bac080cd38785672a009c39e00fb7e64c`; corte previo de 2.028 fuentes sin diferencias y grafo SHA256 `82b338ede064ff0cf77b0c35b47925bf39cd4569e60148cc09519738a62b4c80`.

Continúa [el contrato](340-contrato-recorridos-optimizacion-alpha-20261025.md) y conserva los resultados de [N08A2](412-n08-a2-resultado-contraste-por-lotes-20261026.md). No repite las pruebas válidas ni introduce un candidato de optimización. Los tiempos alfa actuales son aceptables: sólo una mejora claramente justificada permitiría otro contraste; las ganancias marginales se posponen al final del desarrollo.

## Alcance y ejes independientes

Se cubren `route:R_promotion_orders`, `route:R_promotion_order_detail`, `route:R_promotion_products`, `route:R_promotion_product_versions`, `route:R_promotion_version_edit` y `route:R_promotion_version_preview`. La tarea y Beat de autosubida quedan para N08C, con prerregistro independiente y sin atribuir a la ejecución eager una prueba real de worker.

1. Historial propio: 0/1/10/26/100 pedidos sintéticos, todas las páginas nativas de 25, ES y EN, una petición inicial y cinco posteriores por página y estado. Mantener exactamente un anuncio y un producto elegibles en el formulario. Un pedido de otro comprador actúa como centinela de aislamiento. Son 108 GET medidos; detalle de un pedido propio, seis GET por idioma, añade 12. Preparación de pedidos y sus intentos fuera de los relojes; no representa 100 compras ni cobros realizados.
2. Opciones del formulario, sin historial propio: variar anuncios gestionados 0/1/10/100 con un producto constante; variar productos elegibles 0/1/10/100 con un anuncio constante. Seis GET por idioma y cohorte: 96 GET. Verificar los PK de las opciones realmente ofrecidas, los nombres localizados y los centinelas ajenos o excluidos. El filtro GET de productos no equivale a toda la validación de compra; se conserva el servicio nativo que revalida al escribir.
3. Catálogo: 0/1/10/51/100 productos, todas las páginas nativas de 50, ES y EN, seis GET por página y estado: 84 GET. Versiones de un producto: 1/10/51/100, todas las páginas de 50, ambos idiomas y seis GET: 72 GET. Edición y vista previa de un borrador: seis GET por ruta e idioma, otros 24. Total del eje: 180 GET. Los importes incompletos son NULL y no se presentan como cero ni como vendibles.

Total previsto: **396 GET medidos** en tres casos nuevos explícitos. Los controles negativos y las mutaciones nativas adicionales se identificarán por separado antes de congelar las fuentes. No se suman los GET del instrumento y los mismos GET registrados por el observador global. No se repiten los 77 testigos históricos por rutina: se conciliará su identidad y alcance con los originales conservados.

## Instrumentación y oráculos

PostgreSQL desechable real del runner oficial, datos exclusivamente sintéticos, ejecución serial y sin producción. Se usan las vistas, formularios, permisos, sesiones y paginadores nativos. No sustituir autorización, ORM, servicios, relojes ni reglas de publicación. Preparación y oráculos fuera de los intervalos; las respuestas se materializan dentro.

Registrar por petición: pared, CPU del proceso, llamadas de cursor y tiempo acumulado mediante `connection.execute_wrapper`, bytes, estado, ruta, idioma y cabeceras privadas. No usar `CaptureQueriesContext` ni su búfer circular como contador. Separar la primera observación de la mediana y rango de las cinco posteriores, por eje, cohorte, idioma y página. La CPU no incluye PostgreSQL; los tiempos son del Client y no latencia de red, navegador, p95, SLA ni capacidad de producción.

Los oráculos comprueban orden e identidad de filas, total y páginas, aislamiento de comprador, opciones esperadas, idioma efectivo, avisos de simulación y ausencia de venta habilitada. Un resumen de todos los campos escalares de los modelos comerciales antes y después de cada segmento verifica que los GET no mutan el dominio; no exportar valores de sujetos ni secretos. Los controles de escritura se miden sólo como observaciones individuales de operaciones distintas, sin agregarlas a una falsa distribución de reintentos equivalentes.

Revisar el instrumento con `django-expert` y `django-reviewer`, acotado a los archivos propios. MCP Django dummy no acredita esquema aplicado; los MCP nuevos no expuestos en esta sesión no se presentan como utilizados. No conectar PostgreSQL MCP con credenciales descubiertas, ejecutar migraciones ni cambiar servicios.

## Congelación, ejecución y aceptación

Antes de ejecutar: revisar propuestas aisladas, concretar controles adicionales, refrescar AST de fuentes nuevas y semántica de este documento/seguimiento, comprobar el grafo, congelar fuentes y registrar selección exacta. Usar runner oficial con observador HTTP y notificación terminal Telegram, comprobar recibo y limpieza. Si el instrumento falla, conservar el resultado original y repetir sólo el alcance invalidado después de una corrección justificada.

Resultado posterior: tabla por segmento con tiempos anteriores y posteriores cuando exista un par causal; sin candidato, consignar referencia actual y posterior no medido, sin porcentaje de mejora inventado. N08 sólo se acepta tras conciliar sus 17 identificadores y el frente N08C. No abrir beta, activar proveedores ni ampliar el contrato.
