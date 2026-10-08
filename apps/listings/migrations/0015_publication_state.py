import django.db.models.deletion
from django.db import migrations, models

ALL = "SELECT id FROM listings_listing"
VIA_REVISION = "SELECT v.listing_id FROM {rows} r JOIN listings_revision v ON v.id = r.{column}"
VIA_PHOTO = (
    "SELECT v.listing_id FROM {rows} r JOIN mediafiles_photo p ON p.id = r.{column} "
    "JOIN listings_revision v ON v.id = p.revision_id"
)
VIA_PERSON = "SELECT l.id FROM {rows} r JOIN listings_listing l ON l.person_id = r.{column}"
PROPOSAL = (
    "SELECT l.id FROM {rows} r JOIN safety_rightsrectificationproposal pr ON pr.id = r.{column} "
    "JOIN listings_listing l ON l.person_id = pr.person_id"
)
REVIEW = (
    "SELECT l.id FROM {rows} r JOIN safety_rightsrectificationreview rv ON rv.id = r.{column} "
    "JOIN safety_rightsrectificationproposal pr ON pr.id = rv.proposal_id "
    "JOIN listings_listing l ON l.person_id = pr.person_id"
)
NOTIFICATION = (
    "SELECT l.id FROM {rows} r JOIN safety_rightsrectificationnotification n ON n.id = r.{column} "
    "JOIN safety_rightsrectificationreview rv ON rv.id = n.review_id "
    "JOIN safety_rightsrectificationproposal pr ON pr.id = rv.proposal_id "
    "JOIN listings_listing l ON l.person_id = pr.person_id"
)
EXECUTION = (
    "SELECT l.id FROM {rows} r JOIN safety_rightsrectificationexecution e ON e.id = r.{column} "
    "JOIN safety_rightsrectificationnotification n ON n.id = e.notification_id "
    "JOIN safety_rightsrectificationreview rv ON rv.id = n.review_id "
    "JOIN safety_rightsrectificationproposal pr ON pr.id = rv.proposal_id "
    "JOIN listings_listing l ON l.person_id = pr.person_id"
)

# Every table read by moderation.publicly_visible (captured from executed SQL, plus the
# postal/zone catalog tables). Each entry maps changed rows to the listings they affect.
DEPENDENCIES = {
    "listings_listing": ["SELECT r.id FROM {rows} r"],
    "listings_revision": ["SELECT r.listing_id FROM {rows} r"],
    "listings_revision_categories": [VIA_REVISION.replace("{column}", "revision_id")],
    "listings_revision_services": [VIA_REVISION.replace("{column}", "revision_id")],
    "listings_revision_travel_areas": [VIA_REVISION.replace("{column}", "revision_id")],
    "listings_rate": [VIA_REVISION.replace("{column}", "revision_id")],
    "mediafiles_photo": [VIA_REVISION.replace("{column}", "revision_id")],
    "mediafiles_blob": [
        "SELECT v.listing_id FROM {rows} r JOIN mediafiles_photo p ON p.blob_id = r.id "
        "JOIN listings_revision v ON v.id = p.revision_id"
    ],
    "mediafiles_match": [
        VIA_PHOTO.replace("{column}", "photo_id"),
        VIA_PHOTO.replace("{column}", "candidate_id"),
    ],
    "core_person": ["SELECT l.id FROM {rows} r JOIN listings_listing l ON l.person_id = r.id"],
    "core_phoneclaim": [
        "SELECT l.id FROM {rows} r JOIN core_person p ON p.phone_claim_id = r.id "
        "JOIN listings_listing l ON l.person_id = p.id"
    ],
    "core_agency": [
        "SELECT l.id FROM {rows} r JOIN core_person p ON p.agency_id = r.id "
        "JOIN listings_listing l ON l.person_id = p.id"
    ],
    "core_legalacceptance": [
        "SELECT v.listing_id FROM {rows} r JOIN listings_revision v "
        "ON v.publisher_acceptance_id = r.id"
    ],
    "core_legaldocument": [ALL],
    "core_representationaction": [VIA_PERSON.replace("{column}", "person_id")],
    "core_verificationcheck": [VIA_PERSON.replace("{column}", "person_id")],
    "safety_privacypublicationhold": [VIA_PERSON.replace("{column}", "person_id")],
    "safety_restriction": ["SELECT r.listing_id FROM {rows} r"],
    "safety_rightsphotoreintroduction": [VIA_PHOTO.replace("{column}", "photo_id")],
    "safety_rightsrectificationproposal": [
        VIA_PERSON.replace("{column}", "person_id"),
        VIA_REVISION.replace("{column}", "source_revision_id"),
    ],
    "safety_rightsrectificationreview": [PROPOSAL.replace("{column}", "proposal_id")],
    "safety_rightsrectificationnotification": [REVIEW.replace("{column}", "review_id")],
    "safety_rightsrectificationexecution": [
        NOTIFICATION.replace("{column}", "notification_id"),
        VIA_REVISION.replace("{column}", "corrected_revision_id"),
    ],
    "safety_rightsrectificationphotoupload": [VIA_PHOTO.replace("{column}", "photo_id")],
    "safety_rightsrectificationphotodisposition": [
        VIA_PHOTO.replace("{column}", "source_photo_id"),
        EXECUTION.replace("{column}", "execution_id"),
    ],
    "catalog_category": [ALL],
    "catalog_service": [ALL],
    "catalog_region": [ALL],
    "catalog_province": [ALL],
    "catalog_municipality": [ALL],
    "catalog_postalcode": [ALL],
    "catalog_postalcode_municipalities": [ALL],
    "catalog_zone": [ALL],
}

MARK = """
CREATE SEQUENCE IF NOT EXISTS listings_publication_generation;
CREATE OR REPLACE FUNCTION listings_publication_mark(ids uuid[]) RETURNS void AS $$
BEGIN
  INSERT INTO listings_publicationdirty (listing_id, generation)
  SELECT id, nextval('listings_publication_generation')
  FROM (SELECT DISTINCT unnest(ids) AS id) AS changed WHERE id IS NOT NULL
  ON CONFLICT (listing_id) DO UPDATE SET generation = EXCLUDED.generation;
END $$ LANGUAGE plpgsql;
"""


def trigger_sql(table, mappings):
    def collect(rows):
        return " UNION ".join(sql.format(rows=rows) for sql in mappings)

    function = f"lpd_{table}"
    body = f"""
CREATE OR REPLACE FUNCTION {function}() RETURNS trigger AS $$
BEGIN
  IF TG_OP IN ('INSERT', 'UPDATE') THEN
    PERFORM listings_publication_mark(ARRAY({collect('new_rows')}));
  END IF;
  IF TG_OP IN ('UPDATE', 'DELETE') THEN
    PERFORM listings_publication_mark(ARRAY({collect('old_rows')}));
  END IF;
  RETURN NULL;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER {function}_i AFTER INSERT ON {table}
  REFERENCING NEW TABLE AS new_rows FOR EACH STATEMENT EXECUTE FUNCTION {function}();
CREATE TRIGGER {function}_u AFTER UPDATE ON {table}
  REFERENCING OLD TABLE AS old_rows NEW TABLE AS new_rows FOR EACH STATEMENT EXECUTE FUNCTION {function}();
CREATE TRIGGER {function}_d AFTER DELETE ON {table}
  REFERENCING OLD TABLE AS old_rows FOR EACH STATEMENT EXECUTE FUNCTION {function}();
CREATE TRIGGER {function}_t AFTER TRUNCATE ON {table}
  FOR EACH STATEMENT EXECUTE FUNCTION listings_publication_truncated();
"""
    reverse = f"DROP FUNCTION IF EXISTS {function}() CASCADE;"
    return body, reverse


TRUNCATE = """
CREATE OR REPLACE FUNCTION listings_publication_truncated() RETURNS trigger AS $$
BEGIN
  PERFORM listings_publication_mark(ARRAY(SELECT id FROM listings_listing));
  RETURN NULL;
END $$ LANGUAGE plpgsql;
"""

forward = [MARK, TRUNCATE]
backward = []
for table, mappings in DEPENDENCIES.items():
    body, reverse = trigger_sql(table, mappings)
    forward.append(body)
    backward.insert(0, reverse)
backward += [
    "DROP FUNCTION IF EXISTS listings_publication_truncated() CASCADE;",
    "DROP FUNCTION IF EXISTS listings_publication_mark(uuid[]);",
    "DROP SEQUENCE IF EXISTS listings_publication_generation;",
]


class Migration(migrations.Migration):
    dependencies = [
        ("listings", "0014_rate_rate_text_unknown_v1_and_more"),
        ("core", "0015_user_account_erased_at"),
        ("catalog", "0005_promotionentitlement_last_checked_at"),
        ("mediafiles", "0010_preparation_cleanup"),
        ("safety", "0110_recipient_execution_notices"),
    ]

    operations = [
        migrations.CreateModel(
            name="PublicationDirty",
            fields=[
                ("listing_id", models.UUIDField(primary_key=True, serialize=False)),
                ("generation", models.BigIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name="PublicationState",
            fields=[
                (
                    "listing",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="publication_state",
                        serialize=False,
                        to="listings.listing",
                    ),
                ),
                ("eligible", models.BooleanField()),
                ("rules_version", models.CharField(max_length=64)),
                ("check_age", models.BooleanField(default=False)),
                ("check_contact", models.BooleanField(default=False)),
                ("check_agency", models.BooleanField(default=False)),
                ("computed_at", models.DateTimeField()),
                (
                    "revision",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="listings.revision",
                    ),
                ),
            ],
        ),
        migrations.RunSQL(forward, backward),
        # Small, high-churn queue: vacuum and analyze it eagerly.
        migrations.RunSQL(
            "ALTER TABLE listings_publicationdirty SET (autovacuum_vacuum_scale_factor = 0, "
            "autovacuum_vacuum_threshold = 200, autovacuum_analyze_scale_factor = 0, "
            "autovacuum_analyze_threshold = 200)",
            migrations.RunSQL.noop,
        ),
        # Existing listings start unknown: everything is evaluated natively until computed.
        migrations.RunSQL(
            "SELECT listings_publication_mark(ARRAY(SELECT id FROM listings_listing));",
            migrations.RunSQL.noop,
        ),
    ]
