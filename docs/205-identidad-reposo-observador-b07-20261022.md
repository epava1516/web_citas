# B07 — Identidades archivadas y ventana posterior del observador

Estado: preparación208 y calibración209 terminadas; identidad y ventana posterior verificadas en Docker real.

B07-208: manifiesto mínimo de identidad por contenedor y tres muestras idle_after implementados;63guardas y Ruff PASS. Calibración209 pequeña preregistrada para comprobar identidad archivada y deltaCPU posterior. Sin carga grande ni cierre B07;8de18.

La [calibración207](204-calibracion-observador-kernel-b07-20261022.md) conserva su resultado y límites: una muestra posterior y guardas de identidad ejecutadas, sin manifiesto mínimo de contenedores archivado. Este corte modifica sólo el instrumento, no aplicación, escenario ni cuotas. El lector guarda por rol run, nombre exacto, ID completo, PID init/startticks y cgroup ya verificados. No archiva Config/Env/argv ni Docker inspect completo. Una nueva guarda confirma que un marcador privado en Env no aparece en el manifiesto.

El observador exige tres muestras idle_after con periodo nominal0,5s y mantiene el reposo funcional de2s existente. Si no llega a obtenerlas antes de la retirada, devuelve ERROR; no acepta dos puntos fingidos ni amplía silenciosamente la espera. Mantiene rechazo de fases ausentes, cotas600s/600muestras/8MiB, topología exacta y guardas de PID/cgroup. Estas muestras permiten un intervalo CPU posterior; no memoria exclusiva, CPU por petición ni overhead causal. El proceso observador sigue fuera de8CPU/8GiB, diagnóstico funcional separado de capacidad limpia.

## Calibración209 previa

Una única funcional territorial idéntica en alcance a207:10publicados7/3,2derechos,18slots14URLs/18sondas200,60dinámicas20porcategoría30poridioma en3s y1upload302persistido. Imagen inmutable5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede, cuotas8CPU8GiBswap0 y memoria/storage originales;4Gunicornsync/unhilo, worker y Beat propios, GC intacto y alineación+5s. Congelar fuentes/protocolo/mapa antes de lanzar;628producto iguales y artefactos207 rehash verificados. Sin otra batería durante ejecución, estimación2–4min.

Criterios además de los de207: seis identidades únicas archivadas con nombres/run/IDs/cgroup/PID/startticks exactos; cada init observado conserva identidad en sus muestras; tres muestras finales completas dentro de idle_after y separadas por tiempos crecientes, intervalo CPU posterior positivo con contadores no decrecientes. Mantener ventana de carga y ledger conciliados, cuotas, controles de generador, upload, GC/Beat y limpieza fresca, mapa/protocolo original y Telegram. El manifiesto mínimo no prueba por sí solo ownership: su guarda debe haberse ejecutado en las fuentes exactas. No cambiar conclusiones de207 ni sumar ambas como una sola candidata.

```bash
.venv/bin/python scripts/run_notified.py --name 'B07 calibración identidad reposo209' -- .venv/bin/python scripts/run_vps_capacity.py beta-http-functional --territorial --service-resources --cpu-budget 8 --app-image sha256:5a0751c176d10434058efea920237a207b0c4c22b6d8c4655d47ce216506aede
```

Auditar después de terminal real y antes de editar protocolo. Conservar cualquier ERROR/FAIL sin repetir TCP automáticamente. Sin short/900 ni aceptación B07. Estados/backlog/edad de colas/PRODUCTIONchecked y recursos a escala siguen pendientes en [matriz180](180-matriz-cobertura-b07-censo-geografico-20261021.md).

## Resultado209

B07-209: identidad y reposo del observador auditados 1PASS/92,221sJUnit; seis identidades mínimas archivadas y70muestras completas62previas/5carga/3posteriores, deltaCPU posterior≈1,04s.10publicados7/3 y2derechos,60éxitos/1upload,628producto y limpieza confirmados. Diagnóstico host separado; sin capacidad grande ni cierre B07,8de18.

Corrida `20261022-004759-9c053c74`, entorno VPS `20261022-004759-5446b8a9`. [Auditoría terminal](evidencias/b07-resources209-identity-idle-20261022-audit.json). Protocolo original/mapa congelado conservados, fuentes verificadas antes de esta actualización. Prerrequisito confirma delta de instrumento únicamente en scripts/benchmark_capacity_resources.py y su prueba frente207; artefactos207 rehash intactos.63guardasPASS y RuffPASS separados del caso integrado1PASS/0FAIL/0ERROR/0SKIP. No se suman como una ejecución64casos.

Manifiesto de seis IDs y PID/startticks únicos, nombres/run/cgroup exactos; cada init conserva identidad en todas las muestras.70muestras completamente dentro de fase62/5/3. CPU por intervalos entre muestras: carga≈2,05s, app≈2,026cores y PostgreSQL≈0,687cores; reposo≈1,04s, app≈0,0333cores y PostgreSQL≈0,000154cores. Son intervalos parciales por servicio, no toda la carga, CPU por petición ni inferencia causal. Sin edad de colas ni backlog medidos.

60dinámicas20porcategoría30poridioma,18slots14URLs/18sondas200 y1uploadpersistido; generador p95/p99/máximo2,519/6,501/6,501ms.8CPU8GiBswap0, memoria superior runtime1344958464bytes/storage4865392640bytes;4Gunicornsync/1hilo, GC y Beat/worker nativos vigentes. El hilo observador consume1,795sCPU/172,592s de vida completa, RSS de proceso host23576576bytes al cierre (no pico ni exclusivo); permanece fuera del presupuesto del runtime, medición instrumentada funcional.

Salida real del launcher verificada por PID/startticks, inspección fresca sin contenedores/redes/volúmenes de esa etiqueta y recibos Telegram confirmados. No repetición TCP ni fallo de auditor en209.207y209 acreditan sus cortes individuales; no se extrapolan ni se combinan como candidata grande. Siguiente frente: estados/backlog y edad de colas, antes de ampliar el escenario de recursos.
