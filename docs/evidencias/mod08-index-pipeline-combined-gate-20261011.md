# MOD-08: verificación conjunta del pipeline y HMAC adaptativo

Integración e5e531c, ejecución 20261011-063647-2425f04d. PostgreSQL real; 38 pruebas pasan sin fallos, errores ni omisiones. Verificados independientemente 1156 hashes y retirada de contenedores propios.

| Verificación | Pipeline aislado | HMAC aislado | Conjunto |
|---|---:|---:|---:|
| Pruebas aprobadas | 79 | 31 | 38 |
| Fallos / errores / omisiones | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

Las selecciones difieren; sus cantidades no expresan rendimiento ni cobertura equivalente. El conjunto verifica auditoría física de cuatro páginas con runtime enforced, corrupción tardía con rollback y sellos de validación con replay/tamper.

No acredita todavía reducción del request. La próxima captura/use debe congelar ambas optimizaciones; objetivos completos de dos casos, N3, navegación p95 ≤2s y descarga p95 ≤5s siguen pendientes. SQL execute wrappers no incluyen el tiempo de pipeline.sync; comparar relojes TCP/WSGI completos.
