# Entrega Docker con compilación nativa aislada

Se corrige un desfase comprobado: la imagen usaba Python 3.12 flotante, copiaba el artefacto nativo del host si existía y arrancaba con 2 workers/45 s frente a 4/65 s del escenario medido. No había identidad nativa actual verificada en las imágenes existentes.

`Dockerfile` fija Python 3.12.15/slim-bookworm en ambas etapas, instala dependencias con el lock existente y compila el kernel mediante el builder vigente y Cython 3.0.12 en venv separado. El compilador y Cython quedan en la etapa de construcción. `.dockerignore` excluye el artefacto del host; la etapa final recibe sólo el generado dentro de Docker y exige `native-sealed` antes de completar la construcción. El comando usa los mismos 4 workers sync/65 s del ensayo reciente; no se adopta el candidato 8sync rechazado. No hay nueva optimización de aplicación ni cambio del lock.

Construcción local terminal exit0, imagen propia **`web-modelos-cr09-native:20261016`**, ID `sha256:bb8bc8e5497cee1df2c5931d33caf171b848fbf1ec7fae1d18578d161fe4b697`, 902443487 bytes. Etiqueta revision identifica la base `3874bab`; dos archivos modificados identificados por hashes en el [recibo](cr09-docker-native-terminal-20261016.json). No representa por sí sola un commit integrado sin modificaciones. Imagen retenida para revisión; no se sustituyen etiquetas normales ni se publica.

Verificación real con contenedores efímeros y red interna, sin puertos publicados: PostgreSQL 17, migraciones completas, comando Gunicorn predeterminado y cuatro workers registrados. App con UID10001, raíz de sólo lectura, sin capacidades, no-new-privileges y tmpfs64MiB. Cuotas app2CPU/1536MiB, PG1CPU/1536MiB, swap deshabilitado y pids128 por contenedor; PGtmpfs512MiB. No se usa Redis normal: URL deliberadamente inaccesible en este smoke sin tareas. `/health/` responde200 con `status=ok` tras consultar PG real.

Runtime Python3.12.15/Django5.2.17/Gunicorn23.0.0/psycopg3.3.6/Celery5.6.3. Kernel **native-sealed**, Cython3.0.12/GCC12.2, fuente9cecbd34…, binario2caa578c…. Once entradas válidas e inválidas coinciden en éxito o clase/mensaje de error con el validador de referencia. No es la batería exhaustiva de paridad ni N3. La nueva identidad binaria puede cambiar sellos/versiones respecto al host: no se afirma equivalencia binaria ni se reutilizan autorizaciones previas entre entornos.

Fuentes seleccionadas iguales antes/después; contenedores/red y PIDs init propios ausentes, intermediarios de construcción ausentes, unidad terminalMainPID0. Logs de construcción/migraciones/Gunicorn, inspecciones y verificador en `artifacts/cr09-docker-native-20261016/`. Ruff completo y comprobación documental pasaron. No servicios normales tocados.

**Pendiente:** probar recorridos pertinentes dentro de esta imagen y medir su capacidad antes de atribuirle el p95 del host; directorio limpio/repetición/carga larga y N3 común siguen abiertos. Este smoke no cierra CR09 ni el contrato completo.
