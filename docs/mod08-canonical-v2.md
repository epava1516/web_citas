# MOD-08 — forma canónica y referencias de contenido v2

Alcance: `rights_exports.canonical` usa `rights-canonical-json-v2` (orjson,
claves ordenadas, UTF-8, JSON compacto). La nueva forma cambia espacios y la
representación de algunos flotantes respecto a json.dumps; conserva valores JSON,
orden de listas y Unicode sin normalización. Se rechazan números no finitos,
claves no textuales, tipos que necesitan conversión explícita (datetime, Decimal,
UUID, bytes), enteros fuera de [-2^63, 2^64-1] y profundidad superior a 200.
Las fuentes de derechos ya convierten fechas e identificadores a texto.

`rights_portability_selection.row_reference` usa ahora BLAKE3 sin clave y el
prefijo `b3v2:`. Su entrada liga dataset, posición y fila completa; la canónica y
su versión se incluyen en el dominio de la huella. Esto es identidad de contenido,
no autorización: acciones, canales, tokens y enlaces siguen usando sus HMAC
existentes. SHA-256 de imágenes, archivos, manifiestos y evidencia histórica se
conserva.

Los expedientes y artefactos sintéticos anteriores deben regenerar sus lecturas,
selecciones y decisiones. Una referencia/digest anterior se rechaza por discrepancia;
no se convierte en una aprobación nueva ni se preservan firmas inválidas. No hay
producción ni datos reales y MOD-08 autoriza esta regeneración. Las evidencias
históricas siguen describiendo la versión probada entonces, sin reescritura.

N1 ejecutada: 21 casos puros (canónica y contexto de inspección), cero skips,
0,57 segundos. Comprueban roundtrip Unicode y números extremos, orden de claves,
rechazo de tipos no JSON/no finitos/ciclos, separación de referencias por fila y
persistencia de HMAC dependiente del secreto. No acredita PostgreSQL, N2, capacidad
ni latencia HTTP. Regresión PostgreSQL de exportación/selección pendiente del
runner conjunto coordinado por el agente principal.

Microdiagnóstico sintético local, mínimo de cinco ejecuciones de una operación,
sin cuotas ni HTTP: 1.500 filas con texto ASCII (~22,6 MB) json.dumps 71,9 ms frente
a canónica v2 de texto 10,3 ms; con Unicode dominante (~18,1 MB), 21,8 ms frente
a 40,5 ms. La codificación v2 binaria cuesta 4,4/3,7 ms respectivamente, pero el
wrapper conserva la interfaz de texto por compatibilidad de consumidores. Por
tanto no se afirma una mejora universal: la conversión UTF-8 a texto puede empeorar
la muestra Unicode. Son diagnóstico, no SLO ni aceptación de capacidad.
