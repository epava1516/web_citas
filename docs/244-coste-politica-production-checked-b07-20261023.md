# B07 — Coste local de política PRODUCTION y filtros checked

B07-281 auditado: dos casos PASS/414,401sJUnit con PostgreSQL17 y Redis7.4; 210observaciones y1470lecturas de coste normal/PRODUCTIONchecked100. Fuentes1704, producto628, referencia244, limpieza y Telegram verificados; compactación y reactivación automática del mismo objetivo confirmadas. Diagnóstico local, sin proveedor real ni aceptación B07.

## Pregunta y referencia

[Conciliación241](241-conciliacion-cierre-b07-20261023.md) exige completar el coste de la rama PRODUCTION/checked. [Equivalencia244](216-equivalencia-local-production-checked-b07-20261022.md) ya verifica dos modos,100perfiles70/30, tres fases fresh/pending/repaired, cuatro selecciones checked y ESEN, con114páginas normales y96producción. No repetirla como prueba aislada: el nuevo instrumento llama a su función original y conserva todas sus aserciones, fuente y oráculo. Sin promociones en este escenario; no extrapolar al cruce con promociones ni a proveedor externo/configuración productiva.

La población se prepara con PRODUCTIONFalse y las guardas originales. Sólo después se activa la política local con proveedor synthetic-policy-fixture.invalid, procedimientos explícitos y20pruebas incompletas. Manager_version obsoleto debe retirar un perfil fuera de la primera página y conservar marca/generación hasta reparación manual. No se cambia ningún archivo de producto ni verificador de identidad/contacto.

## Instrumento280

Nuevo tests/beta_policy_checked_cost_diagnostic.py, dos casos normal/production, sólo100. Obtiene el client original después del bootstrap y envuelve sus GET de páginas combinadas. Por página: una lectura warm, cinco controles sin este observador SQL/render y una lectura instrumentada. Todas las siete firmas de IDs ordenados/recuento/patrocinio coinciden; la última respuesta se devuelve al control original, que la compara con autoridad nativa independiente. La igualdad transitiva no sustituye el oráculo por HTTP. El original comprueba que ninguna lectura repara las marcas pendientes.

Mediciones de perf_counter/process_time alrededor de client.get; aserciones de firma y oráculo fuera de esos relojes. Observación separada mediante execute_wrapper y wrapper temporal de discovery.render, restaurado después de cada lectura instrumentada. DriverSQL incluye su ámbito real; render es inclusivo y se solapa con SQL. No sumar intervalos ni inferir CPUPostgreSQL, reglas de validación, objetosORM, filasSQL o coste por servicio. Se declaran esas métricas not_measured. Sin SQLtexto/parámetros/datos reales. Cinco muestras son descriptivas y no percentilesSLO.

Esperado:114+96=210observaciones,210warm+1050controles+210instrumentadas=1470lecturas. Se archivan beta-policy-checked-cost100-normal.json y -production.json en el directorioCI, y propiedadesJUnit con el mismoJSON, huella de referencia, controles crudos y muestras SQL/render. No TCP, concurrencia, SLO, proveedor real, reparación porworker ni capacidad aceptados.

## Prerregistro281 y presupuesto

Runner oficial scripts/run_local_ci.py --profile focused --native-source /tmp/web-modelos-librdb-v2.4.0 --workers 1 --fixture-snapshots --isolate-test-broker --test tests/beta_policy_checked_cost_diagnostic.py --timeout 1200. PostgreSQL17/Redis7.4 propios reales, sin otra batería concurrente. Reutilizar condiciones normalesCI del control244, no inventar cuotas8CPU de la topología de capacidad.

La referencia244 tardó139,130sJUnit para210lecturas y preparación de dos casos. Ahora se añaden1260lecturas; no extrapolar linealmente ese total ni prometer duración. Presupuestar varios minutos largos más construcción/limpieza con watchdog1200s de pytest; un timeout se conservaERROR, no se amplía automáticamente. Primero sólo100; estimar escala desde evidencia auditada, sin ampliar1000/10000 ni carga contractual automáticamente.

Antes de lanzar: Ruff, AST y semántica dirigidos, protocolo y fuentes completos congelados, helpers y huellas verificados. Wrapper/watch/callback/compactador persistentes, cuatroPIDs/start_ticks/sesiones/argv y avisosINICIO/PREPAUSA confirmados. Se pausa el mismo objetivo durante esta espera; shell solicita compactación yreactiva automáticamente al terminar, conservando consumo, sin sondeos del modelo.

Tras terminal, antes de editar: auditar doscasos/noSKIP y JSONJUnitarchivos coincidentes,210observaciones1470lecturas, fases/filtros/idiomas/recuentos70/30/56/24yretirada69/55, firmas/coincidencia nativa/promocionesFalse/proveedorrealFalse, restauración/render/SQL y fuente de referencia intacta, fuentes prerregistro/lanzamiento/CI/árbol y producto628, protocolo originalbytes, construcciónreal/PGRedis/limpiezaDockerPIDtemporal yrecibosTelegram/compactación/autoresume. ConservarFAIL/ERROR antes de corregir; no repetir para verde.

El INVALIDHTTP277 permanece sin causa resuelta;279 no lo reprodujo y sólo acredita diagnóstico. Este frente es independiente y no acepta HTTPcombinado, B07 o beta global. Ocho18cerrados; no publicación/proveedores/datosreales/ClaudeV1 nuevos ni repetición262/265/268/269/270/271.

## Resultado281 auditado

Runner `artifacts/local-ci/20261023-081449-b061710b`: dos casos PASS,414,401sJUnit. Auditoría `artifacts/beta-promotion-fix-20261020/policy281-audit.json`: VERIFIED_POLICY_CHECKED_COST100_NOT_CAPACITY. Las1704fuentes coinciden entre prerregistro, lanzamiento, runner y árbol antes de esta actualización documental;628fuentes de producto y referencia244 sin cambios. Protocolo original conservado por bytes. Contenedores y procesos propios ausentes, temporal eliminado, avisos terminales y reactivación confirmados. Solicitud de compactación reconocida durante la pausa; contexto compactado disponible al retomar.

114observaciones normales y96PRODUCTION: cada una warm+5controles+instrumentada;1470lecturas totales. IDs ordenados, recuentos y patrocinio coinciden con el oráculo original, sin reparaciones por lectura. Medianas de controles por grupo: normal fresh164,029–180,357ms/pending219,147–236,593ms/repaired159,260–173,798ms; PRODUCTION fresh211,372–225,533ms/pending256,947–283,738ms/repaired201,492–220,951ms. SQL por lectura instrumentada: normal34 fresca/reparada y34–53pendiente; PRODUCTION42–58fresca,58–78pendiente y41–58reparada. Render inclusivo mediano por grupo37,178–48,104ms. No sumar render y SQL ni atribuir causalmente las diferencias entre modos: son grupos de páginas y políticas distintos.

El coste adicional pendiente merece revisión de las consultas y reglas concretas antes de optimizar. El instrumento no conserva textoSQL ni planes; no identifica consultas redundantes por sí solo. No ampliar escalas ni repetir cargas para obtener verde. El HTTP277 sigue INVALID y279 no acreditó causa ni aceptación. El frente HTTP con política PRODUCTION/checked y la aceptación B07 permanecen pendientes según241.
