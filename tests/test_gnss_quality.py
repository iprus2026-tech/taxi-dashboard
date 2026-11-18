"""Regression tests for gnss_quality (TAXI-GNSS-QUALITY-01, milestone 1).

Synthetic fixtures only: every coordinate is generated arithmetically around
the WGS84 origin (0, 0) in open ocean, or at the mathematical range limits
(poles, antimeridian). No real driver route, address, device identifier or
recorded GPS payload is used. Nothing here starts Flask, reads or writes
driver_state.json / shift_history.json, touches the network or the clock.

Run from the repository root:
    python3 -m unittest tests.test_gnss_quality -v
    python3 -m pytest tests/test_gnss_quality.py
"""

from __future__ import annotations

import ast
import math
import os
import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import gnss_quality as gq  # noqa: E402
from gnss_quality import Disposition as D  # noqa: E402

T0 = datetime(2030, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
M_PER_DEG = gq.EARTH_RADIUS_M * math.pi / 180.0  # metres per degree of latitude


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def north(metres: float) -> float:
    """Latitude (deg) that lies ``metres`` north of the synthetic origin."""
    return metres / M_PER_DEG


def payload(n: int = 1, *, lat=0.0, lng=0.0, t: float = 0.0, **overrides):
    """Synthetic DriverLocationFixV1 payload ``t`` seconds after T0."""
    data = {
        "point_id": f"synthetic-{n:04d}",
        "lat": lat,
        "lng": lng,
        "captured_at": iso(T0 + timedelta(seconds=t)),
        "source": "browser_geolocation",
        "accuracy_m": 10.0,
    }
    data.update(overrides)
    return data


def received(t: float = 0.0, lag: float = 1.0) -> datetime:
    return T0 + timedelta(seconds=t + lag)


def anchor(n: int = 1, **kw):
    """An accepted anchor fix produced through the public API."""
    t = kw.pop("t", 0.0)
    result = gq.evaluate_fix(payload(n, t=t, **kw), received_at=received(t))
    assert result.disposition == D.ACCEPTED_SEGMENT_START, result
    return result.next_anchor


def codes(result):
    return [(i.field, i.code) for i in result.issues]


class ValidMeasurementTests(unittest.TestCase):
    def test_minimal_valid_fix_first_is_segment_start_with_zero_distance(self):
        r = gq.evaluate_fix(payload(), received_at=received())
        self.assertEqual(r.disposition, D.ACCEPTED_SEGMENT_START)
        self.assertTrue(r.valid_measurement)
        self.assertTrue(r.starts_new_segment)
        self.assertEqual(r.distance_contribution_m, 0.0)
        self.assertEqual(r.reasons, ("FIRST_FIX",))
        self.assertIs(r.next_anchor, r.fix)

    def test_optional_fields_absent_or_null_are_none(self):
        r = gq.evaluate_fix(
            payload(speed_mps=None, heading_deg=None, altitude_m=None),
            received_at=received(),
        )
        self.assertTrue(r.valid_measurement)
        f = r.fix
        self.assertIsNone(f.speed_mps)
        self.assertIsNone(f.heading_deg)
        self.assertIsNone(f.altitude_m)
        self.assertIsNone(f.altitude_accuracy_m)
        self.assertFalse(f.new_segment)

    def test_all_optional_fields_kept_in_canonical_units(self):
        r = gq.evaluate_fix(
            payload(
                speed_mps=12.5,
                heading_deg=359.999,
                altitude_m=-12.25,
                altitude_accuracy_m=3.5,
                schema="DriverLocationFixV1",
            ),
            received_at=received(),
        )
        self.assertTrue(r.valid_measurement, r.issues)
        d = r.fix.to_dict()
        self.assertEqual(d["speed_mps"], 12.5)
        self.assertEqual(d["heading_deg"], 359.999)
        self.assertEqual(d["altitude_m"], -12.25)
        self.assertEqual(d["altitude_accuracy_m"], 3.5)
        self.assertEqual(d["schema"], "DriverLocationFixV1")

    def test_integer_json_numbers_accepted(self):
        r = gq.evaluate_fix(payload(lat=0, lng=1, accuracy_m=5), received_at=received())
        self.assertTrue(r.valid_measurement)
        self.assertIsInstance(r.fix.lat, float)

    def test_no_silent_rounding_of_coordinates(self):
        lat, lng = 0.123456789012345, -0.987654321098765
        r = gq.evaluate_fix(payload(lat=lat, lng=lng), received_at=received())
        self.assertEqual(r.fix.lat, lat)
        self.assertEqual(r.fix.lng, lng)
        self.assertEqual(r.fix.to_dict()["lat"], lat)

    def test_coordinate_range_boundaries_inclusive(self):
        for lat, lng in [(90.0, 180.0), (-90.0, -180.0), (90, -180), (-90, 180)]:
            with self.subTest(lat=lat, lng=lng):
                r = gq.evaluate_fix(payload(lat=lat, lng=lng), received_at=received())
                self.assertTrue(r.valid_measurement, r.issues)

    def test_timestamps_normalized_to_utc(self):
        local = "2030-01-01T15:00:00.123456+03:00"  # = 12:00:00.123456Z
        r = gq.evaluate_fix(payload(captured_at=local), received_at=received())
        self.assertTrue(r.valid_measurement, r.issues)
        self.assertEqual(r.fix.captured_at.utcoffset(), timedelta(0))
        self.assertEqual(r.fix.to_dict()["captured_at"], "2030-01-01T12:00:00.123456Z")

    def test_received_at_is_from_caller_not_payload(self):
        r = gq.evaluate_fix(payload(), received_at="2030-01-01T12:00:02Z")
        self.assertEqual(r.fix.received_at, T0 + timedelta(seconds=2))

    def test_canonical_dict_has_exact_v1_keys_and_no_constellation(self):
        d = gq.evaluate_fix(payload(), received_at=received()).fix.to_dict()
        self.assertEqual(
            list(d),
            [
                "schema",
                "point_id",
                "lat",
                "lng",
                "captured_at",
                "received_at",
                "source",
                "accuracy_m",
                "speed_mps",
                "heading_deg",
                "altitude_m",
                "altitude_accuracy_m",
                "new_segment",
            ],
        )


class RejectionTests(unittest.TestCase):
    def assertRejected(self, p, field, code):
        r = gq.evaluate_fix(p, received_at=received())
        self.assertEqual(r.disposition, D.REJECTED, r)
        self.assertFalse(r.valid_measurement)
        self.assertEqual(r.distance_contribution_m, 0.0)
        self.assertIsNone(r.fix)
        self.assertIn((field, code), codes(r))
        return r

    def test_payload_not_object(self):
        for p in ([], 1, None, True, ["lat", 0]):
            with self.subTest(p=p):
                r = gq.evaluate_fix(p, received_at=received())
                self.assertEqual(codes(r), [("$", "PAYLOAD_NOT_OBJECT")])

    def test_missing_required_fields(self):
        for name in ("point_id", "lat", "lng", "captured_at", "source"):
            with self.subTest(name=name):
                p = payload()
                del p[name]
                self.assertRejected(p, name, "MISSING")
                self.assertRejected(payload(**{name: None}), name, "MISSING")

    def test_bool_is_not_a_number(self):
        for name in ("lat", "lng", "accuracy_m", "speed_mps", "heading_deg", "altitude_m"):
            for value in (True, False):
                with self.subTest(name=name, value=value):
                    self.assertRejected(payload(**{name: value}), name, "INVALID_TYPE")

    def test_numeric_strings_rejected(self):
        # The current /api/track accepts numeric strings such as "1.5" via float(); v1 does not.
        for name in ("lat", "lng", "accuracy_m"):
            with self.subTest(name=name):
                self.assertRejected(payload(**{name: "1.5"}), name, "INVALID_TYPE")

    def test_nan_and_infinity_rejected(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            for name in ("lat", "lng", "accuracy_m", "speed_mps", "heading_deg"):
                with self.subTest(name=name, value=value):
                    self.assertRejected(payload(**{name: value}), name, "NOT_FINITE")

    def test_huge_integer_rejected_without_overflow(self):
        self.assertRejected(payload(lat=10**400), "lat", "OUT_OF_RANGE")

    def test_out_of_range_coordinates(self):
        for lat in (90.0000001, -90.0000001, 180.0):
            self.assertRejected(payload(lat=lat), "lat", "OUT_OF_RANGE")
        for lng in (180.0000001, -180.0000001, 360.0):
            self.assertRejected(payload(lng=lng), "lng", "OUT_OF_RANGE")

    def test_out_of_range_accuracy_speed_heading_altitude(self):
        cases = [
            ("accuracy_m", 0.0),
            ("accuracy_m", -1.0),
            ("accuracy_m", 100_000.0001),
            ("speed_mps", -0.1),
            ("speed_mps", 120.0001),
            ("heading_deg", -0.0001),
            ("heading_deg", 360.0),
            ("altitude_m", -1000.1),
            ("altitude_m", 10000.1),
            ("altitude_accuracy_m", 0.0),
        ]
        for name, value in cases:
            with self.subTest(name=name, value=value):
                self.assertRejected(payload(**{name: value}), name, "OUT_OF_RANGE")

    def test_malformed_accuracy(self):
        for value in ("10", [10], {"m": 10}, True):
            with self.subTest(value=value):
                self.assertRejected(payload(accuracy_m=value), "accuracy_m", "INVALID_TYPE")

    def test_timezone_naive_timestamp(self):
        self.assertRejected(
            payload(captured_at="2030-01-01T12:00:00"), "captured_at", "TIMEZONE_NAIVE"
        )
        self.assertRejected(
            payload(captured_at="2030-01-01T12:00:00.5"), "captured_at", "TIMEZONE_NAIVE"
        )

    def test_invalid_timestamps(self):
        for value, code in [
            ("2030-01-01 12:00:00Z", "INVALID_FORMAT"),
            ("2030-13-01T12:00:00Z", "INVALID_VALUE"),
            ("2030-01-01T24:00:00Z", "INVALID_VALUE"),
            ("2030-01-01T23:59:60Z", "INVALID_VALUE"),
            ("1893456000", "INVALID_FORMAT"),
            ("", "INVALID_FORMAT"),
            (1893456000, "INVALID_TYPE"),
            ("2030-01-01T12:00:00.1234567Z", "PRECISION_UNSUPPORTED"),
        ]:
            with self.subTest(value=value):
                self.assertRejected(payload(captured_at=value), "captured_at", code)

    def test_point_id_bounds(self):
        ok = "a" * gq.MAX_POINT_ID_LENGTH
        self.assertTrue(gq.evaluate_fix(payload(point_id=ok), received_at=received()).valid_measurement)
        for value in ("a" * 65, "", " x", "x y", "-lead", "ид", "a/b"):
            with self.subTest(value=value):
                self.assertRejected(payload(point_id=value), "point_id", "INVALID_FORMAT")
        self.assertRejected(payload(point_id=42), "point_id", "INVALID_TYPE")

    def test_unknown_fields_rejected(self):
        self.assertRejected(payload(device_id="x"), "device_id", "UNKNOWN_FIELD")
        # received_at is a server value; a client cannot supply it.
        self.assertRejected(payload(received_at=iso(T0)), "received_at", "UNKNOWN_FIELD")

    def test_wrong_schema_rejected(self):
        self.assertRejected(payload(schema="DriverLocationFixV2"), "schema", "UNSUPPORTED_SCHEMA")

    def test_new_segment_must_be_strict_bool(self):
        for value in (1, "true", 0):
            with self.subTest(value=value):
                self.assertRejected(payload(new_segment=value), "new_segment", "INVALID_TYPE")

    def test_all_issues_reported_in_deterministic_order(self):
        p = payload(lat=True, lng=999, accuracy_m=float("nan"), source="gps")
        a = gq.evaluate_fix(p, received_at=received())
        b = gq.evaluate_fix(dict(reversed(list(p.items()))), received_at=received())
        self.assertEqual(codes(a), codes(b))
        self.assertEqual(
            codes(a),
            [
                ("lat", "INVALID_TYPE"),
                ("lng", "OUT_OF_RANGE"),
                ("accuracy_m", "NOT_FINITE"),
                ("source", "INVALID_SOURCE"),
            ],
        )


class SourceProvenanceTests(unittest.TestCase):
    def test_all_four_enum_sources_accepted_verbatim(self):
        for source in ("browser_geolocation", "android_location", "external_gnss", "unknown"):
            with self.subTest(source=source):
                r = gq.evaluate_fix(payload(source=source), received_at=received())
                self.assertEqual(r.fix.source, source)

    def test_misattributed_sources_rejected(self):
        for source in ("gps", "GPS", "glonass", "galileo", "beidou", "gnss",
                       "GPS+GLONASS", "Browser_Geolocation", "browser", "", 1, True):
            with self.subTest(source=source):
                r = gq.evaluate_fix(payload(source=source), received_at=received())
                self.assertEqual(r.disposition, D.REJECTED)
                self.assertIn(("source", "INVALID_SOURCE"), codes(r))

    def test_constellation_claims_rejected_even_for_native_sources(self):
        for source in ("browser_geolocation", "android_location", "external_gnss"):
            for key in ("constellations", "constellation", "satellites_used", "gnss_system"):
                with self.subTest(source=source, key=key):
                    r = gq.evaluate_fix(
                        payload(source=source, **{key: ["GPS", "GLONASS"]}),
                        received_at=received(),
                    )
                    self.assertEqual(r.disposition, D.REJECTED)
                    self.assertIn((key, "CONSTELLATION_NOT_SUPPORTED_V1"), codes(r))

    def test_source_is_never_inferred(self):
        # High accuracy and speed do not upgrade a browser fix to "GNSS".
        r = gq.evaluate_fix(payload(accuracy_m=1.0, speed_mps=10.0), received_at=received())
        self.assertEqual(r.fix.source, "browser_geolocation")
        r = gq.evaluate_fix(payload(source="unknown"), received_at=received())
        self.assertEqual(r.fix.source, "unknown")
        self.assertFalse(any("constell" in k or "satell" in k for k in r.fix.to_dict()))


class TimingTests(unittest.TestCase):
    def test_stale_boundary(self):
        limit = gq.DEFAULT_CONFIG.max_age_s
        ok = gq.evaluate_fix(payload(), received_at=T0 + timedelta(seconds=limit))
        self.assertTrue(ok.valid_measurement)
        stale = gq.evaluate_fix(payload(), received_at=T0 + timedelta(seconds=limit, microseconds=1))
        self.assertEqual(stale.disposition, D.REJECTED)
        self.assertEqual(stale.reasons, ("FIX_STALE",))

    def test_future_boundary(self):
        skew = gq.DEFAULT_CONFIG.max_future_skew_s
        ok = gq.evaluate_fix(payload(), received_at=T0 - timedelta(seconds=skew))
        self.assertTrue(ok.valid_measurement)
        future = gq.evaluate_fix(payload(), received_at=T0 - timedelta(seconds=skew, microseconds=1))
        self.assertEqual(future.reasons, ("FIX_IN_FUTURE",))
        self.assertFalse(future.valid_measurement)

    def test_limits_are_configurable(self):
        cfg = gq.QualityConfig(max_age_s=3600.0, max_future_skew_s=0.0)
        r = gq.evaluate_fix(payload(), received_at=T0 + timedelta(minutes=30), config=cfg)
        self.assertTrue(r.valid_measurement)
        r = gq.evaluate_fix(payload(), received_at=T0 - timedelta(microseconds=1), config=cfg)
        self.assertEqual(r.reasons, ("FIX_IN_FUTURE",))

    def test_out_of_order_discarded_anchor_kept(self):
        prev = anchor(1, t=10.0)
        r = gq.evaluate_fix(payload(2, lat=north(50), t=5.0), received_at=received(10.0), previous=prev)
        self.assertEqual(r.disposition, D.DISCARDED)
        self.assertEqual(r.reasons, ("OUT_OF_ORDER",))
        self.assertTrue(r.valid_measurement)
        self.assertEqual(r.distance_contribution_m, 0.0)
        self.assertIs(r.next_anchor, prev)

    def test_equal_timestamp_discarded(self):
        prev = anchor(1, t=10.0)
        r = gq.evaluate_fix(payload(2, lat=north(50), t=10.0), received_at=received(10.0), previous=prev)
        self.assertEqual(r.reasons, ("NON_INCREASING_TIMESTAMP",))
        self.assertIs(r.next_anchor, prev)

    def test_naive_received_at_is_a_programming_error(self):
        with self.assertRaises(ValueError):
            gq.evaluate_fix(payload(), received_at=datetime(2030, 1, 1, 12, 0, 1))
        with self.assertRaises(ValueError):
            gq.evaluate_fix(payload(), received_at="2030-01-01T12:00:01")


class DuplicateTests(unittest.TestCase):
    def test_exact_duplicate_point_id_is_idempotent(self):
        prev = anchor(1)
        # A retry of the same point arrives later; only received_at differs.
        r = gq.evaluate_fix(payload(1), received_at=received(lag=30.0), previous=prev)
        self.assertEqual(r.disposition, D.DISCARDED)
        self.assertEqual(r.reasons, ("DUPLICATE_POINT_ID",))
        self.assertEqual(r.distance_contribution_m, 0.0)
        self.assertIs(r.next_anchor, prev)

    def test_same_point_id_different_content_is_conflict(self):
        prev = anchor(1)
        r = gq.evaluate_fix(payload(1, lat=north(500), t=10.0), received_at=received(10.0), previous=prev)
        self.assertEqual(r.reasons, ("POINT_ID_CONFLICT",))
        self.assertEqual(r.distance_contribution_m, 0.0)

    def test_replayed_sequence_adds_no_distance(self):
        items = [(payload(i, lat=north(100 * i), t=10.0 * i), received(10.0 * i)) for i in range(1, 6)]
        once = gq.evaluate_sequence(items)
        twice = gq.evaluate_sequence(items + items[-1:] * 3)
        self.assertAlmostEqual(once.total_distance_m, 400.0, places=6)
        self.assertEqual(once.total_distance_m, twice.total_distance_m)


class AccuracyTests(unittest.TestCase):
    def test_accuracy_missing_is_valid_but_contributes_nothing(self):
        # Contrast: static/script.js turns a missing accuracy into 0 m ("perfect").
        absent = payload()
        del absent["accuracy_m"]
        for p in (absent, payload(accuracy_m=None)):
            with self.subTest(p=sorted(p)):
                r = gq.evaluate_fix(p, received_at=received())
                self.assertTrue(r.valid_measurement)
                self.assertEqual(r.disposition, D.DISCARDED)
                self.assertEqual(r.reasons, ("ACCURACY_MISSING",))
                self.assertIsNone(r.next_anchor)

    def test_accuracy_threshold_boundary(self):
        limit = gq.DEFAULT_CONFIG.max_accuracy_m
        ok = gq.evaluate_fix(payload(accuracy_m=limit), received_at=received())
        self.assertEqual(ok.disposition, D.ACCEPTED_SEGMENT_START)
        bad = gq.evaluate_fix(payload(accuracy_m=limit + 1e-9), received_at=received())
        self.assertEqual(bad.disposition, D.DISCARDED)
        self.assertEqual(bad.reasons, ("ACCURACY_INSUFFICIENT",))
        self.assertTrue(bad.valid_measurement)

    def test_insufficient_accuracy_does_not_move_anchor(self):
        prev = anchor(1)
        r = gq.evaluate_fix(
            payload(2, lat=north(300), t=10.0, accuracy_m=500.0),
            received_at=received(10.0),
            previous=prev,
        )
        self.assertEqual(r.reasons, ("ACCURACY_INSUFFICIENT",))
        self.assertIs(r.next_anchor, prev)
        self.assertEqual(r.distance_contribution_m, 0.0)


class MotionTests(unittest.TestCase):
    def test_zero_motion(self):
        prev = anchor(1)
        r = gq.evaluate_fix(payload(2, t=10.0), received_at=received(10.0), previous=prev)
        self.assertEqual(r.disposition, D.ACCEPTED_STATIONARY)
        self.assertEqual(r.reasons, ("STATIONARY_JITTER",))
        self.assertEqual(r.raw_distance_m, 0.0)
        self.assertEqual(r.distance_contribution_m, 0.0)
        self.assertIs(r.next_anchor, prev)

    def test_same_point_jitter_adds_no_distance(self):
        # Parked car: 60 fixes scattered within +/-4 m per axis, accuracy 10 m each.
        offsets = [((i * 37) % 9 - 4, (i * 53) % 9 - 4) for i in range(60)]
        items = [
            (payload(i + 1, lat=north(dy), lng=north(dx), t=5.0 * i), received(5.0 * i))
            for i, (dx, dy) in enumerate(offsets)
        ]
        res = gq.evaluate_sequence(items)
        self.assertEqual(res.total_distance_m, 0.0)
        self.assertEqual(res.evaluations[0].disposition, D.ACCEPTED_SEGMENT_START)
        for e in res.evaluations[1:]:
            self.assertEqual(e.disposition, D.ACCEPTED_STATIONARY)
            self.assertFalse(e.starts_new_segment)
        # 300 s parked > max_gap_s: the anchor is refreshed in place, never a track break.
        reasons = {e.reasons[0] for e in res.evaluations[1:]}
        self.assertEqual(reasons, {"STATIONARY_JITTER", "STATIONARY_REANCHOR"})

    def test_long_stop_then_drive_away_counts_from_recent_anchor(self):
        items = [(payload(i + 1, t=10.0 * i), received(10.0 * i)) for i in range(31)]  # 300 s parked
        items.append((payload(99, lat=north(60.0), t=305.0), received(305.0)))
        res = gq.evaluate_sequence(items)
        last = res.evaluations[-1]
        self.assertEqual(last.disposition, D.ACCEPTED_MOVEMENT)
        self.assertAlmostEqual(res.total_distance_m, 60.0, places=6)

    def test_jitter_threshold_boundary(self):
        cfg = gq.QualityConfig(min_movement_m=20.0, jitter_accuracy_factor=0.0)
        prev = anchor(1, accuracy_m=5.0)
        inside = gq.classify_fix(
            gq.normalize_fix(payload(2, lat=north(19.999), t=10.0), received_at=received(10.0))[0],
            prev, cfg,
        )
        self.assertEqual(inside.disposition, D.ACCEPTED_STATIONARY)
        outside = gq.classify_fix(
            gq.normalize_fix(payload(2, lat=north(20.001), t=10.0), received_at=received(10.0))[0],
            prev, cfg,
        )
        self.assertEqual(outside.disposition, D.ACCEPTED_MOVEMENT)

    def test_slow_movement_is_not_lost_while_anchor_waits(self):
        # 2 m per step with 10 m accuracy: individually jitter, cumulatively real.
        items = [(payload(i + 1, lat=north(2.0 * i), t=2.0 * i), received(2.0 * i)) for i in range(51)]
        res = gq.evaluate_sequence(items)
        moved = [e for e in res.evaluations if e.disposition == D.ACCEPTED_MOVEMENT]
        self.assertTrue(moved)
        last_anchor_m = res.final_anchor.lat * M_PER_DEG
        self.assertAlmostEqual(res.total_distance_m, last_anchor_m, places=6)
        self.assertGreater(res.total_distance_m, 100.0 - 15.0)
        self.assertLessEqual(res.total_distance_m, 100.0 + 1e-6)

    def test_normal_movement_counts_exact_haversine(self):
        prev = anchor(1)
        r = gq.evaluate_fix(payload(2, lat=north(100.0), t=10.0), received_at=received(10.0), previous=prev)
        self.assertEqual(r.disposition, D.ACCEPTED_MOVEMENT)
        self.assertEqual(r.reasons, ("MOVEMENT",))
        self.assertAlmostEqual(r.distance_contribution_m, 100.0, places=6)
        self.assertEqual(r.distance_contribution_m, r.raw_distance_m)
        self.assertAlmostEqual(r.derived_speed_mps, 10.0, places=6)
        self.assertIs(r.next_anchor, r.fix)

    def test_impossible_jump_is_suspect(self):
        prev = anchor(1)
        r = gq.evaluate_fix(payload(2, lat=north(5000.0), t=10.0), received_at=received(10.0), previous=prev)
        self.assertEqual(r.disposition, D.SUSPECT)
        self.assertEqual(r.reasons, ("IMPLAUSIBLE_SPEED",))
        self.assertTrue(r.valid_measurement)
        self.assertEqual(r.distance_contribution_m, 0.0)
        self.assertIs(r.next_anchor, prev)
        self.assertGreater(r.derived_speed_mps, gq.DEFAULT_CONFIG.max_speed_mps)

    def test_speed_boundary_uses_accuracy_margin(self):
        cfg = gq.QualityConfig(max_speed_mps=50.0)
        prev = anchor(1, accuracy_m=3.0)
        margin = math.hypot(3.0, 4.0)  # 5 m
        at_limit = 50.0 * 10.0 + margin
        ok = gq.evaluate_fix(payload(2, lat=north(at_limit - 0.001), t=10.0, accuracy_m=4.0),
                             received_at=received(10.0), previous=prev, config=cfg)
        self.assertEqual(ok.disposition, D.ACCEPTED_MOVEMENT)
        bad = gq.evaluate_fix(payload(2, lat=north(at_limit + 0.01), t=10.0, accuracy_m=4.0),
                              received_at=received(10.0), previous=prev, config=cfg)
        self.assertEqual(bad.disposition, D.SUSPECT)

    def test_single_outlier_spike_is_ignored_and_track_continues(self):
        items = [
            (payload(1, lat=north(0), t=0), received(0)),
            (payload(2, lat=north(100), t=10), received(10)),
            (payload(3, lat=north(9000), t=20), received(20)),  # spike
            (payload(4, lat=north(300), t=30), received(30)),
        ]
        res = gq.evaluate_sequence(items)
        self.assertEqual([e.disposition for e in res.evaluations],
                         [D.ACCEPTED_SEGMENT_START, D.ACCEPTED_MOVEMENT, D.SUSPECT, D.ACCEPTED_MOVEMENT])
        self.assertAlmostEqual(res.total_distance_m, 300.0, places=6)

    def test_antimeridian_crossing_is_short(self):
        prev = anchor(1, lng=179.9995)
        r = gq.evaluate_fix(payload(2, lng=-179.9995, t=10.0), received_at=received(10.0), previous=prev)
        self.assertEqual(r.disposition, D.ACCEPTED_MOVEMENT)
        self.assertAlmostEqual(r.distance_contribution_m, 0.001 * M_PER_DEG, places=3)


class SegmentTests(unittest.TestCase):
    def test_gap_starts_new_segment_without_distance(self):
        prev = anchor(1)
        gap = gq.DEFAULT_CONFIG.max_gap_s
        r = gq.evaluate_fix(payload(2, lat=north(2000.0), t=gap + 1), received_at=received(gap + 1), previous=prev)
        self.assertEqual(r.disposition, D.ACCEPTED_SEGMENT_START)
        self.assertEqual(r.reasons, ("GAP_NEW_SEGMENT",))
        self.assertTrue(r.starts_new_segment)
        self.assertEqual(r.distance_contribution_m, 0.0)
        self.assertAlmostEqual(r.raw_distance_m, 2000.0, places=6)
        self.assertIs(r.next_anchor, r.fix)

    def test_gap_without_movement_reanchors_without_break(self):
        prev = anchor(1)
        gap = gq.DEFAULT_CONFIG.max_gap_s
        r = gq.evaluate_fix(payload(2, lat=north(5.0), t=gap + 1), received_at=received(gap + 1), previous=prev)
        self.assertEqual(r.disposition, D.ACCEPTED_STATIONARY)
        self.assertEqual(r.reasons, ("STATIONARY_REANCHOR",))
        self.assertFalse(r.starts_new_segment)
        self.assertEqual(r.distance_contribution_m, 0.0)
        self.assertIs(r.next_anchor, r.fix)

    def test_gap_boundary_inclusive(self):
        prev = anchor(1)
        gap = gq.DEFAULT_CONFIG.max_gap_s
        r = gq.evaluate_fix(payload(2, lat=north(1000.0), t=gap), received_at=received(gap), previous=prev)
        self.assertEqual(r.disposition, D.ACCEPTED_MOVEMENT)

    def test_client_new_segment_flag(self):
        prev = anchor(1)
        r = gq.evaluate_fix(payload(2, lat=north(100.0), t=10.0, new_segment=True),
                            received_at=received(10.0), previous=prev)
        self.assertEqual(r.reasons, ("SEGMENT_REQUESTED",))
        self.assertEqual(r.distance_contribution_m, 0.0)
        self.assertTrue(r.fix.new_segment)

    def test_stuck_anchor_recovers_through_gap(self):
        # After a genuine relocation the first far fixes look implausible, but
        # once max_gap_s has passed since the anchor a new segment starts.
        items = [(payload(1, t=0), received(0))]
        items += [(payload(i, lat=north(50_000 + i), t=10.0 * i), received(10.0 * i)) for i in range(2, 15)]
        res = gq.evaluate_sequence(items)
        disp = [e.disposition for e in res.evaluations]
        self.assertIn(D.SUSPECT, disp)
        self.assertIn(D.ACCEPTED_SEGMENT_START, disp[1:])
        self.assertEqual(res.total_distance_m,
                         math.fsum(e.distance_contribution_m for e in res.evaluations))
        self.assertLess(res.total_distance_m, 200.0)  # never the 50 km jump


class SeparationAndPurityTests(unittest.TestCase):
    def test_three_outcomes_are_separate_fields(self):
        prev = anchor(1)
        samples = {
            "invalid": gq.evaluate_fix(payload(2, lat=91.0, t=10), received_at=received(10), previous=prev),
            "discarded": gq.evaluate_fix(payload(2, t=10, accuracy_m=200.0), received_at=received(10), previous=prev),
            "suspect": gq.evaluate_fix(payload(2, lat=north(9000), t=10), received_at=received(10), previous=prev),
            "moving": gq.evaluate_fix(payload(2, lat=north(100), t=10), received_at=received(10), previous=prev),
        }
        self.assertFalse(samples["invalid"].valid_measurement)
        for key in ("discarded", "suspect", "moving"):
            self.assertTrue(samples[key].valid_measurement, key)
        for key in ("invalid", "discarded", "suspect"):
            self.assertEqual(samples[key].distance_contribution_m, 0.0, key)
        self.assertGreater(samples["moving"].distance_contribution_m, 0.0)

    def test_deterministic(self):
        prev = anchor(1)
        a = gq.evaluate_fix(payload(2, lat=north(100), t=10), received_at=received(10), previous=prev)
        b = gq.evaluate_fix(payload(2, lat=north(100), t=10), received_at=received(10), previous=prev)
        self.assertEqual(a, b)

    def test_inputs_not_mutated_and_results_frozen(self):
        p = payload()
        before = dict(p)
        r = gq.evaluate_fix(p, received_at=received())
        self.assertEqual(p, before)
        with self.assertRaises(FrozenInstanceError):
            r.fix.lat = 1.0  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            r.distance_contribution_m = 5.0  # type: ignore[misc]

    def test_repr_hides_coordinates_and_point_id(self):
        r = gq.evaluate_fix(payload(lat=0.4321987, lng=0.8765123, altitude_m=123.456), received_at=received())
        text = repr(r)
        for hidden in ("0.4321987", "0.8765123", "123.456", "synthetic-0001"):
            self.assertNotIn(hidden, text)

    def test_previous_must_be_accepted_anchor(self):
        f = gq.normalize_fix(payload(accuracy_m=None), received_at=received())[0]
        with self.assertRaises(ValueError):
            gq.classify_fix(f, previous=f)
        with self.assertRaises(TypeError):
            gq.classify_fix(f, previous={"lat": 0})

    def test_config_validation(self):
        for bad in (dict(max_age_s=float("nan")), dict(max_speed_mps=-1.0),
                    dict(max_gap_s=0.0), dict(max_accuracy_m=True)):
            with self.subTest(bad=bad):
                with self.assertRaises((TypeError, ValueError)):
                    gq.QualityConfig(**bad)

    def test_config_is_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            gq.DEFAULT_CONFIG.max_speed_mps = 1.0  # type: ignore[misc]
        self.assertEqual(replace(gq.DEFAULT_CONFIG, max_gap_s=60.0).max_gap_s, 60.0)
        self.assertEqual(gq.DEFAULT_CONFIG.max_gap_s, 120.0)

    def test_module_imports_only_stdlib_and_has_no_io(self):
        path = os.path.join(REPO_ROOT, "gnss_quality.py")
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        self.assertLessEqual(imported, {"__future__", "json", "math", "re", "dataclasses", "datetime", "typing"})
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        for forbidden in ("open", "print", "input", "exec", "eval", "__import__"):
            self.assertNotIn(forbidden, names)
        for forbidden in ("now", "utcnow", "today", "time", "getLogger", "system"):
            self.assertNotIn(forbidden, attrs)

    def test_import_has_no_side_effects_on_app_runtime(self):
        # Fresh isolated interpreter (-I: no PYTHONPATH, no user site, no cwd on sys.path).
        code = (
            "import sys; sys.path.insert(0, sys.argv[1]); import gnss_quality;"
            "print(sorted(m for m in ('app', 'flask', 'storage', 'logging', 'socket') if m in sys.modules))"
        )
        out = subprocess.run(
            [sys.executable, "-I", "-c", code, REPO_ROOT],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), "[]")


class JsonDecodingTests(unittest.TestCase):
    def test_valid_json_document(self):
        raw = (
            '{"point_id":"synthetic-0001","lat":0.0,"lng":0.0,'
            '"captured_at":"2030-01-01T12:00:00Z","source":"unknown","accuracy_m":12.5}'
        )
        r = gq.evaluate_fix(raw, received_at=received())
        self.assertEqual(r.disposition, D.ACCEPTED_SEGMENT_START)
        r = gq.evaluate_fix(raw.encode("utf-8"), received_at=received())
        self.assertEqual(r.disposition, D.ACCEPTED_SEGMENT_START)

    def test_nan_infinity_tokens_rejected(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token):
                value, issues = gq.decode_fix_json('{"lat": %s}' % token)
                self.assertIsNone(value)
                self.assertEqual(issues, (gq.Issue("$", "NOT_FINITE"),))

    def test_overflowing_literal_rejected_as_not_finite(self):
        r = gq.evaluate_fix(
            '{"point_id":"p1","lat":1e400,"lng":0,"captured_at":"2030-01-01T12:00:00Z","source":"unknown"}',
            received_at=received(),
        )
        self.assertIn(("lat", "NOT_FINITE"), codes(r))

    def test_duplicate_keys_rejected(self):
        _, issues = gq.decode_fix_json('{"lat": 0, "lat": 1}')
        self.assertEqual(issues, (gq.Issue("$", "DUPLICATE_KEY"),))

    def test_malformed_and_oversized(self):
        for raw, code in [
            ("{", "MALFORMED_JSON"),
            ("", "MALFORMED_JSON"),
            ("{'lat': 0}", "MALFORMED_JSON"),
            (b"\xff\xfe", "INVALID_UTF8"),
            ("x" * (gq.MAX_JSON_BYTES + 1), "PAYLOAD_TOO_LARGE"),
            (b"x" * (gq.MAX_JSON_BYTES + 1), "PAYLOAD_TOO_LARGE"),
        ]:
            with self.subTest(code=code):
                r = gq.evaluate_fix(raw, received_at=received())
                self.assertEqual(r.disposition, D.REJECTED)
                self.assertEqual(codes(r), [("$", code)])

    def test_json_array_is_not_an_object(self):
        r = gq.evaluate_fix("[0, 0]", received_at=received())
        self.assertEqual(codes(r), [("$", "PAYLOAD_NOT_OBJECT")])


class RepositoryIsolationTests(unittest.TestCase):
    def test_production_state_files_not_created(self):
        # The module never writes; these runtime files must not appear because of tests.
        for name in ("driver_state.json", "shift_history.json"):
            path = os.path.join(REPO_ROOT, name)
            existed_before = _EXISTED_AT_IMPORT[name]
            self.assertEqual(os.path.exists(path), existed_before, name)


_EXISTED_AT_IMPORT = {
    name: os.path.exists(os.path.join(REPO_ROOT, name))
    for name in ("driver_state.json", "shift_history.json")
}


if __name__ == "__main__":
    unittest.main()
