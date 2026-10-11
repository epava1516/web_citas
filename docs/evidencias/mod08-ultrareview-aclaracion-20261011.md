Respuesta corta: la mención es una **referencia que no tiene respaldo en lo que recibí**. No viene con ubicación, reproducción ni hallazgo propio. No volví a leer código para esta respuesta; solo uso lo leído antes y el texto del informe.

## Hallazgo 2: la mención a `KernelIntegrityError`

**Lo que dice el informe:**
- El razonamiento del hallazgo 2 dice: *"per the already-reported KernelIntegrityError-propagation issue turns into either a universal silent fallback to the pure-Python path (perf regression) or an uncaught crash in rights_validation_seal.rule_version(), depending on environment."*
- Eso es todo lo que hay sobre ese problema. No da archivo, ni línea, ni reproducción, ni severidad, ni verificación.
- El resultado final trae solo 3 hallazgos y ninguno trata de que se propague `KernelIntegrityError`.
- El texto llegó recortado en parte: el razonamiento del hallazgo 3 termina en "on line…". No puedo ver el resultado sin procesar del trabajo en la nube; solo tengo lo que me llegó en la notificación.

**Lo que yo deduzco, sin verificar:**
- Lo más probable es que fuera un candidato de una fase anterior de la revisión. Pudo descartarse al verificarlo o fusionarse con otro, y el texto del hallazgo 2 conservó la referencia. No puedo confirmarlo.
- La propia frase se contradice: "silent fallback **o** crash según el entorno" no describe un comportamiento concreto. Además, el docstring del loader dice que un build presente pero inválido "fails closed", lo que choca con lo de "silent fallback".
- Del código que sí leí:
  - `_load()` lanza `KernelIntegrityError` si el manifest no es válido (`canonical_kernel_loader.py:118-122`).
  - `_check` llama a `validated_kernel()` sin `try` (`fast_canonical.py:54`).
  - No leí `validated_kernel()` (está después de la línea 130). Puede que guarde el fallo en caché o que devuelva `None`, así que no sé si el error llega de verdad a quien llama.
  - Tampoco leí `rights_validation_seal.rule_version()`.

**Conclusión:** sin evidencia. Para descartarlo o confirmarlo habría que leer `validated_kernel()` y sus llamadores. No lo he hecho.

## Por qué unificar `_check` y `reference_check` no es seguro sin más

**Lo que leí en el código:**
- `fast_canonical.py:39-40` lo dice explícitamente: *"Keep the original Python body in this frame at recursion-budget edges. Do not call the Python loader where its own frames could change acceptance."*
- El acceso al kernel solo ocurre en la llamada de primer nivel (`depth == 0`) y solo si quedan más de 512 frames de margen (`fast_canonical.py:41-47`). Si queda menos, se ejecuta el cuerpo Python en ese mismo frame.
- Cada nivel de anidamiento gasta un frame. El límite propio es `depth > 200`, que lanza `ValueError`.

**Qué pasaría en cada forma de unificarlas (inferencia):**
1. **`_check` llama a `reference_check`:** añade un frame más a toda la recursión. Una entrada que hoy se acepta, o que da `ValueError` por anidamiento, podría dar `RecursionError` cuando la pila está justo en el borde. Cambia qué se acepta y qué tipo de excepción sale, y quien capture `ValueError`/`TypeError` no la capturaría. El efecto es pequeño (un frame) y solo aparece en el borde exacto, pero es justo lo que ese comentario prohíbe.
2. **`reference_check` llama a `_check`:** según el informe, `reference_check` es el respaldo del kernel nativo (`_canonical_kernel.pyx: check()`); no leí el `.pyx` para confirmarlo. Si es así, el respaldo volvería a pasar por la entrada del kernel con `depth == 0`, llamando otra vez al loader desde dentro del kernel. Eso podría crear reentrada o recursión mutua, y vuelve a meter los frames del loader en el cálculo de aceptación.

**Matiz:** es más exacto decir "no está demostrado que sea seguro y contradice la regla documentada" que "se sabe que rompe". Por eso propuse un test de equivalencia entre las dos funciones en vez de fusionarlas.

Comprobación independiente Codex: _validated_state guarda el mensaje de fallo y vuelve a lanzar KernelIntegrityError; validated_kernel no convierte ese fallo a None. rule_version llama kernel_identity directamente. La ausencia del artefacto permite referencia Python; un artefacto instalado inválido falla cerrado por diseño. La afirmación de fallback silencioso por mismatch no queda sustentada por estos caminos. Tests existentes cubren errores de integridad propagados y semántica de recursión. Revisión estática, sin nueva prueba ni medición.
