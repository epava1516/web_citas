import io
import json
import os
import random
from pathlib import Path

import pyotp
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from apps.catalog.models import Category, Municipality, Service
from apps.core.mfa import encrypt
from apps.core.models import (
    Agency,
    AgencyMember,
    AgencyReview,
    LegalAcceptance,
    LegalDocument,
    Person,
    PhoneClaim,
    RepresentationAction,
    User,
)
from apps.core.verification_services import receive_event, simulate_event, start_age_check
from apps.listings.models import Listing, Rate, Revision
from apps.listings.moderation import decide
from apps.listings.submissions import submit
from apps.mediafiles.models import Blob
from apps.mediafiles.services import ingest, process

NAMES = [
    "individual",
    "agency",
    "model-a",
    "model-b",
    "editor",
    "moderator",
    "visitor",
    "withdrawn",
]


def demo_image(seed):
    rng = random.Random(seed)
    image = Image.new("RGB", (640, 480), "white")
    draw = ImageDraw.Draw(image)
    for _ in range(100):
        x, y = rng.randrange(580), rng.randrange(420)
        draw.rectangle((x, y, x + 40, y + 40), fill=tuple(rng.randrange(256) for _ in range(3)))
    output = io.BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


class Command(BaseCommand):
    help = "Install synthetic private demo accounts/photos once; forbidden in production"

    def add_arguments(self, parser):
        parser.add_argument("--credentials-file", default=".ai/demo-credentials.json")

    def handle(self, *args, **options):
        if settings.PRODUCTION or settings.VERIFICATION_PROVIDER != "simulator":
            raise CommandError("Synthetic demo requires a development simulator")
        password = os.getenv("DEMO_PASSWORD", "")
        if not password:
            raise CommandError("Set DEMO_PASSWORD without placing it on the command line")
        try:
            validate_password(password)
        except ValidationError as error:
            raise CommandError("Demo password does not meet password policy") from error
        existing = set(
            User.objects.filter(username__startswith="fixture-v1-").values_list(
                "username", flat=True
            )
        )
        expected = {f"fixture-v1-{name}" for name in NAMES}
        if existing == expected:
            self.stdout.write(
                "Synthetic demo already installed; existing data and credentials preserved"
            )
            return
        if existing:
            raise CommandError("Demo namespace occupied; existing users preserved")
        credentials_path = Path(options["credentials_file"])
        credentials_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(credentials_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as error:
            raise CommandError("Credentials file exists; it will not be overwritten") from error
        written_files = []
        try:
            with os.fdopen(descriptor, "w") as output, transaction.atomic():
                call_command("bootstrap", stdout=self.stdout)
                call_command("seed_catalog", stdout=self.stdout)
                credentials = {"synthetic_only": True, "password": password, "accounts": {}}
                users = {}
                for name in NAMES:
                    mfa = name in ["agency", "editor", "moderator"]
                    user = User.objects.create_user(
                        username=f"fixture-v1-{name}",
                        email=f"fixture-{name}@example.invalid",
                        password=password,
                        email_verified_at=timezone.now(),
                        role="agency" if name == "agency" else "visitor",
                        mfa_enabled=mfa,
                        mfa_version=1 if mfa else 0,
                    )
                    secret = pyotp.random_base32() if mfa else ""
                    if secret:
                        user.mfa_secret_encrypted = encrypt(secret)
                        user.save(update_fields=["mfa_secret_encrypted"])
                    users[name] = user
                    credentials["accounts"][name] = {"email": user.email, "totp_secret": secret}
                    for document in LegalDocument.objects.filter(
                        active=True, language="es", slug__in=["terms", "privacy"]
                    ):
                        LegalAcceptance.objects.create(
                            user=user,
                            document=document,
                            action="account_terms"
                            if document.slug == "terms"
                            else "privacy_notice",
                        )
                moderator = users["moderator"]
                moderator.user_permissions.add(
                    *Permission.objects.filter(codename__in=["review_agency", "review_listing"])
                )
                agency = Agency.objects.create(
                    owner=users["agency"],
                    name="Agencia sintética de demostración",
                    verification_status="passed",
                    verification_procedure="simulator-v1",
                    review_version=2,
                )
                AgencyReview.objects.create(
                    agency=agency,
                    reviewer=moderator,
                    outcome="passed",
                    reason="Estado sintético para demostración",
                    evidence_reference="fixture-v1-synthetic",
                    procedure="simulator-v1",
                )
                AgencyMember.objects.create(agency=agency, user=users["editor"])
                document = LegalDocument.objects.get(slug="publishing", language="es", active=True)
                city = Municipality.objects.get(code="demo-south")
                shared_phone = PhoneClaim.objects.create(
                    agency=agency, phone="+349990001001", verified_at=timezone.now()
                )
                for index, name in enumerate(["individual", "model-a", "model-b", "withdrawn"]):
                    managed_by_agency = name.startswith("model-")
                    subject = users[name]
                    manager = users["agency"] if managed_by_agency else subject
                    claim = (
                        shared_phone
                        if managed_by_agency
                        else PhoneClaim.objects.create(
                            individual=subject,
                            phone=f"+34999000100{index + 2}",
                            verified_at=timezone.now(),
                        )
                    )
                    person = Person.objects.create(
                        alias=f"Persona sintética {name}",
                        agency=agency if managed_by_agency else None,
                        individual=None if managed_by_agency else subject,
                        subject=subject,
                        phone_claim=claim,
                        consent_version=1,
                        assigned_editor=users["editor"] if name == "model-a" else None,
                    )
                    RepresentationAction.objects.create(
                        person=person,
                        subject=subject,
                        manager_version=1,
                        action="grant",
                        document=document,
                    )
                    receive_event(simulate_event(start_age_check(person, subject), "passed"))
                    acceptance, _ = LegalAcceptance.objects.get_or_create(
                        user=manager,
                        document=document,
                        agency=agency if managed_by_agency else None,
                        action="publish",
                    )
                    listing = Listing.objects.create(person=person)
                    revision = Revision.objects.create(
                        listing=listing,
                        manager_version=1,
                        title=f"Demostración de fotografía {name}",
                        description="Perfil sintético para probar fotografía profesional y eventos culturales. No representa a una persona real.",
                        description_alternative="Synthetic profile for photography and cultural events; not a real person.",
                        municipality=city,
                        spoken_languages=["es", "en"],
                        days=["1", "3"],
                        time_slot="morning",
                        phone=claim.phone,
                        contact_exposure_accepted=True,
                        publisher_acceptance=acceptance,
                    )
                    revision.categories.add(Category.objects.get(slug="modeling"))
                    revision.services.add(Service.objects.get(slug="photography"))
                    Rate.objects.create(
                        revision=revision, concept="Sesión fotográfica sintética", mode="consult"
                    )
                    photo = ingest(
                        manager,
                        revision.pk,
                        SimpleUploadedFile(
                            "synthetic.png", demo_image(710001 + index), content_type="image/png"
                        ),
                    )
                    written_files.append(
                        ("original", photo.blob.original.storage, photo.blob.original.name)
                    )
                    process(photo.blob_id)
                    photo.blob.refresh_from_db()
                    written_files.append(
                        ("derivative", photo.blob.derivative.storage, photo.blob.derivative.name)
                    )
                    revision.refresh_from_db()
                    submit(manager, revision.pk, revision.edit_version, True)
                    if name != "model-b":
                        decide(
                            moderator,
                            revision.pk,
                            revision.edit_version,
                            "approved",
                            "Publicación sintética de prueba, sin identidad real",
                        )
                    if name == "withdrawn":
                        # State fixture; this does not assert CR-08 lifecycle delivery.
                        listing.refresh_from_db()
                        listing.status = "withdrawn"
                        listing.available_until = None
                        listing.save(update_fields=["status", "available_until"])
                json.dump(credentials, output, indent=2)
                output.flush()
                os.fsync(output.fileno())
        except Exception:
            credentials_path.unlink(missing_ok=True)
            for field, storage, name in written_files:
                if name and not Blob.objects.filter(**{field: name}).exists():
                    storage.delete(name)
            raise
        self.stdout.write(
            "Synthetic demo installed: eight accounts, four people, pending/published/withdrawn; private credentials file created (0600)"
        )
