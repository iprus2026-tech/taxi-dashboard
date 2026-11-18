"""Pure quality engine for driver location fixes (TAXI-GNSS-QUALITY-01, milestone 1).

The module validates and classifies one ``DriverLocationFixV1`` sample at a time.
The contract is documented in ``docs/gnss/QUALITY-CONTRACT.md``.

Design rules:

* Pure and side-effect free: no Flask, no file/network I/O, no logging, no
  printing, no clock reads, no global mutable state. Every input that affects
  a decision (``received_at``, the previous anchor fix, limits) is passed in
  explicitly, so the same inputs always give the same result.
* Not connected to ``app.py``, ``static/script.js`` or any stored driver state.
  Nothing in production imports this module in milestone 1.
* No fabricated provenance: ``source`` is copied from the caller only when it
  is one of the four enum values, and satellite constellation fields are not
  part of v1 at all (they are rejected, never inferred).
* No silent precision loss: coordinates and measurements are kept exactly as
  received (finite JSON numbers), timestamps with more than microsecond
  precision are rejected instead of truncated.
* Valid measurement, distance contribution and discarded/suspect fixes are
  reported separately (see ``Disposition``).
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping, Optional, Tuple

__all__ = [
    "SCHEMA_NAME",
    "SOURCES",
    "EARTH_RADIUS_M",
    "Disposition",
    "Issue",
    "QualityConfig",
    "DEFAULT_CONFIG",
    "NormalizedFix",
    "FixEvaluation",
    "SequenceResult",
    "decode_fix_json",
    "normalize_fix",
    "classify_fix",
    "evaluate_fix",
    "evaluate_sequence",
    "haversine_m",
]

SCHEMA_NAME = "DriverLocationFixV1"

# Where the caller says the fix came from. Never inferred by this module.
SOURCES = frozenset(
    {"browser_geolocation", "android_location", "external_gnss", "unknown"}
)

# Same spherical radius as app.py, so future integration does not change the
# distance model silently. Haversine on a sphere is an approximation (error
# up to roughly 0.5 % against the WGS84 ellipsoid).
EARTH_RADIUS_M = 6_371_000.0

MAX_POINT_ID_LENGTH = 64
MAX_JSON_BYTES = 4096

# Always applied with ``fullmatch``: ``$`` would also match before a trailing
# "\n", which let "abc\n" and a 65-character "a"*64 + "\n" through (F3).
_POINT_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}", re.ASCII)
# RFC 3339 profile: explicit offset required, at most 6 fractional digits.
# ASCII digits only and ``fullmatch`` (no trailing newline). Field ranges are
# checked explicitly in ``_parse_timestamp`` instead of relying on
# ``datetime.fromisoformat``, whose accepted forms differ between Python
# versions (3.14 accepts hour 24 as next-day midnight, F1) and which turns an
# offset minute of 60 into a whole hour (F2).
_TIMESTAMP_RE = re.compile(
    r"(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})"
    r"T(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"(?:\.(?P<fraction>[0-9]{1,6}))?"
    r"(?:Z|(?P<sign>[+-])(?P<off_hour>[0-9]{2}):(?P<off_minute>[0-9]{2}))",
    re.ASCII,
)

_REQUIRED_FIELDS = ("point_id", "lat", "lng", "captured_at", "source")
_OPTIONAL_FIELDS = (
    "schema",
    "accuracy_m",
    "speed_mps",
    "heading_deg",
    "altitude_m",
    "altitude_accuracy_m",
    "new_segment",
)
_KNOWN_FIELDS = frozenset(_REQUIRED_FIELDS + _OPTIONAL_FIELDS)
# Names that would claim satellite provenance. Not supported in v1.
_CONSTELLATION_FIELDS = frozenset(
    {
        "constellation",
        "constellations",
        "gnss_system",
        "gnss_systems",
        "satellites",
        "satellites_used",
        "used_in_fix",
    }
)

# (lower, lower_inclusive, upper, upper_inclusive) for numeric fields.
_RANGES = {
    "lat": (-90.0, True, 90.0, True),
    "lng": (-180.0, True, 180.0, True),
    "accuracy_m": (0.0, False, 100_000.0, True),
    "speed_mps": (0.0, True, 120.0, True),
    "heading_deg": (0.0, True, 360.0, False),
    "altitude_m": (-1_000.0, True, 10_000.0, True),
    "altitude_accuracy_m": (0.0, False, 100_000.0, True),
}


class Disposition:
    """Classification outcome. Plain string constants (immutable)."""

    REJECTED = "REJECTED"  # not a valid measurement
    DISCARDED = "DISCARDED"  # valid measurement, not usable for distance
    SUSPECT = "SUSPECT"  # valid measurement, physically implausible
    ACCEPTED_SEGMENT_START = "ACCEPTED_SEGMENT_START"  # anchor, 0 m
    ACCEPTED_STATIONARY = "ACCEPTED_STATIONARY"  # within jitter, 0 m
    ACCEPTED_MOVEMENT = "ACCEPTED_MOVEMENT"  # contributes distance

    ALL = (
        REJECTED,
        DISCARDED,
        SUSPECT,
        ACCEPTED_SEGMENT_START,
        ACCEPTED_STATIONARY,
        ACCEPTED_MOVEMENT,
    )


@dataclass(frozen=True)
class Issue:
    """One validation problem: which field and a stable reason code."""

    field: str
    code: str


@dataclass(frozen=True)
class QualityConfig:
    """Explicit, configurable limits. All durations in seconds, lengths in metres."""

    max_age_s: float = 300.0
    max_future_skew_s: float = 5.0
    max_accuracy_m: float = 80.0
    max_speed_mps: float = 70.0
    max_gap_s: float = 120.0
    min_movement_m: float = 3.0
    jitter_accuracy_factor: float = 1.0

    def __post_init__(self) -> None:
        for name in (
            "max_age_s",
            "max_future_skew_s",
            "max_accuracy_m",
            "max_speed_mps",
            "max_gap_s",
            "min_movement_m",
            "jitter_accuracy_factor",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be a number")
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and >= 0")
        if self.max_accuracy_m == 0 or self.max_speed_mps == 0 or self.max_gap_s == 0:
            raise ValueError("max_accuracy_m, max_speed_mps and max_gap_s must be > 0")


DEFAULT_CONFIG = QualityConfig()


@dataclass(frozen=True)
class NormalizedFix:
    """Canonical v1 fix. Coordinates are hidden from repr to avoid accidental logging."""

    point_id: str = field(repr=False)
    lat: float = field(repr=False)
    lng: float = field(repr=False)
    captured_at: datetime
    received_at: datetime
    source: str
    accuracy_m: Optional[float] = None
    speed_mps: Optional[float] = None
    heading_deg: Optional[float] = None
    altitude_m: Optional[float] = field(default=None, repr=False)
    altitude_accuracy_m: Optional[float] = None
    new_segment: bool = False

    def to_dict(self) -> dict:
        """Canonical JSON-ready form. Timestamps in UTC with ``Z``; no rounding."""
        return {
            "schema": SCHEMA_NAME,
            "point_id": self.point_id,
            "lat": self.lat,
            "lng": self.lng,
            "captured_at": _format_utc(self.captured_at),
            "received_at": _format_utc(self.received_at),
            "source": self.source,
            "accuracy_m": self.accuracy_m,
            "speed_mps": self.speed_mps,
            "heading_deg": self.heading_deg,
            "altitude_m": self.altitude_m,
            "altitude_accuracy_m": self.altitude_accuracy_m,
            "new_segment": self.new_segment,
        }


@dataclass(frozen=True)
class FixEvaluation:
    """Result of evaluating one fix against the previous accepted anchor.

    * ``valid_measurement`` - the payload passed schema, range and time checks.
    * ``distance_contribution_m`` - metres this fix adds to a track; > 0 only
      for ``ACCEPTED_MOVEMENT``.
    * ``disposition`` / ``reasons`` - why the fix was used, discarded or
      flagged as suspect.
    * ``next_anchor`` - the fix the caller must pass as ``previous`` next time
      (either this fix or the unchanged previous anchor).
    """

    disposition: str
    valid_measurement: bool
    distance_contribution_m: float
    reasons: Tuple[str, ...]
    issues: Tuple[Issue, ...] = ()
    fix: Optional[NormalizedFix] = None
    next_anchor: Optional[NormalizedFix] = None
    starts_new_segment: bool = False
    raw_distance_m: Optional[float] = None
    elapsed_s: Optional[float] = None
    derived_speed_mps: Optional[float] = None


@dataclass(frozen=True)
class SequenceResult:
    """Fold of ``evaluate_fix`` over an ordered batch of fixes."""

    evaluations: Tuple[FixEvaluation, ...]
    total_distance_m: float
    final_anchor: Optional[NormalizedFix]


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance on a sphere of ``EARTH_RADIUS_M``, in metres (unrounded)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(d_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
    )
    return 2.0 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


def _parse_timestamp(value: Any) -> Tuple[Optional[datetime], Optional[str]]:
    """Parse a strict RFC 3339 string with explicit offset into aware UTC."""
    if not isinstance(value, str):
        return None, "INVALID_TYPE"
    match = _TIMESTAMP_RE.fullmatch(value)
    if match is None:
        if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$", value):
            return None, "TIMEZONE_NAIVE"
        if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{7,}", value):
            return None, "PRECISION_UNSUPPORTED"
        return None, "INVALID_FORMAT"
    hour = int(match["hour"])
    minute = int(match["minute"])
    second = int(match["second"])
    # RFC 3339 section 5.6: time-hour 00-23, time-minute 00-59, time-second
    # 00-59 (leap second 60 is not supported) and the same hour/minute ranges
    # for the numeric offset. Out-of-range values are rejected, never rolled
    # over into the next day or into a shifted offset hour.
    if hour > 23 or minute > 59 or second > 59:
        return None, "INVALID_VALUE"
    offset = timedelta(0)
    if match["sign"] is not None:
        off_hour = int(match["off_hour"])
        off_minute = int(match["off_minute"])
        if off_hour > 23 or off_minute > 59:
            return None, "INVALID_VALUE"
        offset = timedelta(hours=off_hour, minutes=off_minute)
        if match["sign"] == "-":
            offset = -offset
    fraction = match["fraction"]
    microsecond = int(fraction.ljust(6, "0")) if fraction else 0
    try:
        parsed = datetime(
            int(match["year"]),
            int(match["month"]),
            int(match["day"]),
            hour,
            minute,
            second,
            microsecond,
            tzinfo=timezone(offset),
        )
        # Year 1 / year 9999 with an offset can fall outside datetime's range in UTC.
        return parsed.astimezone(timezone.utc), None
    except (ValueError, OverflowError):
        return None, "INVALID_VALUE"


def _coerce_received_at(value: Any) -> datetime:
    """``received_at`` is caller-supplied (server clock); programmer errors raise."""
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("received_at must be timezone-aware")
        return value.astimezone(timezone.utc)
    parsed, error = _parse_timestamp(value)
    if parsed is None:
        raise ValueError(f"received_at is invalid: {error}")
    return parsed


def _check_number(name: str, value: Any) -> Tuple[Optional[float], Optional[str]]:
    # bool is a subclass of int in Python; JSON true/false are not numbers.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, "INVALID_TYPE"
    try:
        number = float(value)
    except OverflowError:
        return None, "OUT_OF_RANGE"
    if not math.isfinite(number):
        return None, "NOT_FINITE"
    low, low_inc, high, high_inc = _RANGES[name]
    if (number < low) or (number == low and not low_inc):
        return None, "OUT_OF_RANGE"
    if (number > high) or (number == high and not high_inc):
        return None, "OUT_OF_RANGE"
    return number, None


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------


def decode_fix_json(raw: Any) -> Tuple[Any, Tuple[Issue, ...]]:
    """Decode a raw JSON document strictly (pure: works on the given bytes/str).

    Rejects NaN/Infinity tokens (Python's ``json`` accepts them by default),
    duplicate keys, invalid UTF-8 and documents above ``MAX_JSON_BYTES``.
    Returns ``(value, ())`` on success or ``(None, issues)``.
    """
    if isinstance(raw, (bytes, bytearray)):
        if len(raw) > MAX_JSON_BYTES:
            return None, (Issue("$", "PAYLOAD_TOO_LARGE"),)
        try:
            text = bytes(raw).decode("utf-8")
        except UnicodeDecodeError:
            return None, (Issue("$", "INVALID_UTF8"),)
    elif isinstance(raw, str):
        if len(raw.encode("utf-8", "surrogatepass")) > MAX_JSON_BYTES:
            return None, (Issue("$", "PAYLOAD_TOO_LARGE"),)
        text = raw
    else:
        return None, (Issue("$", "INVALID_TYPE"),)

    class _Reject(Exception):
        def __init__(self, code: str) -> None:
            super().__init__(code)
            self.code = code

    def _no_constants(token: str) -> Any:
        raise _Reject("NOT_FINITE")

    def _no_duplicates(pairs: list) -> dict:
        result: dict = {}
        for key, item in pairs:
            if key in result:
                raise _Reject("DUPLICATE_KEY")
            result[key] = item
        return result

    try:
        value = json.loads(
            text, parse_constant=_no_constants, object_pairs_hook=_no_duplicates
        )
    except _Reject as exc:
        return None, (Issue("$", exc.code),)
    except (ValueError, RecursionError):
        return None, (Issue("$", "MALFORMED_JSON"),)
    return value, ()


def normalize_fix(
    payload: Any, *, received_at: Any
) -> Tuple[Optional[NormalizedFix], Tuple[Issue, ...]]:
    """Validate a decoded JSON object and build a canonical ``NormalizedFix``.

    Only shape, type, range and timestamp-format checks happen here; freshness
    relative to ``received_at`` is checked in ``evaluate_fix``. Returns
    ``(fix, ())`` or ``(None, issues)``. Issues are in a deterministic order.
    """
    received = _coerce_received_at(received_at)
    if not isinstance(payload, Mapping):
        return None, (Issue("$", "PAYLOAD_NOT_OBJECT"),)

    issues = []
    for key in sorted(k for k in payload.keys() if isinstance(k, str)):
        if key in _CONSTELLATION_FIELDS:
            issues.append(Issue(key, "CONSTELLATION_NOT_SUPPORTED_V1"))
        elif key not in _KNOWN_FIELDS:
            issues.append(Issue(key, "UNKNOWN_FIELD"))
    if any(not isinstance(k, str) for k in payload.keys()):
        issues.append(Issue("$", "NON_STRING_KEY"))

    for name in _REQUIRED_FIELDS:
        if name not in payload or payload[name] is None:
            issues.append(Issue(name, "MISSING"))

    values: dict = {}

    if "schema" in payload and payload["schema"] != SCHEMA_NAME:
        issues.append(Issue("schema", "UNSUPPORTED_SCHEMA"))

    point_id = payload.get("point_id")
    if point_id is not None:
        if not isinstance(point_id, str):
            issues.append(Issue("point_id", "INVALID_TYPE"))
        elif not _POINT_ID_RE.fullmatch(point_id):
            issues.append(Issue("point_id", "INVALID_FORMAT"))
        else:
            values["point_id"] = point_id

    for name in ("lat", "lng"):
        if payload.get(name) is not None:
            number, code = _check_number(name, payload[name])
            if code:
                issues.append(Issue(name, code))
            else:
                values[name] = number

    for name in ("accuracy_m", "speed_mps", "heading_deg", "altitude_m", "altitude_accuracy_m"):
        if payload.get(name) is not None:
            number, code = _check_number(name, payload[name])
            if code:
                issues.append(Issue(name, code))
            else:
                values[name] = number
        else:
            values[name] = None

    if payload.get("captured_at") is not None:
        parsed, code = _parse_timestamp(payload["captured_at"])
        if code:
            issues.append(Issue("captured_at", code))
        else:
            values["captured_at"] = parsed

    source = payload.get("source")
    if source is not None:
        if not isinstance(source, str) or source not in SOURCES:
            issues.append(Issue("source", "INVALID_SOURCE"))
        else:
            values["source"] = source

    # Absent -> False. An explicit JSON null is a type error, not "false" (F4).
    new_segment = payload.get("new_segment", False)
    if not isinstance(new_segment, bool):
        issues.append(Issue("new_segment", "INVALID_TYPE"))
    values["new_segment"] = new_segment is True

    if issues:
        return None, tuple(issues)

    return (
        NormalizedFix(
            point_id=values["point_id"],
            lat=values["lat"],
            lng=values["lng"],
            captured_at=values["captured_at"],
            received_at=received,
            source=values["source"],
            accuracy_m=values["accuracy_m"],
            speed_mps=values["speed_mps"],
            heading_deg=values["heading_deg"],
            altitude_m=values["altitude_m"],
            altitude_accuracy_m=values["altitude_accuracy_m"],
            new_segment=values["new_segment"],
        ),
        (),
    )


def _rejected(issues: Tuple[Issue, ...], previous: Optional[NormalizedFix]) -> FixEvaluation:
    reasons = tuple(dict.fromkeys(i.code for i in issues))
    return FixEvaluation(
        disposition=Disposition.REJECTED,
        valid_measurement=False,
        distance_contribution_m=0.0,
        reasons=reasons,
        issues=issues,
        next_anchor=previous,
    )


def classify_fix(
    fix: NormalizedFix,
    previous: Optional[NormalizedFix] = None,
    config: QualityConfig = DEFAULT_CONFIG,
) -> FixEvaluation:
    """Classify a normalized fix against the previous accepted anchor.

    ``previous`` must be the ``next_anchor`` returned by the previous call (or
    ``None`` at the start of tracking). Freshness is checked here, using the
    fix's own ``received_at``.
    """
    if not isinstance(fix, NormalizedFix):
        raise TypeError("fix must be a NormalizedFix")
    if previous is not None:
        if not isinstance(previous, NormalizedFix):
            raise TypeError("previous must be a NormalizedFix or None")
        if previous.accuracy_m is None:
            raise ValueError("previous must be an accepted anchor (accuracy_m set)")
    if not isinstance(config, QualityConfig):
        raise TypeError("config must be a QualityConfig")

    # 1. Freshness against the caller-supplied server receive time.
    age_s = (fix.received_at - fix.captured_at).total_seconds()
    if age_s > config.max_age_s:
        return _rejected((Issue("captured_at", "FIX_STALE"),), previous)
    if -age_s > config.max_future_skew_s:
        return _rejected((Issue("captured_at", "FIX_IN_FUTURE"),), previous)

    def discarded(code: str, disposition: str = Disposition.DISCARDED, **extra: Any) -> FixEvaluation:
        return FixEvaluation(
            disposition=disposition,
            valid_measurement=True,
            distance_contribution_m=0.0,
            reasons=(code,),
            fix=fix,
            next_anchor=previous,
            **extra,
        )

    # 2. Idempotency and ordering relative to the anchor.
    if previous is not None:
        if fix.point_id == previous.point_id:
            ignore = {"received_at": None}
            same = (fix.to_dict() | ignore) == (previous.to_dict() | ignore)
            return discarded("DUPLICATE_POINT_ID" if same else "POINT_ID_CONFLICT")
        if fix.captured_at < previous.captured_at:
            return discarded("OUT_OF_ORDER")
        if fix.captured_at == previous.captured_at:
            return discarded("NON_INCREASING_TIMESTAMP")

    # 3. Reported horizontal accuracy.
    if fix.accuracy_m is None:
        return discarded("ACCURACY_MISSING")
    if fix.accuracy_m > config.max_accuracy_m:
        return discarded("ACCURACY_INSUFFICIENT")

    def segment_start(code: str, **extra: Any) -> FixEvaluation:
        return FixEvaluation(
            disposition=Disposition.ACCEPTED_SEGMENT_START,
            valid_measurement=True,
            distance_contribution_m=0.0,
            reasons=(code,),
            fix=fix,
            next_anchor=fix,
            starts_new_segment=True,
            **extra,
        )

    # 4. Segment boundaries.
    if previous is None:
        return segment_start("FIRST_FIX")

    elapsed_s = (fix.captured_at - previous.captured_at).total_seconds()
    distance_m = haversine_m(previous.lat, previous.lng, fix.lat, fix.lng)
    geometry = {"raw_distance_m": distance_m, "elapsed_s": elapsed_s}

    # Movement inside the combined reported uncertainty is jitter, not distance.
    combined_accuracy = math.hypot(previous.accuracy_m, fix.accuracy_m)
    jitter_threshold = max(
        config.min_movement_m, config.jitter_accuracy_factor * combined_accuracy
    )

    if fix.new_segment:
        return segment_start("SEGMENT_REQUESTED", **geometry)
    if elapsed_s > config.max_gap_s:
        if distance_m <= jitter_threshold:
            # Long stationary period: refresh the anchor in place, no track break.
            return FixEvaluation(
                disposition=Disposition.ACCEPTED_STATIONARY,
                valid_measurement=True,
                distance_contribution_m=0.0,
                reasons=("STATIONARY_REANCHOR",),
                fix=fix,
                next_anchor=fix,
                **geometry,
            )
        return segment_start("GAP_NEW_SEGMENT", **geometry)

    derived_speed = distance_m / elapsed_s
    geometry["derived_speed_mps"] = derived_speed

    # 5. Jitter within the gap limit: anchor stays, so slow motion still accumulates.
    if distance_m <= jitter_threshold:
        return discarded(
            "STATIONARY_JITTER", Disposition.ACCEPTED_STATIONARY, **geometry
        )

    # 6. Physically implausible jump, after giving the benefit of the accuracy doubt.
    effective_speed = max(0.0, distance_m - combined_accuracy) / elapsed_s
    if effective_speed > config.max_speed_mps:
        return discarded("IMPLAUSIBLE_SPEED", Disposition.SUSPECT, **geometry)

    return FixEvaluation(
        disposition=Disposition.ACCEPTED_MOVEMENT,
        valid_measurement=True,
        distance_contribution_m=distance_m,
        reasons=("MOVEMENT",),
        fix=fix,
        next_anchor=fix,
        **geometry,
    )


def evaluate_fix(
    payload: Any,
    *,
    received_at: Any,
    previous: Optional[NormalizedFix] = None,
    config: QualityConfig = DEFAULT_CONFIG,
) -> FixEvaluation:
    """Normalize and classify one decoded payload (or raw JSON str/bytes)."""
    if isinstance(payload, (str, bytes, bytearray)):
        payload, issues = decode_fix_json(payload)
        if issues:
            _coerce_received_at(received_at)
            return _rejected(issues, previous)
    fix, issues = normalize_fix(payload, received_at=received_at)
    if fix is None:
        return _rejected(issues, previous)
    return classify_fix(fix, previous, config)


def evaluate_sequence(
    items: Iterable[Tuple[Any, Any]],
    *,
    previous: Optional[NormalizedFix] = None,
    config: QualityConfig = DEFAULT_CONFIG,
) -> SequenceResult:
    """Evaluate ``(payload, received_at)`` pairs in the given order.

    Pure fold: the returned total is the exact (``math.fsum``) sum of
    ``distance_contribution_m``; nothing is rounded or stored.
    """
    anchor = previous
    evaluations = []
    for payload, received_at in items:
        result = evaluate_fix(
            payload, received_at=received_at, previous=anchor, config=config
        )
        evaluations.append(result)
        anchor = result.next_anchor
    total = math.fsum(e.distance_contribution_m for e in evaluations)
    return SequenceResult(tuple(evaluations), total, anchor)
