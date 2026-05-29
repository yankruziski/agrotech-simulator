"""Unit tests for engine/decision_tree.py — additive payoff formula."""

import pytest
from engine.decision_tree import compute_payoff


class TestComputePayoff:

    # ── Absolute payoff values ────────────────────────────────────────────────

    @pytest.mark.parametrize("d1,c1,d2,c2,expected", [
        # Best case: Early + Favorable + Ideal + Favorable = 64+4+2+4 = 74
        ("Early",  "Favorable",    "Ideal", "Favorable",    74.0),
        # Worst case: Late + Challenging + Low + Challenging = 52-6-3-6 = 37
        ("Late",   "Challenging",  "Low",   "Challenging",  37.0),
        # Normal with all neutral/slightly negative: 60+0-1+0 = 59
        ("Normal", "Intermediary", "High",  "Intermediary", 59.0),
        # Early with no optional adjustments: 64
        ("Early",  None,           None,    None,           64.0),
        # Normal base only: 60
        ("Normal", None,           None,    None,           60.0),
        # Late base only: 52
        ("Late",   None,           None,    None,           52.0),
        # Early + Challenging: 64-6 = 58
        ("Early",  "Challenging",  None,    None,           58.0),
        # Normal + Favorable pH: 60+4 = 64
        ("Normal", None,           None,    "Favorable",    64.0),
        # Late + Low + Challenging: 52-3-6 = 43
        ("Late",   None,           "Low",   "Challenging",  43.0),
    ])
    def test_payoff_values(self, d1, c1, d2, c2, expected):
        result = compute_payoff(d1, c1, d2, c2)
        assert result["payoff_sc_ha"] == expected

    # ── Component structure ───────────────────────────────────────────────────

    def test_components_keys(self):
        result = compute_payoff("Early", "Favorable", "Ideal", "Favorable")
        assert set(result["components"].keys()) == {"D1_base", "C1_adj", "D2_adj", "C2_adj"}

    def test_d1_base_values(self):
        assert compute_payoff("Early",  None, None, None)["components"]["D1_base"] == 64
        assert compute_payoff("Normal", None, None, None)["components"]["D1_base"] == 60
        assert compute_payoff("Late",   None, None, None)["components"]["D1_base"] == 52

    def test_c1_adj_values(self):
        assert compute_payoff("Normal", "Favorable",    None, None)["components"]["C1_adj"] ==  4
        assert compute_payoff("Normal", "Intermediary", None, None)["components"]["C1_adj"] ==  0
        assert compute_payoff("Normal", "Challenging",  None, None)["components"]["C1_adj"] == -6

    def test_d2_adj_values(self):
        assert compute_payoff("Normal", None, "Low",   None)["components"]["D2_adj"] == -3
        assert compute_payoff("Normal", None, "Ideal", None)["components"]["D2_adj"] ==  2
        assert compute_payoff("Normal", None, "High",  None)["components"]["D2_adj"] == -1

    def test_c2_adj_values(self):
        assert compute_payoff("Normal", None, None, "Favorable")["components"]["C2_adj"]    ==  4
        assert compute_payoff("Normal", None, None, "Intermediary")["components"]["C2_adj"] ==  0
        assert compute_payoff("Normal", None, None, "Challenging")["components"]["C2_adj"]  == -6

    def test_none_adjustment_is_none_in_components(self):
        result = compute_payoff("Early", None, None, None)
        assert result["components"]["C1_adj"] is None
        assert result["components"]["D2_adj"] is None
        assert result["components"]["C2_adj"] is None

    def test_none_adjustments_not_counted_in_total(self):
        full   = compute_payoff("Early", "Favorable", "Ideal", "Favorable")["payoff_sc_ha"]
        partial = compute_payoff("Early", None, None, None)["payoff_sc_ha"]
        assert full > partial

    # ── Return type ───────────────────────────────────────────────────────────

    def test_returns_dict_with_required_keys(self):
        result = compute_payoff("Normal", None, None, None)
        assert "payoff_sc_ha" in result
        assert "components" in result

    def test_payoff_is_float(self):
        result = compute_payoff("Early", "Favorable", "Ideal", "Favorable")
        assert isinstance(result["payoff_sc_ha"], float)
