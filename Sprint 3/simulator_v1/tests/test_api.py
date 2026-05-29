"""
Integration tests for the FastAPI endpoints using FastAPI's TestClient.
No live server required — the CSV is loaded once via the session-scoped client fixture.
"""

import pytest


VALID = {
    "state": "MG",
    "crop": "soybeans",
    "planting_date": "2024-10-15",
    "soil_texture": "clay",
    "soil_ph_min": 5.8,
    "soil_ph_max": 6.2,
    "seed_population": 300_000,
}


# ── GET /health ────────────────────────────────────────────────────────────────

class TestHealth:
    def test_status_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_data_loaded(self, client):
        assert client.get("/health").json()["data_loaded"] is True

    def test_record_count_reasonable(self, client):
        count = client.get("/health").json()["soybean_records"]
        assert count > 100_000


# ── GET /config ────────────────────────────────────────────────────────────────

class TestConfig:
    def test_status_ok(self, client):
        assert client.get("/config").status_code == 200

    def test_has_all_top_level_keys(self, client):
        body = client.get("/config").json()
        for key in ["states", "crops", "season_codes", "soil_textures",
                    "planting_windows", "seed_population_thresholds",
                    "ph_classes", "adjustments", "immutable_assumptions"]:
            assert key in body, f"Missing key: {key}"

    def test_valid_states(self, client):
        states = client.get("/config").json()["states"]
        assert set(states) == {"MG", "PR", "MS", "GO"}

    def test_valid_crops(self, client):
        crops = client.get("/config").json()["crops"]
        assert "soybeans" in crops

    def test_planting_windows_have_three_classes(self, client):
        pw = client.get("/config").json()["planting_windows"]
        assert set(pw.keys()) == {"Early", "Normal", "Late"}

    def test_adjustments_structure(self, client):
        adj = client.get("/config").json()["adjustments"]
        assert "C1" in adj and "D2" in adj and "C2" in adj

    def test_immutable_assumptions_nonempty(self, client):
        ia = client.get("/config").json()["immutable_assumptions"]
        assert isinstance(ia, list) and len(ia) > 0


# ── POST /simulate ─────────────────────────────────────────────────────────────

class TestSimulateClassification:
    def test_early_clay_ideal_favorable(self, client):
        body = client.post("/simulate", json=VALID).json()
        assert body["classification"] == {
            "D1": "Early", "C1": "Favorable", "D2": "Ideal", "C2": "Favorable"
        }

    @pytest.mark.parametrize("date_str,expected_d1", [
        ("2024-09-15", "Early"),
        ("2024-10-15", "Early"),
        ("2024-11-10", "Normal"),
        ("2024-12-01", "Late"),
        ("2025-01-15", "Late"),
        ("2025-03-10", "Late"),
    ])
    def test_d1_classification_by_date(self, client, date_str, expected_d1):
        body = client.post("/simulate", json={**VALID, "planting_date": date_str}).json()
        assert body["classification"]["D1"] == expected_d1

    @pytest.mark.parametrize("pop,expected_d2", [
        (200_000, "Low"),
        (280_000, "Low"),
        (300_000, "Ideal"),
        (320_000, "Ideal"),
        (350_000, "High"),
    ])
    def test_d2_classification_by_population(self, client, pop, expected_d2):
        body = client.post("/simulate", json={**VALID, "seed_population": pop}).json()
        assert body["classification"]["D2"] == expected_d2

    @pytest.mark.parametrize("ph_min,ph_max,expected_c2", [
        (5.8, 6.2, "Favorable"),
        (5.0, 5.0, "Intermediary"),
        (6.6, 6.8, "Challenging"),
        (4.0, 4.5, "Challenging"),
        (7.0, 7.5, "Challenging"),
    ])
    def test_c2_classification_by_ph(self, client, ph_min, ph_max, expected_c2):
        body = client.post("/simulate", json={**VALID, "soil_ph_min": ph_min, "soil_ph_max": ph_max}).json()
        assert body["classification"]["C2"] == expected_c2


class TestSimulatePayoff:
    def test_best_case_payoff(self, client):
        # Early(64) + Favorable(+4) + Ideal(+2) + Favorable(+4) = 74
        body = client.post("/simulate", json=VALID).json()
        assert body["decision_tree"]["payoff_sc_ha"] == 74.0

    def test_d1_only_payoff(self, client):
        payload = {"state": "MG", "crop": "soybeans", "planting_date": "2024-10-15"}
        body = client.post("/simulate", json=payload).json()
        assert body["decision_tree"]["payoff_sc_ha"] == 64.0

    def test_late_planting_reduces_payoff(self, client):
        early = client.post("/simulate", json={**VALID, "planting_date": "2024-10-15"}).json()
        late  = client.post("/simulate", json={**VALID, "planting_date": "2025-01-15"}).json()
        assert early["decision_tree"]["payoff_sc_ha"] > late["decision_tree"]["payoff_sc_ha"]

    def test_challenging_soil_reduces_payoff(self, client):
        favorable   = client.post("/simulate", json={**VALID, "soil_texture": "clay"}).json()
        challenging = client.post("/simulate", json={**VALID, "soil_texture": "sandy"}).json()
        assert favorable["decision_tree"]["payoff_sc_ha"] > challenging["decision_tree"]["payoff_sc_ha"]


class TestSimulateScenarios:
    def test_scenario_keys_present(self, client):
        sc = client.post("/simulate", json=VALID).json()["scenarios"]
        assert set(sc.keys()) == {"pessimistic", "most_likely", "optimistic"}

    def test_each_scenario_has_required_fields(self, client):
        sc = client.post("/simulate", json=VALID).json()["scenarios"]
        for name in ["pessimistic", "most_likely", "optimistic"]:
            assert "yield_sc_ha" in sc[name]
            assert "percentile" in sc[name]
            assert "source" in sc[name]
            assert "description" in sc[name]

    def test_scenario_yield_values_positive(self, client):
        sc = client.post("/simulate", json=VALID).json()["scenarios"]
        assert sc["pessimistic"]["yield_sc_ha"] > 0
        assert sc["most_likely"]["yield_sc_ha"] > 0
        assert sc["optimistic"]["yield_sc_ha"] > 0

    def test_scenario_ordering_pess_le_base_le_opt(self, client):
        sc = client.post("/simulate", json=VALID).json()["scenarios"]
        assert sc["pessimistic"]["yield_sc_ha"] <= sc["most_likely"]["yield_sc_ha"]
        assert sc["most_likely"]["yield_sc_ha"] <= sc["optimistic"]["yield_sc_ha"]

    def test_source_is_valid_value(self, client):
        sc = client.post("/simulate", json=VALID).json()["scenarios"]
        valid_sources = {"historical_data", "fallback_stddev"}
        for name in ["pessimistic", "most_likely", "optimistic"]:
            assert sc[name]["source"] in valid_sources

    def test_cv_seed_present_with_full_payload(self, client):
        body = client.post("/simulate", json=VALID).json()
        assert "cv_seed_pct" in body
        assert body["cv_seed_pct"] is not None

    def test_plasticity_index_present_with_full_payload(self, client):
        body = client.post("/simulate", json=VALID).json()
        assert "plasticity_index" in body
        assert body["plasticity_index"] is not None


class TestSimulateComparableCases:
    def test_comparable_cases_present(self, client):
        body = client.post("/simulate", json=VALID).json()
        assert "comparable_cases" in body
        assert len(body["comparable_cases"]) > 0

    def test_comparable_case_has_required_fields(self, client):
        cases = client.post("/simulate", json=VALID).json()["comparable_cases"]
        for case in cases:
            assert "case_id" in case
            assert "crop_year" in case
            assert "similarity_pct" in case
            assert "observed_yield_sc_ha" in case
            assert "key_divergence" in case

    def test_comparable_cases_sorted_by_similarity(self, client):
        cases = client.post("/simulate", json=VALID).json()["comparable_cases"]
        sims = [c["similarity_pct"] for c in cases]
        assert sims == sorted(sims, reverse=True)

    def test_similarity_pct_in_range(self, client):
        cases = client.post("/simulate", json=VALID).json()["comparable_cases"]
        for case in cases:
            assert 0 <= case["similarity_pct"] <= 100

    def test_max_five_comparable_cases(self, client):
        cases = client.post("/simulate", json=VALID).json()["comparable_cases"]
        assert len(cases) <= 5


class TestSimulateNarrative:
    def test_narrative_nonempty_string(self, client):
        narrative = client.post("/simulate", json=VALID).json()["narrative"]
        assert isinstance(narrative, str)
        assert len(narrative) > 50

    def test_narrative_contains_state(self, client):
        narrative = client.post("/simulate", json=VALID).json()["narrative"]
        assert "MG" in narrative

    def test_narrative_different_for_different_inputs(self, client):
        n_early = client.post("/simulate", json={**VALID, "planting_date": "2024-10-01"}).json()["narrative"]
        n_late  = client.post("/simulate", json={**VALID, "planting_date": "2025-01-15"}).json()["narrative"]
        assert n_early != n_late


class TestSimulateWarnings:
    def test_no_warnings_full_valid_payload(self, client):
        body = client.post("/simulate", json=VALID).json()
        assert body["validation_warnings"] == []

    def test_warning_when_soil_texture_missing(self, client):
        payload = {k: v for k, v in VALID.items() if k != "soil_texture"}
        warnings = client.post("/simulate", json=payload).json()["validation_warnings"]
        assert any("soil_texture" in w or "C1" in w for w in warnings)

    def test_warning_when_seed_population_missing(self, client):
        payload = {k: v for k, v in VALID.items() if k != "seed_population"}
        warnings = client.post("/simulate", json=payload).json()["validation_warnings"]
        assert any("seed_population" in w or "D2" in w for w in warnings)

    def test_warning_when_ph_missing(self, client):
        payload = {k: v for k, v in VALID.items() if k not in ("soil_ph_min", "soil_ph_max")}
        warnings = client.post("/simulate", json=payload).json()["validation_warnings"]
        assert any("ph" in w.lower() or "C2" in w for w in warnings)

    def test_warning_outlier_seed_population(self, client):
        body = client.post("/simulate", json={**VALID, "seed_population": 3_000_000}).json()
        assert any("2,000,000" in w or "seeds/ha" in w for w in body["validation_warnings"])

    def test_warning_only_ph_min_provided(self, client):
        payload = {**VALID, "soil_ph_max": None}
        body = client.post("/simulate", json=payload).json()
        assert any("ph" in w.lower() for w in body["validation_warnings"])


class TestSimulateValidation:
    def test_invalid_state_422(self, client):
        r = client.post("/simulate", json={**VALID, "state": "XX"})
        assert r.status_code == 422

    def test_missing_planting_date_422(self, client):
        payload = {k: v for k, v in VALID.items() if k != "planting_date"}
        assert client.post("/simulate", json=payload).status_code == 422

    def test_missing_state_422(self, client):
        payload = {k: v for k, v in VALID.items() if k != "state"}
        assert client.post("/simulate", json=payload).status_code == 422

    def test_missing_crop_422(self, client):
        payload = {k: v for k, v in VALID.items() if k != "crop"}
        assert client.post("/simulate", json=payload).status_code == 422

    def test_invalid_crop_422(self, client):
        assert client.post("/simulate", json={**VALID, "crop": "wheat"}).status_code == 422

    def test_ph_min_greater_than_ph_max_422(self, client):
        r = client.post("/simulate", json={**VALID, "soil_ph_min": 7.0, "soil_ph_max": 5.0})
        assert r.status_code == 422

    def test_empty_body_422(self, client):
        assert client.post("/simulate", json={}).status_code == 422

    @pytest.mark.parametrize("state", ["MG", "PR", "MS", "GO"])
    def test_all_valid_states_return_200(self, client, state):
        r = client.post("/simulate", json={**VALID, "state": state})
        assert r.status_code == 200, f"State {state} failed with {r.status_code}"
