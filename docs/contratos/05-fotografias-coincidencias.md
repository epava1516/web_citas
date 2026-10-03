# CR-05 — Fotografías y coincidencias, interfaz v1

## Rutas y acceso

- POST /{es|en}/draft/{revision}/photos/upload/: gestor vigente, borrador editable, CSRF, imagen multipart. 302 al paso3; 400 inválida/límite, 404 ajeno, 429 velocidad excesiva. Devuelve el mismo Photo para reintento de idéntico archivo dentro de revisión; no consume otra plaza.
- GET /{es|en}/photos/{id}/private/: gestor autorizado, derivado privado; 302 sin sesión, 404 ajeno/retirado, 409 procesando, 200 WebP no-store. No ruta HTTP directa para original.
- POST /{es|en}/photos/{id}/remove/: solo borrador del gestor vigente; retirado lógico para respetar evidencias/referencias existentes.
- POST /{es|en}/photos/{id}/reorder/: direction up/down; normaliza posiciones bajo bloqueo de revisión; 400 dirección inválida, 409 revisión no editable.

Paso3: carga → estado queued/processing/ready/failed y comparación pendiente → vista previa privada → orden/retirada. Coincidencia solo indica revisión pendiente, no revela imágenes o identidad de otra cuenta. Fotos aún no públicas/aprobadas: CR-06 aplica moderación y accesos públicos de derivados.

## Datos y procesamiento

Blob global por SHA-256 de bytes, originales con clave aleatoria y privados, derivados recodificados WebP sin EXIF/ICC. Photo liga Blob a revisión, posición, aprobación y comparación completada. Reutilizar bytes no concede derechos de otra cuenta ni muestra su original. Match guarda candidato/método/score/decisión; las señales son dirigidas y pueden existir en ambos sentidos de una pareja; UploadAttempt observa comportamiento sin copias redundantes. Una Blob puede servir varias revisiones autorizadas; borrarla requiere comprobar referencias/retención.

Máximos: ocho fotos activas por revisión, diez MiB por archivo, cuarenta megapíxeles. Solo JPEG/PNG/WebP estáticos. Validar decodificación real, animación, límites y descompresión antes de aceptar; SVG/GIF/PDF no aceptados. No confiar en extensión ni Content-Type declarado. Rate limit treinta cargas por quince minutos, además de cuotas.

Tarea Celery process_blob(blob_id), entrada por ID, idempotencia, lease tres minutos, reintento OSError con backoff hasta tres. Estado en DB permite recuperar jobs queued/stale/failed y fotos de Blob ready sin comparación terminada. Beat ejecuta recuperación cada minuto, lote100, hasta cuatro intentos de generación automática. Fallo de broker al registrar callback no elimina original ya confirmado: callback robusto y recuperación periódica.

Comparación marca únicamente fotos capturadas al iniciar el trabajo: una carga que llega durante la comparación conserva pendiente y se reprocesa; no atribuirle un análisis inexistente. Todas las cuentas/agencias/teléfonos entran en el mismo espacio de coincidencias.

## Comparación visual y evaluación

SHA detecta bytes exactos; huellas pHash globales, rotadas y ventanas asimétricas recuperan candidatos para recompresión/recorte moderado. ORB, máximo800 puntos y960px, verifica correspondencia mediante RANSAC de rotación/escala/traslación, al menos20 inliers, proporción/spread/overlap mínimos. OpenCV limita un hilo. Sin reconocimiento facial ni modelos descargados.

Un candidato sin geometría suficiente sigue pendiente de revisión humana. Coincidencia visual no identifica a la persona, no acredita propiedad y no suspende cuenta automáticamente. Planos uniformes/escasa textura no se confirman visualmente. Recortes extremos, espejado y transformaciones no evaluadas no están garantizados.

Evaluación sintética inicial reproducible en tests/test_image_similarity.py: cinco positivos (JPEG40/70, recorte lateral20%, recorte top/left10%, rotación90) recuperados y confirmados; diez negativos de escenas independientes no confirmados; casos planos y diminutos sin confirmación. Tests de pipeline comprueban recorte entre cuentas con SHA diferente y estados pendientes; no calibración sobre fotografías reales ni medida estadística suficiente para prometer tasas generales. Calibración ampliada/rendimiento y revisión humana continúan en B-B.

Referencias: [OpenCV, correspondencias geométricas](https://docs.opencv.org/4.12.0/d1/de0/tutorial_py_feature_homography.html). Esta implementación usa modelo afín parcial más restrictivo para las transformaciones admitidas; umbrales experimentales registrados en similarity.py.

## Almacenamiento y pendientes

Local: Django FileSystemStorage bajo MEDIA_ROOT privado, volumen app/worker compartido. S3 compatible: MEDIA_STORAGE_PROVIDER=s3, AWS_STORAGE_BUCKET_NAME, endpoint/región y credenciales estándar; ACL privada, sin URLs públicas. Adaptador configurado, proveedor/bucket/políticas reales no verificados.

B-B debe optimizar recuperación de candidatos (ahora barrido global de firmas en DB), probar volumen/capacidad, retención, limpieza de huérfanos, almacenamiento real y alertas. Moderación/resolución y publicación CR-06. No confundir generación del derivado con aprobación de foto ni comparación pendiente con completada.

CR-06 extiende comparación exacta del worker a referencias de bytes reutilizados/clonados. Resolución humana y evidencias por pareja están descritas en contratos/06; ninguna copia de revisión hereda automáticamente el derecho de publicación o una decisión sobre otra pareja de fotos.
