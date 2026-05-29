"""Unit tests for engine/classifier.py — pure functions, no I/O."""

import pytest
from engine.classifier import classify_all, classify_c1, classify_c2, classify_d1, classify_d2


# ── D1: Planting Date ──────────────────────────────────────────────────────────

class TestClassifyD1:
    @pytest.mark.parametrize("date_str,expected_class,expected_month", [
        ("2024-09-01", "Early",  9),
        ("2024-10-15", "Early",  10),
        ("2024-11-01", "Normal", 11),
        ("2024-11-30", "Normal", 11),
        ("2024-12-01", "Late",   12),
        ("2025-01-15", "Late",   1),
        ("2025-02-10", "Late",   2),
        ("2025-03-31", "Late",   3),
    ])
    def test_classification_by_month(self, date_str, expected_class, expected_month):
        cls, month = classify_d1(date_str)
        assert cls == expected_class
        assert month == expected_month

    def test_returns_tuple(self):
        result = classify_d1("2024-10-15")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_early_boundary_september(self):
        cls, _ = classify_d1("2024-09-30")
        assert cls == "Early"

    def test_early_boundary_october(self):
        cls, _ = classify_d1("2024-10-31")
        assert cls == "Early"

    def test_different_date_formats_same_result(self):
        cls_iso,  _ = classify_d1("2024-10-15")
        cls_br,   _ = classify_d1("15/10/2024")
        cls_us,   _ = classify_d1("10/15/2024")
        assert cls_iso == cls_br == cls_us == "Early"


# ── C1: Soil Texture ───────────────────────────────────────────────────────────

class TestClassifyC1:
    @pytest.mark.parametrize("texture,expected", [
        ("clay",            "Favorable"),
        ("very clay",       "Favorable"),
        ("argilosa",        "Favorable"),
        ("muito argilosa",  "Favorable"),
        ("loam",            "Intermediary"),
        ("medium",          "Intermediary"),
        ("clay-loam",       "Intermediary"),
        ("franca",          "Intermediary"),
        ("sandy",           "Challenging"),
        ("arenosa",         "Challenging"),
        ("areia",           "Challenging"),
    ])
    def test_known_textures(self, texture, expected):
        assert classify_c1(texture) == expected

    def test_case_insensitive(self):
        assert classify_c1("CLAY") == "Favorable"
        assert classify_c1("Sandy") == "Challenging"
        assert classify_c1("LOAM") == "Intermediary"

    def test_none_input_returns_none(self):
        assert classify_c1(None) is None

    def test_empty_string_returns_none(self):
        assert classify_c1("") is None

    def test_unknown_texture_returns_none(self):
        assert classify_c1("unknown_texture_xyz_abc") is None

    def test_whitespace_stripped(self):
        assert classify_c1("  clay  ") == "Favorable"

    def test_partial_match_clay_in_phrase(self):
        result = classify_c1("medium-to-clay")
        assert result == "Favorable"


# ── D2: Seed Population ────────────────────────────────────────────────────────

class TestClassifyD2:
    def test_none_returns_none(self):
        assert classify_d2(None) is None

    @pytest.mark.parametrize("pop,expected", [
        (100_000,  "Low"),
        (280_000,  "Low"),    # exactly at low_max boundary → Low
        (280_001,  "Ideal"),  # one above → Ideal
        (300_000,  "Ideal"),
        (320_000,  "Ideal"),  # exactly at ideal_max boundary → Ideal
        (320_001,  "High"),   # one above → High
        (400_000,  "High"),
    ])
    def test_boundary_and_typical(self, pop, expected):
        assert classify_d2(pop) == expected

    def test_very_low_population(self):
        assert classify_d2(1) == "Low"

    def test_very_high_population(self):
        assert classify_d2(2_000_000) == "High"


# ── C2: Soil pH ────────────────────────────────────────────────────────────────

class TestClassifyC2:
    def test_both_none_returns_none(self):
        assert classify_c2(None, None) is None

    def test_only_min_returns_none(self):
        assert classify_c2(5.8, None) is None

    def test_only_max_returns_none(self):
        assert classify_c2(None, 6.2) is None

    @pytest.mark.parametrize("ph_min,ph_max,expected", [
        (5.5,  5.5,  "Favorable"),    # lower boundary of Favorable
        (5.8,  6.2,  "Favorable"),    # typical good pH
        (6.0,  6.0,  "Favorable"),
        (6.5,  6.5,  "Favorable"),    # upper boundary of Favorable
        (5.0,  5.0,  "Intermediary"), # avg = 5.0 — lower boundary of Intermediary
        (5.2,  5.4,  "Intermediary"), # avg = 5.3
        (6.6,  6.8,  "Challenging"),  # avg = 6.7 — above 6.5 → Challenging
        (4.0,  4.5,  "Challenging"),  # avg = 4.25 — too acidic
        (7.0,  7.5,  "Challenging"),  # avg = 7.25 — too alkaline
        (4.9,  4.9,  "Challenging"),  # avg = 4.9 — below 5.0
        (6.9,  6.9,  "Challenging"),  # avg = 6.9 — above 6.5
    ])
    def test_ph_classification(self, ph_min, ph_max, expected):
        assert classify_c2(ph_min, ph_max) == expected

    def test_average_is_midpoint(self):
        # avg of 5.0 and 6.5 = 5.75 → Favorable
        assert classify_c2(5.0, 6.5) == "Favorable"


# ── classify_all: full integration ────────────────────────────────────────────

class TestClassifyAll:
    def test_full_payload(self):
        result = classify_all(
            planting_date="2024-10-15",
            soil_texture="clay",
            seed_population=300_000,
            soil_ph_min=5.8,
            soil_ph_max=6.2,
        )
        assert result["D1"] == "Early"
        assert result["C1"] == "Favorable"
        assert result["D2"] == "Ideal"
        assert result["C2"] == "Favorable"
        assert result["planting_month"] == 10
        assert result["soil_ph_avg"] == pytest.approx(6.0)

    def test_minimal_required_only(self):
        result = classify_all(
            planting_date="2024-11-01",
            soil_texture=None,
            seed_population=None,
            soil_ph_min=None,
            soil_ph_max=None,
        )
        assert result["D1"] == "Normal"
        assert result["C1"] is None
        assert result["D2"] is None
        assert result["C2"] is None
        assert result["soil_ph_avg"] is None

    def test_worst_case_combination(self):
        result = classify_all(
            planting_date="2025-01-15",
            soil_texture="sandy",
            seed_population=200_000,
            soil_ph_min=4.0,
            soil_ph_max=4.5,
        )
        assert result["D1"] == "Late"
        assert result["C1"] == "Challenging"
        assert result["D2"] == "Low"
        assert result["C2"] == "Challenging"

    def test_keys_present(self):
        result = classify_all("2024-10-01", None, None, None, None)
        assert set(result.keys()) == {"D1", "C1", "D2", "C2", "planting_month", "soil_ph_avg"}
