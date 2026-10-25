"""Prepared query parity uses the real ORB and geometric comparator."""

import io
from dataclasses import asdict

import numpy as np
import pytest
from PIL import Image
from test_photos import synthetic_image

from apps.mediafiles import similarity


def _jpeg(image, quality):
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=quality)
    with Image.open(io.BytesIO(output.getvalue())) as decoded:
        return decoded.convert("RGB")


@pytest.mark.parametrize(
    "variant",
    ["identity", "q40", "q70", "left20", "top10-left10", "rotate90", "flat", "tiny"]
    + list(range(10, 20)),
)
def test_prepared_confirmation_preserves_every_result_field(variant):
    image = synthetic_image(43)
    if variant == "identity":
        other = image.copy()
    elif variant == "q40":
        other = _jpeg(image, 40)
    elif variant == "q70":
        other = _jpeg(image, 70)
    elif variant == "left20":
        other = _jpeg(image.crop((128, 0, 640, 480)), 70)
    elif variant == "top10-left10":
        other = _jpeg(image.crop((64, 48, 640, 480)), 70)
    elif variant == "rotate90":
        other = image.transpose(Image.Transpose.ROTATE_90)
    elif variant == "flat":
        other = Image.new("RGB", (640, 480), "white")
    elif variant == "tiny":
        other = Image.new("RGB", (1, 1), "black")
    else:
        other = synthetic_image(variant)
    expected = similarity.confirm_match(image, other)
    actual = similarity.confirm_match(image, other, prepared_query=similarity.prepare_query(image))
    assert asdict(actual) == asdict(expected)
    if variant in ("identity", "q40", "q70", "left20", "top10-left10", "rotate90"):
        assert actual.status == "confirmed"
    else:
        assert actual.status != "confirmed"


@pytest.mark.parametrize("size", [(640, 480), (1, 1), (0, 0)])
def test_prepared_low_information_query_preserves_fallback(size):
    image = Image.new("RGB", size, "white")
    other = synthetic_image(43)
    prepared = similarity.prepare_query(image)
    expected = similarity.confirm_match(image, other)
    actual = similarity.confirm_match(image, other, prepared_query=prepared)
    assert asdict(actual) == asdict(expected)
    assert actual == similarity.MatchResult("insufficient_information", "low_information_image")


def test_prepared_query_rejects_equal_but_distinct_image():
    image = synthetic_image(43)
    prepared = similarity.prepare_query(image)
    with pytest.raises(ValueError, match="belong to img_a"):
        similarity.confirm_match(image.copy(), image, prepared_query=prepared)
    with pytest.raises(ValueError, match="belong to img_a"):
        similarity.confirm_match(image, image, prepared_query=object())


def test_prepared_query_retains_unavailable_fallback(monkeypatch):
    monkeypatch.setattr(similarity, "_load_cv2", lambda: None)
    image = synthetic_image(43)
    prepared = similarity.prepare_query(image)
    assert similarity.confirm_match(image, image, prepared_query=prepared) == similarity.confirm_match(
        image, image
    ) == similarity.MatchResult("unavailable", "opencv_not_installed")


def test_prepared_query_reduces_feature_calls_and_is_not_mutated(monkeypatch):
    image = synthetic_image(43)
    others = [_jpeg(image, 40), image.transpose(Image.Transpose.ROTATE_90), synthetic_image(10)]
    original = similarity._orb_features
    calls = []

    def observe(cv2, img):
        calls.append(img)
        return original(cv2, img)

    monkeypatch.setattr(similarity, "_orb_features", observe)
    expected = [similarity.confirm_match(image, other) for other in others]
    assert len(calls) == 2 * len(others)
    calls.clear()
    prepared = similarity.prepare_query(image)
    assert prepared.features is not None
    _, points, descriptors = prepared.features
    before_points, before_descriptors = points.copy(), descriptors.copy()
    actual = [
        similarity.confirm_match(image, other, prepared_query=prepared) for other in others
    ]
    assert actual == expected
    assert len(calls) == len(others) + 1
    assert sum(img is image for img in calls) == 1
    assert not points.flags.writeable
    assert not descriptors.flags.writeable
    np.testing.assert_array_equal(points, before_points)
    np.testing.assert_array_equal(descriptors, before_descriptors)
