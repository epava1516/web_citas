# CR09: contraste preparación estática por proceso

Run025248-2d8dc2bb,HEAD e6d5e4b más test congelado,1PASS125,96s. Python3.12.15/PG17.11 propios/nativehostca3c,10k anuncios sintéticos;controlador4CPU/PG1CPU y límites habituales. Seis procesos nuevos,tresbloquesAB/BA,30peticionescadauno=180. GC activo y observado,sincolección forzada/cambio política. Variante sólo resuelve rutas ES/EN,reverse home(que prepara diccionario inverso),compila base/results/public_detail bajo ambosidiomas. Ninguna lectura de datos de aplicación durante preparación;socketconnect/ex bloqueados,0intentos/0conexionesDB y sin hilos adicionales. get_wsgi_application igual antesdeambasvariantes.

| Primera petición wall ms | Actual | Preparación |
|---|---:|---:|
| Bloque0|640,829|354,258|
| Bloque1|763,852|290,732|
| Bloque2|808,417|327,132|
| Mediana|763,852|327,132|
| CPU hilo mediana|531,953|167,234|

Preparaciónwall338,049/333,226/311,803ms;CPU334,075/329,605/307,990ms. No desaparece trabajo: se adelanta al arranque. Mediana180peticiones porvariante160,571→163,002ms: no mejora general estable demostrada. Primera6sumwall porbloque1,514→1,289s/1,858→1,144s/1,584→1,181s. No sockets HTTP/admisiónconcurrente/Celery ni prueba de capacidad. Arranquecompleto incluye costes no cronometrados de Python. DjangoClient utiliza handlerpropio,no workerGunicornreal.

Listados/búsquedas cuerpos SHA256 iguales entre variantes/repeticiones y ambosidiomas;detalle200/no-store,sin igualdadtotalfirmas variables. Todosprimerosrequests incluidos. Datos static-warmup.json conservan filas/GC/preparación porproceso. No cachédeautorización/datos,ningúncontrolnativo omitido.

Resultado justifica evaluar integración de preparación estática en hookpost_worker_init antesdeadmisión. Verificar hook en runtime real, restauraciónidioma,idempotencia y ausênciaDB/red,después carga clean mismo límite. No aceptar sólo por estaprueba. Últimop95clean1,173553838FAIL;últimoinstrumentado1,198622245FAIL. CR09/N3/contratoabiertos.

Fuentescongeladas iguales antesdeeditar,runner/hijo/temp/contenedores propios ausentes;unidadinactive/MainPID0. Sinproducción/datosreales/proveedores/Claude,consumo previo intacto.
