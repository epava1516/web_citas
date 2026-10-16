# Cierre de representación: replay HTTP corregido

Se encontró un defecto real al completar el escenario de persona representada sin cuenta vinculada. El backend `issue()` ya aceptaba replay exacto, pero `respond()` eliminaba del formulario la opción representation_complete al resolver el expediente. La repetición HTTP quedaba rechazada antes de llegar al backend.

| Operación observada | Antes | Corregido |
|---|---:|---:|
| Primer POST de cierre | 302 | 302 |
| Segundo POST idéntico | 400 | 302 |

[Reproducción](cr09-representation-http-replay-original-20261016.json):142429-80ba3641,1FAIL45,99s. [Verificación](cr09-representation-http-replay-fixed-20261016.json):142911-39b4adeb,**7PASS93,97s**, sin fallos/errores/skips. Se conserva la reproducción; no se altera su veredicto.

La vista conserva la opción únicamente en un POST representation_complete de expediente de representación resuelto con clave UUID válida y respuesta existente del mismo expediente/actor/tipo. Es una condición de formulario, no una autorización: `issue()` sigue bloqueando y revalidando payload, versiones y autoridad vigente. GET no ofrece otro cierre; una clave nueva o inválida conserva400. Mismo identificador con texto cambiado produce409. El control final exige una sola respuesta y aviso.

## Variante sin cuenta vinculada

El nuevo fixture quita `Person.subject` antes de enlazar el expediente y comenzar la prueba proporcional. El solicitante HTTP es anónimo; account_subject/reported_subject sonnull y el snapshot del sujeto de la prueba está vacío. Se verifican retirada/replay, una única subida de manager/lifecycle, consentimiento revocado, teléfono desvinculado, fechas originales y propietario de agencia intactos. Después se emite respuesta tipada por HTTP, queda resolved/version1 y el aviso cifrado apunta al contacto de la reclamación, distinto del propietario de agencia. No se presta su cuenta como identidad del titular.

La identidad usa adaptador simulado explícito; la respuesta conserva simulation=True. PostgreSQL y la aplicación Django son reales locales. El nuevo caso usa Client de Django, EN ysinTCP/navegador propio; los seis controles adicionales de respuestas incluyen su prueba móvil existente. No se declara recepción externa del aviso ni prueba de identidad real. El fixture conserva el antiguo User y evidencias; acredita que no hay cuenta vinculada al perfil, no ausencia de toda cuenta histórica coincidente. No exige que un perfil sin autorización directa estuviera públicamente elegible antes de retirarlo.

La [retirada anterior](cr09-rights-no-linked-account-20261016.json),1PASS45,46s, sólo comprobó retirada antes de ampliar el test. Los [ocho controles revalidados](cr09-rights-withdrawal-current-20261016.json),8PASS108,82s, precedieron la ampliación de los helpers y esta corrección de formulario. No sumar esas ejecuciones como N3 común ni presentarlas como una única batería final.

Fuentes congeladas y limpieza comprobadas independientemente en cada ejecución: runner/pytest porPID-start_ticks ausentes, temporales retirados, PostgreSQL/Redis propios eliminados. Ruff y documentación pasan. Sin producción ni proveedores. P95limpio0,862172866sFAIL permanece vigente; no se vuelve a medir por este cambio privado. La imagen v8 precede esta corrección y necesita incorporar el nuevo módulo antes de afirmar runtime actual.
