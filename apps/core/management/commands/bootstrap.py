from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.core.models import LegalDocument

TEXTS = {
    "terms": (
        "Condiciones de uso",
        "Terms of use",
        "Solo mayores de edad. No se permite contenido ilegal, no consentido ni publicidad de servicios sexuales. La cuenta no acredita verificación de identidad. No publiques datos de otra persona sin autorización específica.",
        "Adults only. Illegal or nonconsensual content and sexual service advertising are prohibited. An account does not establish identity verification. Do not publish another person's data without specific authorization.",
    ),
    "privacy": (
        "Información de privacidad",
        "Privacy information",
        "La cuenta utiliza correo, contraseña cifrada mediante hash y registros de aceptación para gestionar acceso. No publicamos el correo de cuenta. Los anuncios tendrán sus propios controles y avisos. Esta muestra no es una política final y no permite tratar datos reales.",
        "Accounts use email, hashed passwords and acceptance records for access management. Account email is private. Listings have separate controls and notices. This sample is not a final policy and cannot authorize real personal data processing.",
    ),
    "notice": (
        "Aviso legal",
        "Legal notice",
        "Operador y dominio pendientes. Sitio privado de desarrollo sin actividad comercial.",
        "Operator and domain pending. Private development site with no commercial activity.",
    ),
    "cookies": (
        "Cookies",
        "Cookies",
        "Solo sesión, seguridad CSRF y preferencia de idioma. Sin analítica, publicidad de terceros ni rastreadores.",
        "Session, CSRF security and language preference only. No analytics, third-party advertising or trackers.",
    ),
    "publishing": (
        "Condiciones de publicación",
        "Publishing terms",
        "Cada persona requiere mayoría de edad, control de contacto y autorización. Agencia y persona representada son distintas. Una publicación por persona. No contenido sexual explícito ni publicidad de prostitución. Moderación y reclamaciones no eximen al operador de sus responsabilidades.",
        "Each person requires adult-age evidence, contact control and authorization. An agency and its represented person are distinct. One listing per person. No explicit sexual content or prostitution advertising. Moderation and complaints do not exempt the operator from its responsibilities.",
    ),
    "content": (
        "Reglas de contenido",
        "Content rules",
        "Catálogo: modelaje, acompañamiento social y bienestar no sexual. Fotos autorizadas, sin menores, desnudos explícitos ni datos de domicilio.",
        "Catalog: modeling, social companionship and nonsexual wellness. Authorized photos only; no minors, explicit nudity or home addresses.",
    ),
    "safety": (
        "Seguridad y ayuda",
        "Safety and help",
        "Puedes denunciar contenido y reclamar retirada. Una comprobación de edad no garantiza la conducta de una persona.",
        "You can report content and request removal. An age check does not guarantee a person's conduct.",
    ),
}


class Command(BaseCommand):
    help = "Create idempotent synthetic development legal catalog; never for production"

    def handle(self, *args, **options):
        if settings.PRODUCTION:
            raise CommandError("Synthetic legal documents cannot be installed in production")
        for slug, (es_title, en_title, es_body, en_body) in TEXTS.items():
            for language, title, body in [("es", es_title, es_body), ("en", en_title, en_body)]:
                LegalDocument.objects.get_or_create(
                    slug=slug,
                    version="dev-1",
                    language=language,
                    defaults={"title": title, "body": body, "published_at": timezone.now()},
                )
        self.stdout.write(
            self.style.SUCCESS("Synthetic legal documents available; not legally approved")
        )
