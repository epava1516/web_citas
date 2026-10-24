# B07 — Integración HTTP de política y filtros checked

B07-283 auditado: dos casos PASS/226,406sJUnit,210solicitudes TCP y210lecturas nativas de referencia normal/PRODUCTIONchecked100. Fuentes1705, producto628, limpieza y Telegram verificados; compactación y reactivación del mismo objetivo confirmadas. Integración local sin capacidad ni proveedor real; B07 abierto, ocho de18.

## Necesidad y límite

La [conciliación241](241-conciliacion-cierre-b07-20261023.md) deja pendiente el contraste HTTP pertinente de política. El [coste281](244-coste-politica-production-checked-b07-20261023.md) ya acredita210observaciones1470lecturas locales, no TCP. La guarda de capacity_beta_http exige no producción, cuota propia y promociones: no relajarla para acomodar esta prueba sin promociones. Usar integración separada que conserva el escenario normal/PRODUCTION de244.

Consulta del grafo324 antes de analizar: BFS98nodos,25mostrados por presupuesto1000; resultado truncado y contrastado con241,244, contrato16§16, referencia y servidor. No auditoría exhaustiva. El escenario nuevo no reemplaza262/265 ni convierte277INVALID en válido.279 no reprodujo su causa; se conserva como diagnóstico.

## Instrumento282

`tests/beta_policy_checked_http_integration.py` llama a la función de referencia `test_production_checked_combined_equivalence` sin modificar su fuente. Mismos100perfiles70/30, procedimiento sintético incompleto en20, sin derechos promocionales, tres fases fresh/pending/repaired, cuatro selecciones checked con semánticaOR y ESEN.114páginas normales y96PRODUCTION. No repetir coste, cinco controles o diagnóstico de generador.

Al primer GET, iniciar LiveServerThread de Django sobre127.0.0.1/puerto efímero, WSGI y middleware reales, conexiones PostgreSQL propias de las solicitudes. Configuración compartida del mismo proceso; la observación en el handler comprueba hilo distinto, misma base, política del modo, proveedor synthetic-policy-fixture.invalid y PROMOTION_TEST_MODEFalse. PRODUCTION describe política de elegibilidad, no una configuración de despliegue ni proveedor de verificación. No Gunicorn/Caddy/cuotas8CPU/Redisworker/capacidad grande.

Por página se realiza un GET real TCP sin proxy ni seguimiento de redirecciones y timeout65s. Exigir200, no-store, IDs de tarjetas ordenados sin duplicados, recuento HTML y ausencia de patrocinio. Esa firma coincide con la respuesta de DjangoClient que la referencia original compara a su vez con autoridad nativa independiente. Se mantienen los controles originales de exclusión fuera de primera página, generación pendiente sin reparación por lectura y reparación manual. Así cada página TCP tiene paridad nativa transitiva; HTTP no se usa como autoridad de elegibilidad.210GET TCP y210GET client, no1470lecturas ni comparación causal.

Tiempo de pared alrededor de apertura/lectura HTTP; parsing y oráculo fuera. Medición descriptiva serial, sin percentilesSLO ni CPU por servicio. No imágenes, uploads, carga concurrente, ráfaga, proveedor real o ejecución de worker. Al terminar cada modo, detener y unir hilo propietario y comprobar socket cerrado. Conservar fuentes, huella de referencia, reportes JSON por modo y propiedadesJUnit equivalentes.

## Ejecución283 prevista

Runner oficial focal, PostgreSQL17/Redis7.4, librdb nativo y snapshots, un workerpytest, broker aislado, timeout1200. Comando previsto: `.venv/bin/python scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --workers 1 --fixture-snapshots --isolate-test-broker --test tests/beta_policy_checked_http_integration.py --timeout 1200`.

Antes: Ruff, AST y semántica dirigidos; freeze completo y protocolo originalbytes; helpers persistentes con identidades y recibos comprobados. Misma política de pausa, compactación y reactivación del objetivo. No lanzar hasta completar preparativos. Estimación de varios minutos más preparación, no extrapolación lineal desde414,401s de281. No ampliación automática del watchdog ni de población.

Después: auditar fuentes prerregistro/lanzamiento/CI/árbol antes de editar;628producto y referencia244 intactos; dos casos noSKIP, reportesJUnit/JSON iguales,114+96páginas y210handlerobservations; fases/filtros/idiomas/recuentos, paridad, socket/hilo cerrado; PGRedis/build reales, limpieza Docker/PID/temporales, Telegram, compactación y autoresume. Conservar negativos antes de corregir. Una integración válida no acepta capacidad ni cierra B07: documentar matriz y límites antes de decidir trabajo siguiente, sin repetir cargas ya válidas ni cambiar CPU/GC/workers sin hipótesis demostrada.


## Resultado283 auditado

Corrida `20261023-083154-a73c2eaf`:2PASS/226,406sJUnit. Auditoría `artifacts/beta-promotion-fix-20261020/policy283-audit.json`, clasificación VERIFIED_POLICY_CHECKED_HTTP100_INTEGRATION_NOT_CAPACITY. Se compararon1.705fuentes prerregistro/lanzamiento/CI/árbol y protocolo original byte a byte antes de levantar la congelación.628fuentes de producto y referencia244 intactas. PostgreSQL17/Redis7.4/build nativos, pasos terminados con0; contenedores, procesos propietarios y temporal ausentes; avisos global/terminal/reactivación enviados. Compactación REQUEST_ACKNOWLEDGED, mismo objetivo reactivado sin crear otro y preservando consumo.

114solicitudes normales y96PRODUCTION:210TCP más210DjangoClient; reportesJSON coinciden con propiedadesJUnit. Cada respuesta conserva firma de IDs ordenados/recuento/patrocinio y el contraste nativo original, fases fresh/pending/repaired, checkedOR, ESEN, generación pendiente sin reparación por lectura y reparación manual. Handler de hilo distinto acredita modo y basePostgreSQL compartida; hilo terminado/socket cerrado en ambos casos. Medianas HTTP seriales descriptivas339,612ms normal y381,132ms PRODUCTION; no percentiles de carga ni comparación causal con281.

Decisión: integración pertinente de política satisfecha en este fixture100, sin extrapolar a capacidad grande, desplieguePRODUCTION o proveedor externo. No repetir262/265/268–271 ya válidos ni escalar1000/10000 automáticamente.277 permanece INVALID por p99generador32,880ms;279 no lo reprodujo ni acredita su causa. Conciliar la matriz241/214 con este resultado antes de decidir el siguiente cambio justificado. Sin aceptación B07/global.
