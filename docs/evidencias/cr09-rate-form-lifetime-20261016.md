# CR09: liberación del formulario privado de tarifas

Fecha: 2026-10-16. Base: `1c7abb2c5ef8ec745b4aebb5974c913c3e592484`.
Ejecución: `20261016-072912-273cb6ef`. Resultado: **7 PASS**, 0 fallos, errores o exclusiones; pytest 107,36 s.

## Problema y cambio

`PublicationContext.rate_valid` sólo expone y memoiza un booleano. El formulario privado creaba el ciclo BoundField → form → caché de BoundFields. En los campos inválidos, además, ValidationError.error_list contenía el propio error; su traceback conservaba frames con una referencia al formulario. Vaciar únicamente la caché, o descartar `_errors` y `cleaned_data`, no liberaba estos frames.

Se mantiene `RateForm.is_valid()` nativo y su memoización. Un `finally` vacía la caché privada de BoundFields y retira el traceback de los errores de validación almacenados en ese formulario. No cambia validadores, restricciones, errores de formularios de edición ni excepciones propagadas. No se desactiva ni se configura globalmente el GC.

## Diagnóstico y verificación

La sonda local `artifacts/cr09-rate-error-retention-20261016/probe.py` observa el mecanismo de `_clean_fields`, sin validación de modelo ni SQL. Para concepto y duración inválidos comprueba por identidad el error dentro de su propia lista y referencias directas al formulario desde frames. Sin retirar traceback se retiene; retirándolo se libera antes del GC. No es una validación integrada. Su primera versión `full_clean` se detuvo en la barrera de ejecución SQL al intentar una restricción; se preservó y se redujo al mecanismo de campos.

La verificación integrada posterior usa PostgreSQL real propio y fixtures sintéticas: cinco casos de paridad con RateForm nativo, liberación inmediata con GC desactivado sólo dentro del test y memoización; un caso de excepción propagada sin memoizar; un prototipo WSGI de listado ES y búsqueda EN con cuerpos iguales a los nativos, respuesta 200 y no-store. Este último combina la corrección con limpieza experimental de modelos y contexto: **no prueba que RateForm solo libere todos los modelos**.

| Evidencia | Antes | Después |
|---|---:|---:|
| Controles RateForm | 4 PASS / 2 FAIL (072242) | 6 PASS / 0 FAIL |
| Listing / Revision retenidos con prototipo completo, por ruta | 0 / 0 (072242) | 0 / 0 |
| Objetos SAVEALL del prototipo, ES / EN | 659 / 660 (072242) | 659 / 660 |
| Último p95 limpio de carga | 1,013029795 s | Sin nueva medición |

Los fallos 071945 y 072242 se conservan, con fuentes originales en sus directorios. Fuentes congeladas contrastadas independientemente con `source-hashes.json`; JUnit 7/0/0/0; procesos identificados por PID/start_ticks terminados, temporal ausente, ambos contenedores ausentes y cgroup vacío. Se mantuvieron límites del controlador 4 CPU/3584 MiB y PostgreSQL propio 1 CPU/1536 MiB. Dependencias bloqueadas, Python 3.12.15 y kernel native-sealed del runner habitual.

## Investigación comunitaria y límites

Stack Overflow aportó la hipótesis concreta de retención por excepciones y frames: [caso con explicación y respuesta del autor](https://stackoverflow.com/questions/71272721/why-does-creating-a-variable-name-for-an-exception-raised-in-a-python-function-a). Se contrastó con la [referencia de Python 3.12 sobre except](https://docs.python.org/3.12/reference/compound_stmts.html#except-clause), la [API de errores de formularios](https://docs.djangoproject.com/en/5.2/ref/forms/api/) y el código instalado de Django 5.2.17. La evidencia aplicable al proyecto son las identidades observadas y los tests locales, no la aceptación comunitaria de una respuesta.

No hay ahorro temporal demostrado, nueva carga limpia ni aceptación N3. Los prototipos de contexto/render y cachés de modelos siguen sólo en tests; necesitan comprobar precedencia de contexto, procesadores, includes, excepciones y ciclo de vida antes de integrar, y después demostrar ROI. CR09 y el resto del contrato continúan abiertos. Sin producción, proveedores ni invocaciones Claude nuevas.
