# Inicialización estática: coste aislado y límite del hallazgo

Tres intérpretes nuevos, socket.connect/connect_ex bloqueados:0intentos,0conexionesDjangoabiertas,1thread en cada uno. Se importaWSGI, se resuelven rutas públicas ESEN con contexto de idioma y se compilan base/results/public_detail sin render ni datos. Primera ejecución del instrumento falló al resolverENsin activar idioma; Resolver404 conservado, corregido el contexto, sin cambio de aplicación.

| Mediana CPU de3procesos | Primera operación ms | Repetición ms |
| --- | ---: | ---: |
| Resolver rutas | 314,75 | 1,17 |
| Compilar tres plantillas | 16,47 | 0,03 |

[Datos](cr09-static-startup-audit-20261016.json),script/logs enartifacts/cr09-static-startup-audit-20261016/. El arnés ya consulta seis rutas antes de las llegadas20rps ydespués prepara elfixture/espera la faseBeat. No se sabe qué trabajador atendió cada fría desdeesta evidencia; no tratar primera petición etiquetada como primera devida. El coste estático no prueba ahorro de p95 ni justifica precarga adicional sin atribución.

Revisión offline del diagnóstico004422: primeras peticiones etiquetadas porPID/tipo también gastan másSQL, asíque no se atribuye todo a imports. PublicationSampler muestra dirty1 a0,377s y1,378s,dirty0 a2,377s; la espera dura más que esa ventana por acumulación, sin prueba causal exclusiva. Es esta revisión de dependencias la que llevó al defecto de [lectores Match](cr09-match-counterpart-invalidation-20261016.md), no una nueva carga de capacidad. No cambio startup ni nuevo p95.
