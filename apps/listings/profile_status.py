"""Private profile guidance; publication authority remains the shared fresh guard."""

from django.utils import timezone

from .moderation import publicly_visible

STATUSES = {
    "draft": ("Borrador privado", "Private draft"),
    "processing": ("Procesando fotografías", "Processing photographs"),
    "pending": ("En revisión", "Under review"),
    "published": ("Publicado", "Published"),
    "paused": ("En pausa", "Paused"),
    "rejected": ("Necesita correcciones", "Needs corrections"),
    "withdrawn": ("Retirado", "Withdrawn"),
    "expired": ("Caducado", "Expired"),
    "approved": ("Revisión aprobada", "Approved revision"),
    "obsolete": ("Revisión sustituida", "Superseded revision"),
}
HINTS = {
    "draft": ("Completa el perfil, añade fotos y envíalo a revisión. Aún es privado.",
              "Complete your profile, add photographs and send it for review. It is still private."),
    "processing": ("Las fotografías se están procesando. Revisa su estado antes de enviar el perfil.",
                   "Photographs are being processed. Check their status before submitting your profile."),
    "pending": ("Esta versión espera revisión humana y todavía no se ha publicado.",
                "This version awaits human review and has not been published yet."),
    "published": ("Tu perfil está visible. Puedes preparar cambios sin modificar la versión aprobada.",
                  "Your profile is visible. You can prepare changes without editing the approved version."),
    "paused": ("Tu perfil no está visible. Puedes reanudarlo si sigue vigente y cumple los controles.",
               "Your profile is hidden. You can resume it while it is current and passes publication checks."),
    "rejected": ("Consulta el motivo de revisión y prepara un borrador corregido.",
                 "Read the review reason and prepare a corrected draft."),
    "withdrawn": ("Tu perfil no está visible. Para volver a publicar, prepara una nueva revisión.",
                  "Your profile is hidden. Prepare a new revision to publish again."),
    "expired": ("Tu perfil no está visible. Confirma los datos para renovarlo si cumple los controles.",
                "Your profile is hidden. Confirm its information to renew it if publication checks pass."),
}


def status_label(status, language):
    return STATUSES.get(status, ("Revisar estado", "Check status"))[language == "en"]


def revision_summary(revision, language):
    if revision is None:
        return None
    index = language == "en"
    return {"label": status_label(revision.status, language),
            "hint": HINTS.get(revision.status, ("", ""))[index]}


def publication_summary(listing, language):
    index = language == "en"
    if listing is None:
        return {"label": ("Perfil sin completar", "Profile not completed")[index],
                "hint": HINTS["draft"][index], "visible": False}
    status = listing.status
    if status in {"published", "paused"} and listing.expires_at and listing.expires_at <= timezone.now():
        status = "expired"
    visible = status == "published" and publicly_visible(listing)
    if status == "published" and not visible:
        return {"label": ("Publicación no visible", "Publication hidden")[index],
                "hint": ("Revisa los controles de publicación y actualiza el perfil si corresponde.",
                         "Check publication requirements and update your profile where needed.")[index],
                "visible": False}
    return {"label": status_label(status, language),
            "hint": HINTS.get(status, ("", ""))[index], "visible": visible}
