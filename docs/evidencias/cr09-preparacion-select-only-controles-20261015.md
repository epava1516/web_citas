# Preparar sólo SELECT: correctiva acotada

`0ab41bf` cambia únicamente `_PageReadCursor.execute` para que órdenes noSELECT ySQLobjectsdesconocidos ejecutenconprepareFalse. SELECTtextualstr/bytes conservaautopreparación; fallback>65535sigueinterpolandoconDriver yprepareFalse. NoSQLtruncado/no omitirvalidation/no cambiosfactory/threshold/GUC. La clasificación es sólooptimización,no frontera depermisos.

[Reproducción195937](cr09-preparacion-utility-reproduccion-20261015.json):12scopes anidados generan12SAVEPOINT+12RELEASEpreparadosyunSELECT,1FAIL37.41s. [Correctiva200124](cr09-preparacion-select-only-controles-terminal-20261015.json):**21PASS218.72s**,24utility→0yunSELECTreutilizadocontinuapreparado. Fuentes/limpieza independientes, unitéterminal/MainPID0.

Archivos completos: binding(planescache,restauraciónrealtrasSQLerror/anidado,umbralexpresopreservado,65536parámetros), planningpolicyéxito/error, detailguardfresco, proyección y ciclo/upgrade/expiry/carreras, CPUfamilias72requests. No N3 ni repetición92ampliadas globales.

| CPU backend ms/request |Antes,160205(f93c183previoeagerauto)|Actual200124|
|---|---:|---:|
|listES|54.167|38.333|
|listEN|31.667|35.000|
|searchES|41.667|47.500|
|searchEN|45.833|54.167|
|detailES|20.833|28.333|
|detailEN|9.167|13.333|
|media|33.889|36.111|

No demuestraahorroCPUglobal: diferentesversiones/ejecuciones yfixtureorden/estado caliente; actualCPUformaparte de21tests, anteriorejecutadoaislado.100Hz cuantización, sinPGtracker. No ocultarempeoramientoniprometerp95desdeunitcontrol. Correcciónretieneunlímitelógicocaché yevitapreparaciónirreutilizableprobada; siguecortolimpioúnicosincambiocarga/cuotas. Genéricohidrataciónpospuesto,p95limpioanterior.897765506FAIL.
