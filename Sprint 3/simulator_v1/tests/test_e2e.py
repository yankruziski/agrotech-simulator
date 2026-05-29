"""
End-to-end browser tests using Playwright.

Requirements:
    pip install pytest-playwright
    playwright install chromium

Run:
    pytest tests/test_e2e.py -v -m e2e
    (the live_server fixture starts uvicorn automatically if not already running)
"""

import pytest
from playwright.sync_api import Page, expect


pytestmark = pytest.mark.e2e


@pytest.fixture(autouse=True)
def server(live_server):
    """Ensure the live server is running for every test in this module."""
    return live_server


BASE = "http://localhost:8000"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def fill_and_run(page: Page, *, state="MG", date="15/10/2024",
                 population="275000", ph_min="5.8", ph_max="6.2",
                 texture="clay"):
    """Navigate to simulator, fill minimum fields, and click RUN SIMULATION."""
    page.goto(f"{BASE}/#simulator")
    page.select_option("#f-state", state)
    page.fill("#f-planting-date", date)
    if population:
        page.fill("#f-population", population)
    if ph_min:
        page.fill("#f-ph-min", ph_min)
    if ph_max:
        page.fill("#f-ph-max", ph_max)
    if texture:
        page.fill("#f-soil-texture", texture)
    page.click("#sim-run-btn")
    page.wait_for_url(f"{BASE}/#historical", timeout=20_000)


# ─── Home page ────────────────────────────────────────────────────────────────

class TestHomePage:
    def test_page_title(self, page: Page):
        page.goto(BASE)
        expect(page).to_have_title("AgroTech Precision")

    def test_navbar_links_visible(self, page: Page):
        page.goto(BASE)
        expect(page.get_by_text("HOME",       exact=True)).to_be_visible()
        expect(page.get_by_text("SIMULATOR",  exact=True)).to_be_visible()
        expect(page.get_by_text("HISTORICAL", exact=True)).to_be_visible()

    def test_cta_button_navigates_to_simulator(self, page: Page):
        page.goto(BASE)
        page.click("text=CONFIGURE NEW SIMULATION")
        expect(page).to_have_url(f"{BASE}/#simulator")

    def test_home_hero_visible(self, page: Page):
        page.goto(BASE)
        expect(page.locator(".hero-banner")).to_be_visible()

    def test_feature_cards_visible(self, page: Page):
        page.goto(BASE)
        expect(page.locator(".feature-card")).to_have_count(3)


# ─── Simulator page ───────────────────────────────────────────────────────────

class TestSimulatorPage:
    def test_state_dropdown_has_four_options(self, page: Page):
        page.goto(f"{BASE}/#simulator")
        options = page.locator("#f-state option")
        assert options.count() == 4

    def test_action_bar_visible_on_simulator(self, page: Page):
        page.goto(f"{BASE}/#simulator")
        expect(page.locator("#sim-action-bar")).to_be_visible()

    def test_action_bar_hidden_on_home(self, page: Page):
        page.goto(BASE)
        expect(page.locator("#sim-action-bar")).to_be_hidden()

    def test_season_toggle_changes_active_button(self, page: Page):
        page.goto(f"{BASE}/#simulator")
        page.click("[data-season='Safrinha']")
        btn = page.locator("[data-season='Safrinha']")
        assert "active" in (btn.get_attribute("class") or "")

    def test_run_simulation_without_date_stays_on_simulator(self, page: Page):
        page.goto(f"{BASE}/#simulator")
        page.select_option("#f-state", "MG")
        # Do NOT fill planting date — should show alert and stay
        page.on("dialog", lambda d: d.dismiss())
        page.click("#sim-run-btn")
        # Should NOT navigate away
        assert "#historical" not in page.url


# ─── Full simulation flow ─────────────────────────────────────────────────────

class TestSimulationFlow:
    def test_navigates_to_historical_after_run(self, page: Page):
        fill_and_run(page)
        assert page.url == f"{BASE}/#historical"

    def test_baseline_value_shows_sc_ha(self, page: Page):
        fill_and_run(page)
        baseline = page.locator("#r-baseline-value").inner_text()
        assert "sc/ha" in baseline

    def test_pessimistic_value_shows_sc_ha(self, page: Page):
        fill_and_run(page)
        assert "sc/ha" in page.locator("#r-pessimistic-value").inner_text()

    def test_optimistic_value_shows_sc_ha(self, page: Page):
        fill_and_run(page)
        assert "sc/ha" in page.locator("#r-optimistic-value").inner_text()

    def test_insight_text_nonempty(self, page: Page):
        fill_and_run(page)
        insight = page.locator("#r-insight").inner_text()
        assert len(insight) > 20

    def test_cv_seed_metric_populated(self, page: Page):
        fill_and_run(page)
        cv = page.locator("#r-cv-seed").inner_text()
        assert cv != "" and cv != "N/A"

    def test_plasticity_index_populated(self, page: Page):
        fill_and_run(page)
        pi = page.locator("#r-plasticity").inner_text()
        assert pi != ""

    def test_comparable_cases_table_has_rows(self, page: Page):
        fill_and_run(page)
        rows = page.locator("#r-cases-tbody tr")
        assert rows.count() > 0

    def test_comparable_case_row_contains_sc_ha(self, page: Page):
        fill_and_run(page)
        first_row = page.locator("#r-cases-tbody tr").first
        assert "sc/ha" in first_row.inner_text()

    def test_scenario_descriptions_nonempty(self, page: Page):
        fill_and_run(page)
        for el_id in ["r-pessimistic-desc", "r-baseline-desc", "r-optimistic-desc"]:
            text = page.locator(f"#{el_id}").inner_text()
            assert len(text) > 10, f"{el_id} description is too short: '{text}'"

    def test_immutable_assumptions_listed(self, page: Page):
        fill_and_run(page)
        items = page.locator("#r-immutable-list .assumption-item")
        assert items.count() > 0

    def test_auditable_metrics_listed(self, page: Page):
        fill_and_run(page)
        items = page.locator("#r-auditable-list .assumption-item")
        assert items.count() > 0

    def test_crop_field_populated(self, page: Page):
        fill_and_run(page)
        crop = page.locator("#r-crop").inner_text()
        assert crop != ""

    def test_sim_date_populated(self, page: Page):
        fill_and_run(page)
        sim_date = page.locator("#r-sim-date").inner_text()
        assert sim_date != "" and sim_date != "—"

    def test_results_footer_visible(self, page: Page):
        fill_and_run(page)
        expect(page.locator("#results-footer-bar")).to_be_visible()

    def test_edit_configuration_button_returns_to_simulator(self, page: Page):
        fill_and_run(page)
        page.click("#results-edit-btn")
        expect(page).to_have_url(f"{BASE}/#simulator")


# ─── Multi-state smoke tests ──────────────────────────────────────────────────

class TestAllStates:
    @pytest.mark.parametrize("state", ["MG", "PR", "MS", "GO"])
    def test_simulation_completes_for_state(self, page: Page, state: str):
        fill_and_run(page, state=state)
        baseline = page.locator("#r-baseline-value").inner_text()
        assert "sc/ha" in baseline, f"No yield result for state {state}"
