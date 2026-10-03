"""Perceptual image similarity: regional pHash retrieval + ORB geometric confirmation.

Inputs are already-decoded Pillow images. No face recognition, no models, no network.
A hash hit is only a retrieval candidate; only confirm_match() provides geometric
evidence. All thresholds are experimental pending calibration on synthetic data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import imagehash
import numpy as np
from PIL import Image

HASH_WORK_MAX_SIDE = 512
ORB_MAX_SIDE = 960
ORB_MAX_FEATURES = 800
MIN_SIDE = 16

# Window width/height as fraction of each side; anchored start/center/end per axis.
WINDOW_FRACTIONS = (0.9, 0.8, 0.7)

FLAT_STD = 6.0
FLAT_GRADIENT = 2.0
WINDOW_FLAT_STD = 4.0

FULL_HASH_MAX_DISTANCE = 12
ROTATED_HASH_MAX_DISTANCE = 10
WINDOW_HASH_MAX_DISTANCE = 10

MIN_KEYPOINTS = 30
MAX_DESCRIPTOR_DISTANCE = 64
LOWE_RATIO = 0.75
MIN_GOOD_MATCHES = 15
MIN_INLIERS = 20
MIN_INLIER_RATIO = 0.35
RANSAC_REPROJ_PX = 4.0
MIN_SCALE = 0.33
MAX_SCALE = 3.0
MIN_INLIER_SPREAD = 0.04
MIN_OVERLAP = 0.45

_HASH_LIMIT = 1 << 64
_ROTATIONS = (
    Image.Transpose.ROTATE_90,
    Image.Transpose.ROTATE_180,
    Image.Transpose.ROTATE_270,
)


def _axis_windows():
    out = [(1.0, 0.0)]
    for f in WINDOW_FRACTIONS:
        for o in (0.0, (1.0 - f) / 2.0, 1.0 - f):
            out.append((f, round(o, 4)))
    return tuple(out)


_AXIS = _axis_windows()
_MAX_WINDOWS = len(_AXIS) ** 2


@dataclass(frozen=True)
class Signature:
    width: int
    height: int
    low_information: bool
    full_hash: int | None
    rotated_hashes: tuple[int, ...]
    # ((width_frac, x_offset, height_frac, y_offset), hash)
    window_hashes: tuple[tuple[tuple[float, float, float, float], int], ...]


@dataclass(frozen=True)
class CandidateResult:
    is_candidate: bool
    relation: str  # full, rotated, a_in_b, b_in_a, none, low_information
    distance: int | None
    window: tuple[float, float, float, float] | None


@dataclass(frozen=True)
class MatchResult:
    status: str  # confirmed, rejected, insufficient_information, unavailable
    reason: str
    keypoints_a: int = 0
    keypoints_b: int = 0
    good_matches: int = 0
    inliers: int = 0
    inlier_ratio: float = 0.0
    scale: float | None = None
    rotation_deg: float | None = None
    spread: float = 0.0
    overlap: float = 0.0


@dataclass(frozen=True)
class SimilarityResult:
    verdict: str  # match, candidate_only, no_match, low_information
    candidate: CandidateResult
    confirmation: MatchResult | None


def _to_gray(img, max_side):
    if not isinstance(img, Image.Image):
        raise TypeError("expected a PIL image")
    if img.width < 1 or img.height < 1:
        return None
    gray = img.convert("L")
    scale = max_side / max(gray.size)
    if scale < 1.0:
        size = (max(1, round(gray.width * scale)), max(1, round(gray.height * scale)))
        gray = gray.resize(size, Image.Resampling.BOX)
    return gray


def _is_low_information(arr):
    if arr.ndim != 2 or min(arr.shape) < MIN_SIDE:
        return True
    a = arr.astype(np.float32)
    if float(a.std()) < FLAT_STD:
        return True
    grad = float(np.abs(np.diff(a, axis=1)).mean() + np.abs(np.diff(a, axis=0)).mean())
    return grad < FLAT_GRADIENT


def _phash(img):
    bits = imagehash.phash(img, hash_size=8).hash.ravel()
    value = 0
    for bit in bits:
        value = (value << 1) | int(bool(bit))
    return value


def _hamming(a, b):
    return (a ^ b).bit_count()


def _valid_hash(value):
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value < _HASH_LIMIT


def compute_signature(img: Image.Image) -> Signature:
    gray = _to_gray(img, HASH_WORK_MAX_SIDE)
    empty = Signature(img.width, img.height, True, None, (), ())
    if gray is None:
        return empty
    arr = np.asarray(gray)
    if _is_low_information(arr):
        return empty
    rotated = tuple(_phash(gray.transpose(t)) for t in _ROTATIONS)
    h, w = arr.shape
    windows = []
    for fx, ox in _AXIS:
        for fy, oy in _AXIS:
            if fx == 1.0 and fy == 1.0:
                continue
            x0, x1 = round(ox * w), round((ox + fx) * w)
            y0, y1 = round(oy * h), round((oy + fy) * h)
            sub = arr[y0:y1, x0:x1]
            if min(sub.shape) < MIN_SIDE or float(sub.std()) < WINDOW_FLAT_STD:
                continue
            windows.append(((fx, ox, fy, oy), _phash(gray.crop((x0, y0, x1, y1)))))
    return Signature(img.width, img.height, False, _phash(gray), rotated, tuple(windows))


def _windows(sig):
    for item in tuple(sig.window_hashes or ())[:_MAX_WINDOWS]:
        if isinstance(item, tuple) and len(item) == 2 and _valid_hash(item[1]):
            yield item


def retrieval_hashes(sig: Signature) -> list[int]:
    # Keys to index for candidate lookup; empty for low-information images.
    if sig.low_information or not _valid_hash(sig.full_hash):
        return []
    return [sig.full_hash] + [h for _, h in _windows(sig)]


def compare_signatures(a: Signature, b: Signature) -> CandidateResult:
    if a.low_information or b.low_information:
        return CandidateResult(False, "low_information", None, None)
    if not (_valid_hash(a.full_hash) and _valid_hash(b.full_hash)):
        return CandidateResult(False, "low_information", None, None)
    hits = []

    def consider(h1, h2, limit, relation, window=None):
        if _valid_hash(h1) and _valid_hash(h2):
            d = _hamming(h1, h2)
            hits.append((d - limit, d, relation, window))

    consider(a.full_hash, b.full_hash, FULL_HASH_MAX_DISTANCE, "full")
    for h in tuple(b.rotated_hashes or ())[: len(_ROTATIONS)]:
        consider(a.full_hash, h, ROTATED_HASH_MAX_DISTANCE, "rotated")
    for key, h in _windows(b):
        consider(a.full_hash, h, WINDOW_HASH_MAX_DISTANCE, "a_in_b", key)
    for key, h in _windows(a):
        consider(b.full_hash, h, WINDOW_HASH_MAX_DISTANCE, "b_in_a", key)
    best = min(hits, key=lambda t: (t[0], t[1]))
    if best[0] <= 0:
        return CandidateResult(True, best[2], best[1], best[3])
    return CandidateResult(False, "none", best[1], None)


def _load_cv2():
    try:
        import cv2
    except ImportError:
        return None
    return cv2


def _validated(keypoints, descriptors):
    empty = (np.empty((0, 2), np.float32), np.empty((0, 32), np.uint8))
    if keypoints is None or descriptors is None:
        return empty
    des = np.asarray(descriptors)
    if des.dtype != np.uint8 or des.ndim != 2 or des.shape[1] != 32:
        return empty
    if des.shape[0] != len(keypoints):
        return empty
    n = min(des.shape[0], ORB_MAX_FEATURES)
    pts = np.array([keypoints[i].pt for i in range(n)], dtype=np.float32).reshape(-1, 2)
    if not np.isfinite(pts).all():
        return empty
    return pts, np.ascontiguousarray(des[:n])


def _orb_features(cv2, img):
    gray = _to_gray(img, ORB_MAX_SIDE)
    if gray is None:
        return None
    arr = np.ascontiguousarray(np.asarray(gray, dtype=np.uint8))
    if _is_low_information(arr):
        return None
    orb = cv2.ORB_create(nfeatures=ORB_MAX_FEATURES, scaleFactor=1.2, nlevels=8, fastThreshold=12)
    keypoints, descriptors = orb.detectAndCompute(arr, None)
    pts, des = _validated(keypoints, descriptors)
    return arr.shape, pts, des


def _good_matches(cv2, des_a, des_b, n_a, n_b):
    pairs = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False).knnMatch(des_a, des_b, k=2)
    best = {}
    for pair in pairs:
        if len(pair) < 2:
            continue
        m, n = pair[0], pair[1]
        if not (0 <= m.queryIdx < n_a and 0 <= m.trainIdx < n_b):
            continue
        if m.distance > MAX_DESCRIPTOR_DISTANCE or m.distance >= LOWE_RATIO * n.distance:
            continue
        prev = best.get(m.trainIdx)
        if prev is None or m.distance < prev.distance:
            best[m.trainIdx] = m
    return [best[k] for k in sorted(best)]


def _hull_fraction(cv2, pts, shape):
    area = float(shape[0] * shape[1])
    if len(pts) < 3 or area <= 0:
        return 0.0
    hull = cv2.convexHull(np.ascontiguousarray(pts, dtype=np.float32).reshape(-1, 1, 2))
    return float(cv2.contourArea(hull)) / area


def _overlap_fraction(cv2, matrix, shape_a, shape_b):
    (ha, wa), (hb, wb) = shape_a, shape_b
    corners = np.array([[0, 0], [wa, 0], [wa, ha], [0, ha]], dtype=np.float64)
    proj = (corners @ matrix[:, :2].T + matrix[:, 2]).astype(np.float32).reshape(-1, 1, 2)
    rect_b = np.array([[0, 0], [wb, 0], [wb, hb], [0, hb]], dtype=np.float32).reshape(-1, 1, 2)
    denom = min(abs(float(cv2.contourArea(proj))), float(wb * hb))
    if denom <= 0:
        return 0.0
    inter, _ = cv2.intersectConvexConvex(proj, rect_b)
    return max(0.0, min(1.0, float(inter) / denom))


def confirm_match(img_a: Image.Image, img_b: Image.Image) -> MatchResult:
    cv2 = _load_cv2()
    if cv2 is None:
        return MatchResult("unavailable", "opencv_not_installed")
    feats_a = _orb_features(cv2, img_a)
    feats_b = _orb_features(cv2, img_b)
    if feats_a is None or feats_b is None:
        return MatchResult("insufficient_information", "low_information_image")
    (shape_a, pts_a, des_a), (shape_b, pts_b, des_b) = feats_a, feats_b
    ka, kb = len(pts_a), len(pts_b)
    if min(ka, kb) < MIN_KEYPOINTS:
        return MatchResult("insufficient_information", "too_few_keypoints", ka, kb)
    matches = _good_matches(cv2, des_a, des_b, ka, kb)
    base = dict(keypoints_a=ka, keypoints_b=kb, good_matches=len(matches))
    if len(matches) < MIN_GOOD_MATCHES:
        return MatchResult("insufficient_information", "too_few_matches", **base)
    src = np.float32([pts_a[m.queryIdx] for m in matches])
    dst = np.float32([pts_b[m.trainIdx] for m in matches])
    matrix, mask = cv2.estimateAffinePartial2D(
        src,
        dst,
        method=cv2.RANSAC,
        ransacReprojThreshold=RANSAC_REPROJ_PX,
        maxIters=2000,
        confidence=0.995,
        refineIters=10,
    )
    if matrix is None or mask is None:
        return MatchResult("rejected", "no_geometric_model", **base)
    matrix = np.asarray(matrix, dtype=np.float64)
    mask = np.asarray(mask).reshape(-1).astype(bool)
    if matrix.shape != (2, 3) or not np.isfinite(matrix).all() or mask.shape[0] != len(matches):
        return MatchResult("rejected", "invalid_geometric_model", **base)
    src_in, dst_in = src[mask], dst[mask]
    inliers = min(
        len(np.unique(np.round(src_in), axis=0)),
        len(np.unique(np.round(dst_in), axis=0)),
    )
    ratio = inliers / len(matches)
    scale = math.hypot(matrix[0, 0], matrix[1, 0])
    rotation = math.degrees(math.atan2(matrix[1, 0], matrix[0, 0]))
    spread = min(_hull_fraction(cv2, src_in, shape_a), _hull_fraction(cv2, dst_in, shape_b))
    overlap = _overlap_fraction(cv2, matrix, shape_a, shape_b)
    details = dict(
        base,
        inliers=inliers,
        inlier_ratio=round(ratio, 4),
        scale=round(scale, 4),
        rotation_deg=round(rotation, 2),
        spread=round(spread, 4),
        overlap=round(overlap, 4),
    )
    if inliers < MIN_INLIERS:
        return MatchResult("insufficient_information", "too_few_inliers", **details)
    if ratio < MIN_INLIER_RATIO:
        return MatchResult("rejected", "low_inlier_ratio", **details)
    if not MIN_SCALE <= scale <= MAX_SCALE:
        return MatchResult("rejected", "implausible_scale", **details)
    if spread < MIN_INLIER_SPREAD:
        return MatchResult("rejected", "clustered_inliers", **details)
    if overlap < MIN_OVERLAP:
        return MatchResult("rejected", "low_overlap", **details)
    return MatchResult("confirmed", "consistent_similarity_transform", **details)


def compare_images(
    img_a: Image.Image,
    img_b: Image.Image,
    *,
    sig_a: Signature | None = None,
    sig_b: Signature | None = None,
    verify_all: bool = False,
) -> SimilarityResult:
    if sig_a is None:
        sig_a = compute_signature(img_a)
    if sig_b is None:
        sig_b = compute_signature(img_b)
    candidate = compare_signatures(sig_a, sig_b)
    if candidate.relation == "low_information":
        return SimilarityResult("low_information", candidate, None)
    if not candidate.is_candidate and not verify_all:
        return SimilarityResult("no_match", candidate, None)
    confirmation = confirm_match(img_a, img_b)
    if confirmation.status == "confirmed":
        return SimilarityResult("match", candidate, confirmation)
    verdict = "candidate_only" if candidate.is_candidate else "no_match"
    return SimilarityResult(verdict, candidate, confirmation)
