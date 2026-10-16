# Diagnóstico instrumentado del detalle integrado

Run20261016-105425-e54cee8a, fuentee63becb:FAILinstrumentado,1prueba185,96s/1200dinámicas emparejadas porID, sin errores de transporte. p95instrumentado0,897076479s; no sustituye los limpios0,675688141PASS y0,880356520FAIL. Freeze y limpieza independientes. [Recibo completo](cr09-detail-ingress-20261016.json).

| Media por petición | Llegadas0–1s | Llegadas15–60s |
|---|---:|---:|
| WSGI | 310.547ms | 178.714ms |
| SQL | 168.639ms | 70.562ms |
| CPUworker | 123.719ms | 94.682ms |
| GCsolapado | 22.442ms | 7.469ms |
| AntesWSGI | 273.394ms | 37.051ms |

SQL/GC/CPU se solapan, no se suman. Cursor SQL no es CPU PostgreSQL. AntesWSGI no es cola exacta; cohortes tomadas desde origen del generador. El mayor agregado SQL identificado inicialmente es selecciónpágina(caller487/hash95c3…,4llamadas419,540ms), seguido en ese par por recuento(caller486/hashc3f3…,4llamadas242,142ms). Hidratación(hash31a87…,5llamadas229,350ms) también contribuye. Overflow134llamadas377,909ms queda sin atribución individual: no afirmar ranking exhaustivo de todas las consultas.

Los cuatro workers emitieron static_ready y recibieron algún preámbulo antes de carga, con68/39/66/39SQL porworker, diferente del diagnóstico previo donde dos carecían de trabajo SQL relevante. No implica que cada worker haya preparado las seis rutas ni permite asignar nombres a preámbulos no etiquetados. Los tiempos instrumentados no demuestran causalidad entre versiones.

Siguiente control acotado: capturar exclusivamente recuento/selección del algoritmo dirty actual y EXPLAIN ANALYZE BUFFERS SETTINGS fuera del request, cuatro rutas/10ksintéticos/un dirty, conexión nueva por ruta ytimeout5s porplan. Registrar configuración originalJIT/joins. No candidato, comparación temporal, nueva carga limpia o900. Plan posterior con buffers compartidos no prueba el coste frío original.
