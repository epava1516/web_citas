# Preparación del gate HTTP normal en CI propio

Hallazgo verificable: OWNED_REDIS en test_worker_capacity_comparison.py apunta
por defecto a redis://127.0.0.1:56379/15. ss y docker ps confirman que ese puerto
pertenece al servicio normal web-modelos-redis-1. No se conecta ni se inspecciona
su contenido; no se permite scan/delete del broker normal para este ensayo.
El runner actual tiene Redis propio en puerto efímero y etiqueta por run.

El runner oficial limpia variables heredadas, incluidos los switches benchmark.
Por eso pasar WEB_MODELOS_REFRESH_MODE al systemd no basta para activar el modo
normal de forma verificable. El modo actual por defecto es eager; su resultado
no se presenta como worker/Beat reales.

Entrega siguiente después de terminal: adaptar el harness a un broker propio
verificado por etiqueta/puerto/run. El valor debe propagarse tanto a worker/Beat
como al helper de comprobación/limpieza; no aceptar URL normal como fallback en
CI. Activar normal_worker_beat y la política cliente de GC documentada mediante
configuración explícita del ejecutor, registrada antes de la carga. No cambiar
workers, mezcla, duración, umbrales ni decisiones de aplicación. Mantener límites
actuales y verificar limpieza exclusivamente de recursos de esa ejecución.

Validación: un control funcional de la topología, luego gate contractual pertinente
con fuentes congeladas, medida sin perfiladores y ningún otro ensayo propio
concurrente. Un negativo termina y se conserva antes de diagnose separado.
Diseño preparado, aún sin modificación del harness ni carga nueva.
