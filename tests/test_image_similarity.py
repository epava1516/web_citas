import io

import pytest
from PIL import Image
from test_photos import synthetic_image

from apps.mediafiles.similarity import compare_images, compute_signature


def jpeg(image, quality):
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=quality)
    return Image.open(io.BytesIO(output.getvalue())).convert("RGB")


@pytest.mark.parametrize("variant", ["q40", "q70", "left20", "top10-left10", "rotate90"])
def test_positive_recompression_and_crop_candidate_and_confirmation(variant):
    image = synthetic_image(43)
    if variant == "q40":
        edited = jpeg(image, 40)
    elif variant == "q70":
        edited = jpeg(image, 70)
    elif variant == "left20":
        edited = jpeg(image.crop((128, 0, 640, 480)), 70)
    elif variant == "top10-left10":
        edited = jpeg(image.crop((64, 48, 640, 480)), 70)
    else:
        edited = image.transpose(Image.Transpose.ROTATE_90)
    result = compare_images(image, edited)
    assert result.candidate.is_candidate, result
    assert result.verdict == "match", result


@pytest.mark.parametrize("seed", range(10, 20))
def test_unrelated_synthetic_images_never_confirm(seed):
    result = compare_images(synthetic_image(43), synthetic_image(seed), verify_all=True)
    assert result.verdict != "match", result


def test_flat_and_tiny_images_are_not_identity_matches():
    solid = Image.new("RGB", (640, 480), "white")
    assert compute_signature(solid).low_information
    assert compare_images(solid, solid).verdict == "low_information"
    tiny = Image.new("RGB", (1, 1), "black")
    assert compute_signature(tiny).low_information
