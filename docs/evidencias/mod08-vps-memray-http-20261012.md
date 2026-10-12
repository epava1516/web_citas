# MOD-08 — Memray real aislado, sonda y fallos preservados

[Resumen verificable](mod08-vps-memray-http-20261012.json). No capacidad/HTTPp95.
Aplicación contiene corrección de copias a41d31b. Instrumentos84f1886; corrección
de reconexión sólo en hijo de sonda d6e2ac5.

| ID | SHA | Test | Duración test(s) | Salida controlador | Resultado |
|---|---|---|---:|---:|---|
| 20261012-074830-8ad5794e | 84f1886 | No arrancó | — | 125 | INVALID_CONTROLLER_NO_REPORT |
| 20261012-075119-58515115 | 84f1886 | 1FAIL | 41.251 | 1 | ERROR |
| 20261012-075605-67e9ac5d | d6e2ac5 | 1PASS | 50.115 | 1 | PROFESSIONAL_INSTRUMENT_PROBE_NOT_CAPACITY |

Primera ejecución: imágenesapp/PG/RustFS faltaban en estadoactual, sin atribuir
causa a terceros. Reposición PG/RustFS mantiene IDsoriginales; Redis/Caddyiguales.
App recompilada ecb4b179802ddef908a86d0379dcb8022fbbf20756d35c2de7ee92be33c0d9b4
frente a fb009e0c anterior. Bases Python y uv tienen mismos digest exactos en ambos
logs build; uv.lock y appdeps originales. Contexto Docker excluye artifacts/.env/
.ai/venv/media. No servicio existente reiniciado. latest estaba ausente; queda
asociado temporalmente a appprueba, retirar al finalizar sólo si siguepropio.

Segundo fallo: close_old_connections conserva conexión sana con su máximoactual;
la sonda nativa ya fuerza CONN_MAX_AGE=0. Se aplica lo mismo al hijo profesional.
No cambio a conexión de negocio. Primer script auxiliar de auditancia de ausencia
rechazó textoDocker minúsculo no such volume; se normalizó y confirmó ausencia
real de8recursos del fallo temprano. Fallos y XML previos intactos.

Tercera ejecución prueba realmente reconexión PGrol capacity_runtime y
Gunicorn GET /health/200 con Memray nativo. Ambas capturas COMPLETE, sin errores,
CPU positiva y trazas temporales retiradas después de resumen. Python3.12.15,
cryptography50.0.2,numpy2.5.3,orjson3.13.0 desde appsite original; Memray1.20.0
desde venv separado readonly. No py-spy, observadorSQL ni perfiles heredados.
Se conserva presencia/hash/longitud de stderrMemray del hijo sin texto privado.

El launcher final termina1 porque faltaba el nuevo estado en la lista de éxitos
del controlador: defecto de interfaz, no fallo del test ni prueba de aceptación.
Fuentes1414intactas y cleanup real auditado; memoria1116663808bytes<6GiB,
sin fallos del archivo. La lista se corrige conservando el resultado histórico.
Repetición de sonda tras corrección pendiente; sólo luego diagnoseMemray separado
para dos capturas cobertura temprana/tardía. No cadena de ensayos de rendimiento.
