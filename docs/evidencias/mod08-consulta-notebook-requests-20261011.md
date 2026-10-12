# MOD-08: consulta al cuaderno sobre latencia de requests

Fecha: 2026-10-11. Consulta solicitada por el usuario al cuaderno `web_citas — Arquitectura integral`,100fuentes. **Propuesta de tercero, no evidencia de rendimiento ni aceptación técnica.** Desarrollo pausado: no se han ejecutado mediciones, cambiado producto ni contratado servicios.

## Resultado revisado por Codex

El cuaderno no ha demostrado una solución que cierre las brechas de navegación3,753392→2s ni descargas JSON6,930455/binaria7,317947→5s. Su primera respuesta propuso reutilizar descifrado, reducir materialización ORM y consolidar validaciones de cadena. Las redundancias y ahorros no quedaron demostrados. Codex contrastó funciones y configuración locales y solicitó corrección.

Errores retirados: atribuir `unseal` a `validate_approved_assessment` (recibe `body`); atribuir `orjson` a `crypto.unseal` (usa `json.loads`); multiplicar duración exclusiva agregada para proyectar ahorro; confundir16MiB de población de expediente con ciphertext de una fila; equiparar `atomic` con `REPEATABLE READ` o bloqueo del expediente con inmutabilidad de usuarios/grants/pruebas; dar por segura memo de autoridad/cadena; presentar py-spy sin overhead y como medición causal de syscalls; descartar definitivamente mejoras o throttling mediante umbrales arbitrarios. No se aceptan estimaciones0,15–0,50s de la primera respuesta.

Recomendación que queda como hipótesis de diagnóstico: desglosar **validate_assessment/source**, por llamada del mismo request/ciclo, distinguiendo conteos y bytes ORM/fetch/adaptación, descifrado/parseo, ejecuciónSQL/bloqueos y `pipeline.sync`, wall/threadCPU exclusivo y solapamientos. Relacionar el coste observado con una candidata concreta y demostrar conservación de autoridad, revocaciones, auditoría, snapshots y rollback antes de aplicar. Consultas textualmente iguales no prueban redundancia: pueden observar cambios o registrar pasos contractuales distintos.

La respuesta corregida sigue siendo una propuesta: no acredita que todos esos contadores existan hoy. `tests/capacity_phase_spans.py` y `tests/capacity_profile_wsgi.py` son puntos de instrumentación citados; extenderla/reanudar requiere trabajo posterior autorizado. No declarar ausencia universal de margen seguro si una medición no identifica una redundancia concreta. Los perfiles de ciclos anteriores no se suman ni se comparan como si pertenecieran a la misma petición. Citas del cuaderno deben contrastarse con código: Graphify aporta navegación, no prueba de seguridad.

## Respuestas conservadas

- [Consulta inicial, pregunta, respuesta y referencias](mod08-consulta-notebook-inicial-20261011.json).
- [Consulta correctiva, pregunta, respuesta y referencias](mod08-consulta-notebook-correctiva-20261011.json).
- [Relevo y estado medido](mod08-relevo-pausa-20261011.md).

## Texto del cuaderno tras las correcciones

El texto siguiente se conserva como respuesta de tercero, con referencias numéricas resolubles en el JSON correctivo. Sus afirmaciones no sustituyen revisión local.

**Correcciones asumidas:**

1. **Flujo y desencriptación:** `validate_approved_assessment` [1, 2] y `validate_approved_selection` [3] emplean `latest.only("pk")` y validan la evidencia de evaluación sin llamar a `unseal` [1, 3]. `crypto.unseal` usa `json.loads` (no `orjson`) [4]. Los 16 MiB constituyen la cota superior del expediente completo [5], no el tamaño individual de cada ciphertext.
2. **Aislamiento y frescura:** `DATABASES` no impone aislamiento `REPEATABLE READ` por defecto. `atomic` no implica dicho nivel ni inmoviliza `User` u otorgamientos al bloquear `RightsRequest` [6, 7]. Asimismo, `REPEATABLE READ` no detecta revocaciones posteriores al snapshot [8]. Se retira la propuesta de memo/cadena de autoridad al no ser técnicamente segura.
3. **Cómputo e interpolación de métricas:** Los .161807 s representan la duración exclusiva agregada de la fase `unseal` para esa solicitud específica [9]; no se puede multiplicar para estimar ahorros ni justifica cotas proyectadas (.250–.500 s / .100–.200 s). No hay evidencia para afirmar categóricamente la inalcanzabilidad de metas. ProfileID 187 pertenece a un ciclo anterior.
4. **Herramientas de perfilado:** `py-spy` no está instalado, no tiene overhead cero ni mide por sí solo la duración de llamadas de red. Los contadores agregados sin intervalos de cgroups no descartan throttling [10], ni descartan mejoras en Python si I/O ocupa el 65%.
5. **Instrumentación:** `tests/capacity_request_timing.py` es un módulo de instrumentación [9], no un runner ejecutable de control.

---

### Diagnóstico finito seleccionado (instrumentos existentes)

Se selecciona **descomponer la fase `validate_assessment` / `source` dentro del mismo request/ciclo de medición**, aprovechando la instrumentación de `tests/capacity_phase_spans.py` [11] y `tests/capacity_profile_wsgi.py` [12] (con encabezado `X-Capacity-Profile: coverage_page_read` [12, 13]):

1. **Descomposición por llamada:** Desglosar ejecuciones de `validate_approved_assessment` [1], `source_copy` [11, 14] y `validate_assessment_evidence` [1, 15].
2. **Materialización y parseo:** Registrar número de llamadas, bytes materializados desde Postgres, conteo de ejecuciones y bytes procesados por `crypto.unseal` [9, 11].
3. **Métricas PG y Pipeline:** Capturar `sql_count`, `sql_wall_ns` y `sql_thread_cpu_ns` [9], junto con los tiempos de espera asociados a `_source_rows_pipeline` y `pipeline.sync` [16].
4. **Límites de medición:** Medir métricas exclusive wall/thread CPU en el contexto exacto del mismo request sin alterar el pipeline.

---

### Criterio de evidencia para justificar una candidata productiva

* **Verificación local (constatada):** La frescura de autoridad exige verificar activamente a la entidad (`fresh_authority` / `User.objects.get`) en la base de datos [17, 18].
* **Hipótesis:** Se hipotetiza que existen reevaluaciones SQL idénticas o redundantes dentro del mismo bloque transaccional que no aportan verificación de frescura adicional.
* **Evidencia requerida:** Para proponer un cambio en producción, la instrumentación debe demostrar empíricamente que se ejecutan consultas Postgres idénticas sobre datos inmutables dentro del mismo snapshot, y que su consolidación reduce `exclusive_wall_ns` [9] sin cachear credenciales ni omitir la validación de revocaciones.

*Si la medición demuestra que no existe redundancia útil y que cada consulta es indispensable para garantizar frescura o auditoría, se declarará formalmente que no hay margen de optimización segura.*

---

¿Deseas que preparemos la configuración de los encabezados de diagnóstico para capturar las métricas de este request específico?
