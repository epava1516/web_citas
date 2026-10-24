# B07 — transición create/start del observador

## Protocolo259 preregistrado

Hipótesis finita: el primer docker inspect puede devolver0 cuando el último contenedor propio todavía está created/Pid0; CapacityResourceReader exige RunningTrue/Pid>1 y el bucle termina con error en lugar de esperar start. No es causa histórica257 demostrada.258 PASS no elimina ese riesgo.

Reproducción nativa mínima, sin cargaHTTP ni PostgreSQL: un contenedor propio nuevo con nombre/label del ensayo y rol app, imagen existente6936424d/pullnever, sinred,readonly/capdropall/no-new-privileges, CPU0.1/memoria128MiB/swap0/pids32; entrypointPythonimporttime.sleep30. Docker create sin start; inspect debe devolver0/created/RunningFalse/Pid0. Verificador actual debe rechazarlo antes de leerproc. Iniciar una vez, inspect running yverificador debe validarPID/start_ticks/cgroup exacto. Guardar sólo identidad mínima/estados/veredictos/huellas y comprobar eliminación exacta, sinvariables de entorno ni logs. Plazo global90s yporcomando20s, sinreintentos paraverde.

Actualizar grafo293 antes de congelar fuentes y ejecutar. Telegram inicio/terminal con recibos. No repetir100/10000 ni atribuir recursos de este contenedor aHTTP. Un positivo demuestra un estado alcanzable que el bucle trata mal; no identifica retrospectivamente elValueError257. Si confirmado, corregir espera estricta sólo para created propio, manteniendo rechazo de identidades ajenas/paused/restarting/exited/dead ydeadline600. Controles pertinentes antes de integración; B07 abierto, ocho de18.

## Primera reproducción y corrección propuesta

El primer ensayo nativo259 obtuvo inspect0/Statuscreated/RunningFalse/Pid0 yel guard actual lanzó Owned capacity container mismatch: estado alcanzable que el bucle trataba como fallo terminal. El contraste después de start falló: no se conservaron suficientes detalles para identificar por qué el proceso no seguía activo. No declarar todo el ensayoPASS. Negativo íntegro en observer259-native-initial-negative.json yscript original preservado; fuentes/protocolo/limpieza verificados. Este defecto alcanzable no demuestra la causa retrospectiva257.

Cambio mínimo: excepción tipada CapacityContainerPending sólo después de validar nombre,label,ID yrun/rol y únicamenteStatuscreated/RunningFalse/PausedFalse/RestartingFalse/Pidint0. El observador vuelve a esperar dentro del deadline600s existente; cualquier otra excepción sigueERROR. No se aceptan servicios sin arrancar, no se amplían cuotas/plazos y no se toman muestras hasta validar las seis identidades. Códigos seguros258 conservados.

Controles: seis casos metadata created propio/foreign/paused/restarting/exited/Pidboolean; los controles del bucle incorporan una primera observación pending yposterior validación, conservando casos de deadline/fases incompletas. 44controlesPASS33.00s yRuffPASS; son simulados, sin crédito de servicios reales. Reproducción nativa correctiva mantendrá exactamente límites yfixture, con usuarioUID/GID actual explícito yestado mínimo después de start guardado antes de verificar. Una ejecución acotada90s, sinotrascargas. Registrar nuevo grafo294/fuentes antes de ejecutarla y conservar ambos resultados.

## Resultado259 auditado

Correctiva nativa `20261022-214753-6561739d`: inspect decreated devuelve0, el guard corregido lanza CapacityContainerPending ydespués destart valida el proceso vivo mediantePID/start_ticks/cgroup yID íntegro. HostConfig confirma límites declarados/sinred/readonly; no se midieron cuotas kernel ni costes deHTTP en este ensayo mínimo.44controles simuladosPASS33.00s cubren metadatos ybuclepending→validación/deadlines/fases; RuffPASS. No se repitió la pruebaHTTP completa de seis servicios.

Antes de editar se auditaron1.701fuentes iguales a prerregistro/proof/árbol,628producto intacto,protocolo original porbytes/SHA,script exacto,ausencia Docker/PID real,negativo inicial preservado yrecibos Telegram deambos ensayos. Evidencia observer259-audit.json, resultadoVERIFIED_CREATED_PENDING_RUNNING_GUARD_CORRECTION. Es una corrección de un riesgo reproducible del instrumento; no demuestra retrospectivamente la causa257 ni transforma aquelERROR enPASS.

Decisión: no repetir100/10000HTTP por esta corrección del arranque del observador. La cobertura funcional10000 de257 se conserva ysu captura de recursos fallida sigue no aceptada; no mezclarla con otra corrida como si tuviera muestras. Retomar residual contractual: analizar coste combinado a10.000 ymatriz comparable de diversidad, reutilizando240/241para100/1000 ycontroles funcionales válidos. Justificar protocolo/estimación/plazos antes de nueva prueba larga yusar relevo,Telegram,pausa/compactación/autoresume si corresponde. Sin capacidad ni900automático,B07 abierto,ocho de18.
