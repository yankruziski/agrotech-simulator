"""Pydantic request and response schemas."""

from typing import Optional
from pydantic import BaseModel, field_validator, model_validator
from config import VALID_STATES, VALID_CROPS, VALID_SEASON_CODES


# ── Request ────────────────────────────────────────────────────────────────────

class SimulateRequest(BaseModel):
    state: str
    crop: str
    planting_date: str                   # ISO format: YYYY-MM-DD
    season_code: str = "Summer"
    soil_texture: Optional[str] = None
    soil_ph_min: Optional[float] = None
    soil_ph_max: Optional[float] = None
    seed_population: Optional[int] = None   # seeds/ha

    @field_validator("state")
    @classmethod
    def state_in_scope(cls, v: str) -> str:
        if v not in VALID_STATES:
            raise ValueError(f"State '{v}' is outside the supported scope: {VALID_STATES}")
        return v

    @field_validator("crop")
    @classmethod
    def crop_in_scope(cls, v: str) -> str:
        if v.lower() not in VALID_CROPS:
            raise ValueError(f"Crop '{v}' is not supported. Choose from: {VALID_CROPS}")
        return v.lower()

    @field_validator("season_code")
    @classmethod
    def season_in_scope(cls, v: str) -> str:
        if v not in VALID_SEASON_CODES:
            raise ValueError(f"Season code '{v}' is not valid. Choose from: {VALID_SEASON_CODES}")
        return v

    @model_validator(mode="after")
    def ph_range_consistent(self) -> "SimulateRequest":
        if self.soil_ph_min is not None and self.soil_ph_max is not None:
            if self.soil_ph_min > self.soil_ph_max:
                raise ValueError("soil_ph_min cannot be greater than soil_ph_max")
        return self


# ── Sub-schemas (used inside SimulateResponse) ─────────────────────────────────

class ClassificationResult(BaseModel):
    D1: str
    C1: Optional[str]
    D2: Optional[str]
    C2: Optional[str]


class PayoffComponents(BaseModel):
    D1_base: int
    C1_adj: Optional[int]
    D2_adj: Optional[int]
    C2_adj: Optional[int]


class DecisionTreeResult(BaseModel):
    payoff_sc_ha: float
    components: PayoffComponents


class ScenarioValue(BaseModel):
    yield_sc_ha: float
    percentile: str
    source: str
    description: str = ""


class Scenarios(BaseModel):
    pessimistic: ScenarioValue
    most_likely: ScenarioValue
    optimistic: ScenarioValue


class ComparableCase(BaseModel):
    case_id: str
    crop_year: str
    similarity_pct: int
    key_divergence: str
    state: str
    crop: str
    planting_month: int
    soil_texture: Optional[str]
    soil_ph_avg: Optional[float]
    seed_population_per_ha: Optional[float]
    observed_yield_sc_ha: float
    D1_class: str
    C1_class: Optional[str]
    D2_class: Optional[str]
    C2_class: Optional[str]


class AuditableMetrics(BaseModel):
    D1_class: str
    C1_class: Optional[str]
    D2_class: Optional[str]
    C2_class: Optional[str]
    planting_month: int
    soil_ph_avg: Optional[float]


class ModelAssumptions(BaseModel):
    immutable: list[str]
    auditable: AuditableMetrics


# ── Response ───────────────────────────────────────────────────────────────────

class SimulateResponse(BaseModel):
    classification: ClassificationResult
    decision_tree: DecisionTreeResult
    scenarios: Scenarios
    comparable_cases: list[ComparableCase]
    cv_seed_pct: Optional[float]
    plasticity_index: Optional[float]
    narrative: str
    model_assumptions: ModelAssumptions
    validation_warnings: list[str]


# ── Config response ────────────────────────────────────────────────────────────

class ConfigResponse(BaseModel):
    states: list[str]
    crops: list[str]
    season_codes: list[str]
    soil_textures: dict[str, list[str]]
    planting_windows: dict
    seed_population_thresholds: dict[str, int]
    ph_classes: dict
    adjustments: dict
    immutable_assumptions: list[str]


# ── Health ─────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    data_loaded: bool
    soybean_records: int
