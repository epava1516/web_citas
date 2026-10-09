# Preparación de orígenes Redis RDB/AOF

Estado: entrega técnica cerrada localmente; no cierre de CR09. Contrato: [extensión por inventario](contratos/10-denuncias-derechos.md#extensión-rdbaof-por-inventario--entrega-local). Próxima acción y procesos únicamente en [seguimiento17](17-seguimiento-desarrollo.md).

## Herramienta de operador

Usar el proyecto oficial [redis/librdb](https://github.com/redis/librdb/tree/v2.4.0), MIT, fuera de Django y de las peticiones web. Fuente fijada:bc5f295c98b40c2c33099d9d72ab30ce9e595dc7; hiredis:869f3d0ef1513dd0258ad7190c9914df16dcc4a4. Una compilación tiene su propia huella binaria; no prometer hash idéntico con otro compilador/plataforma.

Ejemplo reproducible de selección de fuentes en un directorio nuevo propiedad del operador:

```bash
git clone --branch v2.4.0 --recurse-submodules https://github.com/redis/librdb.git /ruta/privada/librdb
git -C /ruta/privada/librdb rev-parse HEAD
git -C /ruta/privada/librdb submodule status
make -C /ruta/privada/librdb -j2
chmod 755 /ruta/privada/librdb/bin/rdb-cli
sha256sum /ruta/privada/librdb/bin/rdb-cli
```

Comprobar exactamente ambos commits antes de utilizar el resultado; conservar versión del compilador/plataforma y huella observada junto al acta del operador. El hash esperado pasado al comando debe proceder de esa comprobación, nunca de la entrada cifrada que se pretende aceptar. No ejecutar ejemplos con rutas públicas ni herramientas proporcionadas por solicitantes. No recompilar rutinariamente si fuentes/binario y entorno siguen válidos.

```bash
python -m scripts.scope_retained_redis_origin \
  --origin /ruta/privada/captura-aof.encrypted \
  --origin /ruta/privada/captura-rdb.encrypted \
  --decoder /ruta/privada/librdb/bin/rdb-cli \
  --decoder-sha256 HUella_SHA256_VERIFICADA \
  --output-directory /ruta/privada/origenes \
  --request UUID_DEL_EXPEDIENTE \
  --inventory ID_DEL_INVENTARIO
```

Requiere entorno Django/cifrado y PostgreSQL autorizados. No poner secretos en argumentos. El inventario debe existir, pertenecer al expediente y no estar caducado/purgado. Directorio0700 y archivos0600, propietario del lector; en runtime actual UID10001. La preparación escribe un único archivo nuevo sin sobrescribir. Conservar capturas originales cifradas y sus actas; la reconstrucción no sustituye al original ni convierte el estado snapshot en historial de comandos. No ejecutar su RESP ni cargarlo en el Redis normal.

## Evidencia y pruebas

Las pruebas nativas requieren `RETAINED_RDB_DECODER_BIN` y `RETAINED_RDB_DECODER_SHA256` contrastados; su ausencia falla, no produce un skip ni un parser simulado. `tests/retained_rdb_fixture.py` lanza un Redis propio sin TCP, por socket Unix privado; toma un SAVE sintético antes de la caducidad, termina ese PID y analiza el archivo físico después de caducar. No restaura capturas históricas en un servidor ni muta/consume colas normales.

La batería funcional usa el ejecutor existente `scripts/verify_promotion_catalogue.py` con selección explícita, PostgreSQL UUID/medios propios y retirada comprobada. Sus nombres históricos no limitan su selección. Resultado terminal, huellas, preparación/migración/pytest/limpieza son automáticos; revisión del alcance y aceptación corresponden a Codex. El ensayo funcional nativo no acredita capacidad, RPO/RTO, custodia externa ni identidad jurídica.

Entrega comprobada:58 pruebas PG/nativas correctas, fuentes y limpieza verificadas; integración/runtime112 hashes en3 servicios correctos. [Informe](evidencias/redis-rdb-aof-origenes0110.json), [runtime](evidencias/redis-rdb-aof-origenes-runtime0110.json). Pendientes de fase: cobertura histórica integral, metadatos AUX/desconocidos y conservación/revisión independientes; nunca declarar completitud por contar claves o mensajes.


## Diagnóstico AUX residual — evidencia histórica

[Diagnóstico](evidencias/redis-rdb-aux-diagnostico0110.json): cinco campos AUX en snapshot y base: redis-ver, redis-bits, ctime, used-mem y aof-base. Ningún AUX desconocido en estas dos capturas; valores conservados solo cifrados y vinculados a hash/captura originales. No son originales sustitutos ni decisiones de exclusión. ctime no acredita fecha de cada mensaje ni titularidad.

La proyección JSON estándar con opciones AUX/func/stream/db-info fue rechazada por el lector estricto; salida descartada y temporales retirados. Se cambió a callbacks de la API oficial. Extractor propuesto `scripts/native/retained_rdb_aux.c`: pares hexadecimales,64 campos/4096bytes por nombre/256KiB por valor/1MiB agregado; lectura completa con CRC. Su primer intento mezclaba el logger predeterminado con stdout, también rechazado; corregido mediante logger silencioso y retorno de error. Nunca aceptar stdout parcial ante exit distinto de0.

Compilar con fuentes/bibliotecas fijadas y verificar la huella del resultado:

```bash
cc -std=c99 -Wall -Wextra -Werror -fstack-protector-all \
  -I /ruta/privada/librdb/api scripts/native/retained_rdb_aux.c \
  /ruta/privada/librdb/lib/librdb-ext.a /ruta/privada/librdb/lib/librdb.a \
  -o /ruta/privada/retained-rdb-aux
```

Estado durante el diagnóstico: extractor de operador en desarrollo, fuera de HTTP/servicios normales. Su integración posterior queda acreditada abajo. Diagnóstico ejecutado con cwd privado, límites/no-new-privileges/timeout del wrapper existente. Dos capturas conservadas del entorno sintético y fixture oficial con corrupción CRC comprobadas; no N2 ni entrega nueva aceptada. En ese corte estaban pendientes funciones/módulos/metadatos adicionales y revisión por inventario; esta última se entregó posteriormente. El resultado funcional de integración posterior está entregado abajo; no repetir este diagnóstico ni tratarlo como cola vigente. Metadatos no AUX/desconocidos y cobertura integral pendientes.


## Preparación reproducible del entorno de pruebas

[prepare_native_test_tools.py](../scripts/prepare_native_test_tools.py) comprueba los commits fijados de librdb e hiredis, reconstruye el parser y los dos collectors, aplica0755 y registra sus huellas en `manifest.json`. Requiere un checkout desechable: ejecuta `make clean`; no usar una carpeta con trabajo propio. El archivo de variables usa formato GitHub Actions, no se interpreta como código shell.

```bash
uv run python scripts/prepare_native_test_tools.py \
  --source /ruta/desechable/librdb \
  --output /ruta/desechable/binarios \
  --env-file /ruta/desechable/native.env
```

Las seis variables `RETAINED_RDB_*_BIN`/`RETAINED_RDB_*_SHA256` del manifest deben estar en el entorno de pytest. El workflow prepara estos requisitos, PostgreSQL con nombre `promotion_gate_ci`, Redis y Chromium antes de pytest. Esa configuración no acredita una ejecución externa de CI. La omisión de las tareas MOD05 sin argumentos en el adaptador de colas se corrigió durante el saneamiento2026-10-09; los mensajes con argumentos o envelopes desconocidos mantienen el rechazo.

## Preparación integrada AUX — entrega local

Una vez contrastados código/bibliotecas, hash del binario y propietario, instalar el collector con0755 (umask de este host puede producir0776; ese permiso se rechaza). Usar las opciones `--aux-decoder /ruta/privada/retained-rdb-aux --aux-decoder-sha256 HUELLA_VERIFICADA` junto al comando por inventario. Cifrado de AUX dentro del nuevo origen RDBv2; no usar el archivo de diagnóstico como origen completo ni copiar datos a medios públicos. El proceso web solo lee/valida el archivo preparado.

La inspección privada propone huella `redis_metadata_digest` con estado pending. El operador debe motivar su evaluación y conservar esa huella exacta; después se aplica la revisión independiente existente. Un campo técnico reconocido no autoriza entregar valores globales ni excluir los desconocidos. Campos repetidos mantienen referencias distintas; la vista por expediente muestra huellas y tamaños opacos. Valores completos solo en el origen cifrado de operador, sin atribuirlos a una persona ni mostrar valores globales/posibles capacidades a quien solo revisa ese expediente. No interpretar ni ejecutar contenido. AUX no se incorpora a `copy`, y los pendientes de metadatos/cobertura se conservan.

Las nuevas pruebas requieren además `RETAINED_RDB_AUX_BIN` y `RETAINED_RDB_AUX_SHA256` verificados. N2 incluye productor CLI/PG perfil-cuenta, huella ausente/alterada, contenido privado/paquete parcial, desconocidos y duplicados/bytes, CRC y Chromium móvil ES/EN con preparación/revisión. Cierre técnico local:27 pruebas afectadas finales correctas, runtime115 hashes/3 servicios y limpieza comprobados; [informe](evidencias/redis-rdb-aux-integrado0110.json), [runtime](evidencias/redis-rdb-aux-runtime0110.json). Runs inicial/final separados, sin batería75 falsa; no capacidad ni aceptación jurídica.

## Censo físico no AUX por inventario

Extensión del recurso/revisión existentes, sin nuevas familias, modelos ni endpoints. Preparación de operador mediante `--metadata-decoder` y `--metadata-decoder-sha256`, ambos obligatorios juntos. Este collector incluye AUX: no combinarlo con `--aux-decoder`. Compilar `scripts/native/retained_rdb_metadata.c` con las mismas bibliotecas/commit fijados y flags del ejemplo AUX, cambiando únicamente fuente/destino; contrastar fuente, binario, propiedad y0755 antes de usarlo. No recompilar collectors ya válidos por rutina.

El origen RDBv3 incorpora `physical_metadata` cifrado: hash de captura/objeto original, corte, bytes originales, eventos/huella y descriptor de collector. El parser comprueba CRC y el lector exige marcador terminal con consumo exactamente igual al tamaño original: CRC válido no autoriza ignorar bytes finales. Límites:64MiB de entrada,8MiB de salida,8192 eventos,4096 claves y4096bytes por nombre, más límites AUX vigentes. Contexto de base de datos, tipos enteros estrictos, claves físicas duplicadas, hash/corte/fuente y campos exactos se validan; no truncar para aceptar.

El censo recoge cabecera/base/tamaños/atributos de clave y AUX. Detecta presencia de metadatos adicionales del parser para conservar pendiente preciso, sin implementar adaptadores de formatos ausentes por hipótesis. Los eventos completos y nombres de claves permanecen en el origen cifrado del operador. La revisión por expediente solo muestra categorías, referencias, huellas y resumen técnico; no atribuye claves globales al titular. Se reutiliza `redis_metadata_digest` y la revisión independiente existente, con estado inicial pending y vínculo exacto al contenido. No incorpora estos metadatos globales a `copy` ni elimina `snapshot_metadata_scope_review`/`historical_redis_coverage`.

Pruebas nativas requieren adicionalmente `RETAINED_RDB_METADATA_BIN` y `RETAINED_RDB_METADATA_SHA256` contrastados; faltantes fallan, sin simulador. Compilación/probe son pasos internos: cierre solo tras paquete/PG/navegador afectados, integración/runtime y limpieza. Estado de aceptación y única acción operativa en seguimiento17; custodia, procedencia de namespaces, host/backups y decisiones jurídicas conservan sus gates.

Cierre técnico local comprobado:16 casos N1 nativos y7 N2 PG/CLI/paquete/Chromium ES-EN correctos sobre bedc016, runs distintos;850 huellas de integración y118 hashes en3servicios locales coincidentes, limpieza real. [Informe](evidencias/redis-rdb-physicalmeta-integrado0110.json), [runtime](evidencias/redis-rdb-physicalmeta-runtime0110.json). Los dos originales quedaron vinculados al censo validado y revisión opaca reutilizando el probe cifrado, sin repetir el parser. No censo global, N3/capacidad ni aceptación jurídica/externa. Pausa tras este cierre por solicitud del usuario; cola exclusiva en17.
