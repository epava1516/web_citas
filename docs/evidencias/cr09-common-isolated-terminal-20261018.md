# CR09 — regresión común aislada, resultado terminal

Ejecución `20261017-034016-24fb3d1b`, SHA `ad12d29a4520e3e1f2fdad49e77d98ebeba7a6a9`. Resultado del controlador: ERROR; pytest terminó con código 1.

3.631 casos distintos: 3.444 aprobados completos, 57 casos con error y 130 omitidos. Los errores corresponden a 55 preparaciones de RustFS mediante Docker (salida 125) y dos limpiezas de fixtures: alias de base de datos `normal_database` y cursor sustituido por un gestor de contexto. Las causas de los errores Docker aún requieren diagnóstico; no se declaran defectos de producto por estos mensajes. El JSON asociado conserva cada error y omisión con su fase.

Verificación posterior: fuentes idénticas al manifiesto; directorio temporal eliminado; procesos principal y pytest ausentes o PID reutilizado; contenedores propios PostgreSQL y Redis ausentes. No se reinició la batería ni se modificaron fuentes durante su ejecución.

Antes del diagnóstico se refrescó el grafo AST de cinco archivos, con recibo en `artifacts/graphify-regression-diagnosis-20261018/receipt.json`. No es una actualización semántica completa. El intento posterior de agrupamiento mediante CLI falló antes de extracción por backend semántico no configurado; no se contrató ni invocó ningún proveedor.

CR09 continúa abierto. Este resultado no acepta las omisiones ni acredita rendimiento contractual.
