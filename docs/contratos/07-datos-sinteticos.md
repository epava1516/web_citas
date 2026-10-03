# Datos sintéticos de demostración — fixture v1

`python manage.py seed_demo` instala una muestra privada reproducible. Requiere proveedor simulator y entorno distinto de production; `DEMO_PASSWORD` en entorno, validado por la política de contraseñas. No imprime contraseña ni secretos. No envía correo/SMS ni usa proveedores externos.

Ocho cuentas con namespace fixture-v1: particular, propietario de agencia, sujetos model-a/model-b, editor, moderador, visitante y particular retirado. Cuatro personas; dos bajo la misma agencia y teléfono sintético compartido, solo model-a asignada al editor. Moderador con review_listing/review_agency y MFA; propietario/editor también MFA, claves independientes cifradas. Aceptaciones/documentos y geografía son muestras identificadas, no documentación legal final ni cobertura nacional.

Publicaciones: particular publicado, model-a publicado, model-b pendiente y particular retirado. Cada persona tiene autorización específica ligada al gestor y edad simulada. Comprobación de agencia y teléfono son estados sintéticos de preparación; ninguna verificación real acreditada. Publicaciones pasan por validación de envío y moderación; el estado retirado se prepara como fixture y no acredita el recorrido de retirada, pendiente CR-08.

Cuatro imágenes PNG de patrones geométricos generados con código propio y semillas fijas; ninguna persona, fotografía de tercero ni anuncio copiado. Ingesta/derivados/comparación reales en ejecución síncrona para preparar fixture; callbacks de worker siguen idempotentes. No confundir esta ejecución con evidencia de cola/worker real.

Credenciales en `.ai/demo-credentials.json` por defecto, creado exclusivamente con modo0600 y excluido de Git/imagen Docker. Contiene contraseña y claves TOTP por cuenta para usar en un autenticador. Ruta configurable mediante --credentials-file. No sobrescribe archivo existente. Repetición con namespace completo conserva datos/credenciales, incluso estados modificados después; namespace parcial ocupado falla conservando usuarios. No sirve como herramienta de reset.

Creación transaccional. Fallo al escribir credenciales revierte datos y elimina las imágenes generadas que ya no tienen referencias en DB, sin eliminar blobs preexistentes referenciados. Pruebas PostgreSQL verifican roles/estados/publicación, idempotencia, privacidad de credenciales, rechazo de producción/namespace ajeno y recuperación ante fallo de escritura.

Con Docker se ejecuta dentro de app para compartir su volumen privado; guardar credenciales allí y copiar su archivo privado al workspace. Comandos en README. No mezclar fotos guardadas en host y volumen Docker sobre la misma DB sin compartir almacenamiento.
