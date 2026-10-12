# MOD-08 — procedimiento VPS probado localmente, 2026-10-12

Se prueba el instalador fijado y el lanzador final antes de subir los cambios.
No se ha instalado, medido ni desplegado nada en un servidor remoto.

Preflight inicial 20261011-235113-86a278c8: READY_NOT_CAPACITY y limpieza.
Primera carga 20261011-235314-306d68b9: ERROR, 1 fallo en 931,109 s.
Los tiempos recogidos cumplían, pero `Observed app process survived teardown`
invalidó el test. La desaparición de los recursos Docker sí se verificó. No se
conocen el PID ni el estado del superviviente de esa ejecución; no afirmar que
está demostrado que era un zombi o una reutilización de PID.

Se aplica el [init estándar de Docker](https://docs.docker.com/engine/containers/multi-service_container/)
al contenedor propio de aplicación, dentro de sus mismas cuotas, y una espera
máxima de cinco segundos para recoger procesos observados. Se rechazan también
zombis no recogidos; no se oculta la comprobación ni se instala un init artesanal.
No cambios de negocio, permisos, datos ni umbrales. No modificación del despliegue.

Preflight correctivo 20261012-001127-82f49a58: READY_NOT_CAPACITY y limpieza.
Repetición completa 20261012-001431-53a220c0: 1 PASS en 909,989 s,
cero fallos/errores/skips, servidor salida 0 y retirada verificada. Init=true y
PID 1 docker-init comprobados durante el recorrido. Auditoría independiente:
1.411 huellas exactas antes de documentación.

| p95 máximo entre dos casos | Milisegundos | Segundos | Límite (s) |
| --- | ---: | ---: | ---: |
| Navegación | 1611,558 | 1,611558 | 2 |
| JSON | 4181,215 | 4,181215 | 5 |
| Binario | 4166,493 | 4,166493 | 5 |

Resultado DELIVERY_STAGES_PASS_NOT_GLOBAL_CAPACITY_OR_N3. Dos casos concurrentes,
384 navegaciones y 20 descargas por tipo/caso; sin perfiladores. No aceptación
 global de capacidad, N3 o MOD-08 ni mejora causal de rendimiento.

Probe final con init 20261012-003153-2f383fa9: 1 PASS en 18,653 s,
NATIVE_INSTRUMENT_PROBE_NOT_CAPACITY, fuentes sin cambios y limpieza.
109 comprobaciones locales de contratos, separación y cierre pasan.
El cierre de procesos vivos o zombis persistentes sigue fallando explícitamente.

## Incidencia energética conservada

El perfil cambió a balanced y power-saver pese a desactivar battery-aware y fijar
performance. La reserva temporal desapareció; al liberarla devolvió cookie
inexistente. También hubo cambios después de fijar Performance/PowerProfile en
los tres perfiles KDE (AC/Battery/LowBattery), con backup local conservado.
El usuario confirma que sólo alternaba el cable y no cambió perfiles manualmente.
No está identificado el actor exacto. Una observación D-Bus limitada sólo captó
nuestro Set, no prueba que no hubiera otros cambios. No se atribuye a KDE como
causa demostrada ni se presenta el firmware como causa probada.

El [driver de power-profiles-daemon](https://freedesktop-team.pages.debian.net/power-profiles-daemon/power-profiles-daemon-Profile-Drivers.html)
contempla cambios de perfil desde el exterior; esto es una posibilidad, no
medición causal en este portátil. Las pruebas locales no son de energía constante.
Los recibos de entorno y notas de intervenciones se conservan en artifacts;
el VPS debe medir su propio entorno, incluyendo contención/CPU steal.

[Resumen y hashes de artefactos](mod08-vps-preparacion-verificada-20261012.json).
[Procedimiento remoto](../mod08-vps-medicion.md). No se suben bases sintéticas,
secretos, venvs o grandes binarios temporales; se regeneran con el procedimiento.
