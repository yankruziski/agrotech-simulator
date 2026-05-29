"""Unit tests for engine/narrative.py — template-based text generation."""

import pytest
from engine.narrative import generate


DEFAULTS = dict(d1="Normal", c1=None, d2=None, c2=None,
                state="MG", pessimistic=50.0, most_likely=60.0, optimistic=70.0, n_comparable=0)


def make(**overrides):
    return generate(**{**DEFAULTS, **overrides})


class TestGenerateBasics:
    def test_returns_non_empty_string(self):
        result = make()
        assert isinstance(result, str)
        assert len(result) > 20

    def test_always_includes_most_likely_value(self):
        result = make(most_likely=62.5)
        assert "62.5" in result

    def test_always_includes_pessimistic_value(self):
        result = make(pessimistic=48.0)
        assert "48.0" in result

    def test_always_includes_optimistic_value(self):
        result = make(optimistic=79.3)
        assert "79.3" in result

    def test_always_includes_state(self):
        for state in ["MG", "PR", "MS", "GO"]:
            assert state in make(state=state)


class TestD1Windows:
    def test_early_window_mentioned(self):
        result = make(d1="Early")
        assert "early" in result.lower() or "september" in result.lower()

    def test_normal_window_mentioned(self):
        result = make(d1="Normal")
        assert "normal" in result.lower() or "november" in result.lower()

    def test_late_window_mentioned(self):
        result = make(d1="Late")
        assert "late" in result.lower() or "december" in result.lower()


class TestSoilTexture:
    def test_favorable_soil_mentioned(self):
        result = make(c1="Favorable")
        assert "clay" in result.lower()

    def test_challenging_soil_mentioned(self):
        result = make(c1="Challenging")
        assert "sandy" in result.lower()

    def test_intermediary_soil_mentioned(self):
        result = make(c1="Intermediary")
        assert "loam" in result.lower()

    def test_no_soil_texture_omitted(self):
        with_texture    = make(c1="Favorable")
        without_texture = make(c1=None)
        assert len(without_texture) < len(with_texture)


class TestSeedDensityRecommendations:
    def test_low_density_triggers_recommendation(self):
        result = make(d2="Low")
        assert "280,000" in result

    def test_ideal_density_no_correction_recommendation(self):
        result = make(d2="Ideal")
        assert "adjust" not in result.lower()

    def test_high_density_mentioned(self):
        result = make(d2="High")
        assert "320,000" in result.lower() or "high" in result.lower()


class TestSoilPHRecommendations:
    def test_borderline_ph_triggers_liming(self):
        result = make(c2="Intermediary")
        assert "liming" in result.lower() or "ph" in result.lower()

    def test_critical_ph_triggers_strong_warning(self):
        result = make(c2="Challenging")
        assert "correction" in result.lower() or "strongly" in result.lower()

    def test_adequate_ph_no_correction_recommendation(self):
        result = make(c2="Favorable")
        assert "correction" not in result.lower()
        assert "liming" not in result.lower()


class TestComparableCases:
    def test_singular_case_text(self):
        result = make(n_comparable=1)
        assert "1 comparable" in result
        assert "confirms" in result

    def test_plural_cases_text(self):
        result = make(n_comparable=5)
        assert "5 comparable" in result
        assert "confirm" in result

    def test_zero_cases_no_comparable_mention(self):
        result = make(n_comparable=0)
        assert "comparable" not in result

    def test_comparable_includes_state(self):
        result = make(n_comparable=3, state="PR")
        assert "PR" in result


class TestFullCombinations:
    def test_all_optional_provided(self):
        result = generate("Early", "Favorable", "Ideal", "Favorable",
                          "MG", 60.0, 74.0, 85.0, 5)
        assert "74.0" in result
        assert "MG" in result
        assert "5 comparable" in result

    def test_minimal_required_only(self):
        result = generate("Late", None, None, None,
                          "GO", 40.0, 52.0, 60.0, 0)
        assert "52.0" in result
        assert "GO" in result

    def test_worst_case_combo(self):
        result = generate("Late", "Challenging", "Low", "Challenging",
                          "MS", 30.0, 37.0, 44.0, 2)
        assert "37.0" in result
        assert "MS" in result
        # d2="Low" matches the if-branch first; seed density recommendation appears.
        # The elif c2="Challenging" branch is skipped because d2=="Low" already matched.
        assert "280,000" in result
