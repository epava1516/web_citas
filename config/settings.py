import os
import re
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
APP_ENV = os.getenv("APP_ENV", "development")
PRODUCTION = APP_ENV == "production"
RECOVERY_MODE = os.getenv("RECOVERY_MODE", "0") == "1"
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1" and not PRODUCTION
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-development-only-change-before-any-deployment")
if PRODUCTION and (len(SECRET_KEY) < 50 or SECRET_KEY.startswith("local-")):
    raise ImproperlyConfigured("Production requires a strong independent secret")
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.catalog",
    "apps.listings",
    "apps.mediafiles",
    "apps.safety",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.core.middleware.RecoveryGateMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
    "apps.core.middleware.AccountGateMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context.environment",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "clasificados"),
        "USER": os.getenv("POSTGRES_USER", "clasificados"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "local-development-only"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "55432"),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }
}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
LANGUAGE_CODE = "es"
LANGUAGES = [("es", "Español"), ("en", "English")]
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_ROOT = BASE_DIR / "media" / "private"
MEDIA_URL = "/private-media/"
AUTH_USER_MODEL = "core.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "home"
# No implicit per-process personal-data store. Introduce response/data caching
# only with scoped keys, invalidation and retention covered by its contract.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
ACCESS_LOG_ORIGIN_BUNDLE = os.getenv("ACCESS_LOG_ORIGIN_BUNDLE", "")
ACCESS_REDIS_HISTORY_ORIGIN_BUNDLE = os.getenv("ACCESS_REDIS_HISTORY_ORIGIN_BUNDLE", "")
ACCESS_RESOURCE_ORIGIN_BUNDLE = os.getenv("ACCESS_RESOURCE_ORIGIN_BUNDLE", "")
SAFETY_NOTICE_BACKEND = os.getenv("SAFETY_NOTICE_BACKEND", "disabled")
ACCOUNT_CORRECTION_DELIVERY_BACKEND = os.getenv("ACCOUNT_CORRECTION_DELIVERY_BACKEND", "disabled")
RIGHTS_VERIFICATION_BACKEND = os.getenv("RIGHTS_VERIFICATION_BACKEND", "disabled")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@example.invalid")
PUBLIC_ORIGIN = os.getenv("PUBLIC_ORIGIN", "http://localhost:8000").rstrip("/")
VERIFICATION_PROVIDER = os.getenv("VERIFICATION_PROVIDER", "simulator")
PAYMENTS_ENABLED = os.getenv("PAYMENTS_ENABLED", "0") == "1"
if PAYMENTS_ENABLED:
    raise ImproperlyConfigured("Real payments are outside v1")
if PRODUCTION and VERIFICATION_PROVIDER == "simulator":
    raise ImproperlyConfigured("Simulator cannot be used in production")
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = PRODUCTION
CSRF_COOKIE_SECURE = PRODUCTION
SECURE_SSL_REDIRECT = PRODUCTION
SECURE_HSTS_SECONDS = 31536000 if PRODUCTION else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = PRODUCTION
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_AGE = 43200
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:56379/0")
TASK_QUEUE_GENERATION = os.getenv("TASK_QUEUE_GENERATION", "v1")
if not re.fullmatch(r"[a-z0-9]{1,32}", TASK_QUEUE_GENERATION):
    raise ImproperlyConfigured("Task queue generation must contain1–32 lowercase letters/digits")
CELERY_BROKER_TRANSPORT_OPTIONS = {"global_keyprefix": f"clasificados:{TASK_QUEUE_GENERATION}:"}
CELERY_TASK_DEFAULT_QUEUE = "clasificados"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_TIME_LIMIT = 120
CELERY_TASK_SOFT_TIME_LIMIT = 90

MFA_ENCRYPTION_KEY = os.getenv("MFA_ENCRYPTION_KEY", "")
if PRODUCTION and not MFA_ENCRYPTION_KEY:
    raise ImproperlyConfigured("Production requires independent MFA encryption key")

CELERY_BEAT_SCHEDULE = {
    "purge-access-field-decisions": {
        "task": "apps.safety.tasks.purge_expired_access_field_decision",
        "schedule": 60.0,
    },
    "reconcile-retention-reviews": {
        "task": "apps.safety.tasks.reconcile_retention_reviews",
        "schedule": 60.0,
    },
    "reconcile-urgent-report-alerts": {
        "task": "apps.safety.tasks.reconcile_urgent_report_alerts",
        "schedule": 60.0,
    },
    "cleanup-prepared-private-media": {
        "task": "apps.mediafiles.tasks.cleanup_prepared_media",
        "schedule": 60.0,
    },
    "erase-private-media": {"task": "apps.mediafiles.tasks.erase_media_files", "schedule": 60.0},
    "deliver-private-safety-notices": {
        "task": "apps.safety.tasks.deliver_safety_notices",
        "schedule": 60.0,
    },
    "purge-expired-account-confirmation-delivery": {
        "task": "apps.safety.tasks.purge_expired_account_confirmation_delivery",
        "schedule": 60.0,
    },
    "purge-expired-access-scope-inventory": {
        "task": "apps.safety.tasks.purge_expired_access_scope_inventory",
        "schedule": 60.0,
    },
    "purge-expired-access-coverage": {
        "task": "apps.safety.tasks.purge_expired_access_coverage",
        "schedule": 60.0,
    },
    "purge-expired-access-response-drafts": {
        "task": "apps.safety.tasks.purge_expired_access_response_drafts",
        "schedule": 60.0,
    },
    "purge-expired-portability-response-drafts": {
        "task": "apps.safety.tasks.purge_expired_portability_response_drafts",
        "schedule": 60.0,
    },
    "purge-expired-portability-coverage": {
        "task": "apps.safety.tasks.purge_expired_portability_coverage",
        "schedule": 60.0,
    },
    "purge-expired-portability-selections": {
        "task": "apps.safety.tasks.purge_expired_portability_selections",
        "schedule": 60.0,
    },
    "purge-expired-portability-assessments": {
        "task": "apps.safety.tasks.purge_expired_portability_assessments",
        "schedule": 60.0,
    },
    "purge-expired-copy-information": {
        "task": "apps.safety.tasks.purge_expired_copy_information",
        "schedule": 60.0,
    },
    "purge-expired-copy-page-reviews": {
        "task": "apps.safety.tasks.purge_expired_copy_page_reviews",
        "schedule": 60.0,
    },
    "purge-expired-private-copies": {
        "task": "apps.safety.tasks.purge_expired_exports",
        "schedule": 60.0,
    },
    "recover-private-media": {"task": "apps.mediafiles.tasks.recover_media_jobs", "schedule": 60.0},
    "expire-public-listings": {"task": "apps.listings.tasks.expire_listings", "schedule": 60.0},
}

if RECOVERY_MODE:
    CELERY_BEAT_SCHEDULE = {}
    # Beat otherwise installs backend_cleanup even with an empty schedule.
    CELERY_RESULT_EXPIRES = None

MEDIA_STORAGE_PROVIDER = os.getenv("MEDIA_STORAGE_PROVIDER", "local")
if MEDIA_STORAGE_PROVIDER == "s3":
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": os.environ["AWS_STORAGE_BUCKET_NAME"],
                "endpoint_url": os.getenv("AWS_S3_ENDPOINT_URL") or None,
                "region_name": os.getenv("AWS_S3_REGION_NAME", "eu-west-1"),
                "default_acl": "private",
                "querystring_auth": True,
                "file_overwrite": False,
            },
        },
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
elif MEDIA_STORAGE_PROVIDER != "local":
    raise ImproperlyConfigured("Unsupported media storage provider")

AGENCY_PENDING_PERSON_LIMIT = int(os.getenv("AGENCY_PENDING_PERSON_LIMIT", "10"))
if AGENCY_PENDING_PERSON_LIMIT < 1:
    raise ImproperlyConfigured("AGENCY_PENDING_PERSON_LIMIT must be positive")

SAFETY_ENCRYPTION_KEY = os.getenv("SAFETY_ENCRYPTION_KEY", "")
if PRODUCTION and not SAFETY_ENCRYPTION_KEY:
    raise ImproperlyConfigured("Safety encryption key required in production")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"private_requests": {"()": "config.private_logging.PrivateRequestFilter"}},
    "loggers": {
        "django.request": {"filters": ["private_requests"], "propagate": True},
        "django.security.csrf": {"filters": ["private_requests"], "propagate": True},
        "django.server": {"filters": ["private_requests"], "propagate": True},
    },
}

# Synthetic commercial flows require explicit local opt-in; services also reject production.
PROMOTION_TEST_MODE = os.getenv("PROMOTION_TEST_MODE", "0") == "1" and not PRODUCTION

if PROMOTION_TEST_MODE and not RECOVERY_MODE:
    CELERY_BEAT_SCHEDULE["synthetic-promotion-bumps"] = {"task": "apps.catalog.tasks.bump_promotions", "schedule": 60.0}
