"""Explicit settings factory; no implicit network access or credential defaults."""

import base64
import json

import boto3
from botocore.config import Config
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from ..crypto import cipher
from .codec import Keyring
from .read_clients import client as read_client
from .repository import ObjectRepository


def repository():
    try:
        keys = {
            name: base64.b64decode(value, validate=True)
            for name, value in json.loads(settings.RIGHTS_OBJECT_KEYS).items()
        }
        ring = Keyring(keys, settings.RIGHTS_OBJECT_ACTIVE_KEY)
        ring.key(ring.active)
        if not settings.RIGHTS_OBJECT_ACCESS_KEY or not settings.RIGHTS_OBJECT_SECRET_KEY:
            raise ValueError("Missing object credentials")
    except (ValueError, AttributeError, TypeError) as error:
        raise ImproperlyConfigured("Independent private object keys required") from error
    client = read_client(lambda: boto3.client(
        "s3",
        endpoint_url=settings.RIGHTS_OBJECT_ENDPOINT,
        region_name=settings.RIGHTS_OBJECT_REGION,
        aws_access_key_id=settings.RIGHTS_OBJECT_ACCESS_KEY,
        aws_secret_access_key=settings.RIGHTS_OBJECT_SECRET_KEY,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=3,
            read_timeout=30,
            retries={"max_attempts": 2},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    ))
    return ObjectRepository(client, settings.RIGHTS_OBJECT_BUCKET, ring, cipher())
