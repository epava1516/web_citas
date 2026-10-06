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
