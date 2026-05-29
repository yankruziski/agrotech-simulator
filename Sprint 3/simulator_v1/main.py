"""
Bayer Yield Simulator — Backend v1
FastAPI application. No database; all data loaded from CSV at startup.

Run:
    uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import config
from data import loader
from models import SimulateRequest, SimulateResponse, ConfigResponse, HealthResponse
from engine.classifier import classify_all
from engine.decision_tree import compute_payoff
from engine.scenarios import compute_scenarios
from engine.narrative import generate as generate_narrative


# ── Lifespan: load CSV once at startup ────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    loader.load()
    print(f"[startup] Dataset loaded — {len(loader.get()):,} soybean records")
    yield


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Bayer Yield Simulator API",
    version="1.0.0",
    description="Decision-tree backend for the soybean yield simulator.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to the frontend origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    """Liveness check. Confirms the dataset is loaded."""
    try:
        df = loader.get()
        return {"status": "ok", "data_loaded": True, "soybean_records": len(df)}
    except RuntimeError:
        return {"status": "degraded", "data_loaded": False, "soybean_records": 0}


@app.get("/config", response_model=ConfigResponse, tags=["Configuration"])
def get_config():
    """
    Returns all static model parameters and valid input options.
    The frontend must build every dropdown and threshold from this response —
    no agronomic values should be hardcoded in the UI.
    """
    return {
        "states": config.VALID_STATES,
        "crops": config.VALID_CROPS,
        "season_codes": config.VALID_SEASON_CODES,
        "soil_textures": config.TEXTURE_CLASS,
        "planting_windows": config.PLANTING_WINDOW,
        "seed_population_thresholds": config.SEED_POP_THRESHOLDS,
        "ph_classes": config.PH_CLASSES,
        "adjustments": {
            "C1": config.C1_ADJ,
            "D2": config.D2_ADJ,
            "C2": config.C2_ADJ,
        },
        "immutable_assumptions": config.IMMUTABLE_ASSUMPTIONS,
    }


@app.post("/simulate", response_model=SimulateResponse, tags=["Simulation"])
def simulate(req: SimulateRequest):
    """
    Runs the decision-tree simulation and returns scenarios, comparable cases,
    and a narrative recommendation.

    Required fields: state, crop, planting_date.
    Optional fields: soil_texture, soil_ph_min, soil_ph_max, seed_population.
    """
    warnings: list[str] = []

    # ── 1. Validate optional inputs ──────────────────────────────────────────
    if req.seed_population is not None and req.seed_population > config.SEED_POP_OUTLIER_MAX:
        warnings.append(
            f"seed_population ({req.seed_population:,}) exceeds 2,000,000 seeds/ha — "
            "this is outside the normal agronomic range and may affect result quality."
        )

    if req.soil_ph_min is not None and req.soil_ph_max is None:
        warnings.append("soil_ph_max not provided; pH classification will be skipped.")
    if req.soil_ph_max is not None and req.soil_ph_min is None:
        warnings.append("soil_ph_min not provided; pH classification will be skipped.")

    if req.soil_texture is None:
        warnings.append("soil_texture not provided; C1 soil-texture adjustment will not be applied.")
    if req.seed_population is None:
        warnings.append("seed_population not provided; D2 seed-density adjustment will not be applied.")
    if req.soil_ph_min is None or req.soil_ph_max is None:
        warnings.append("soil_ph_min / soil_ph_max not provided; C2 pH adjustment will not be applied.")

    # ── 2. Classify inputs ──────────────────────────────────────────────────
    cls = classify_all(
        planting_date=req.planting_date,
        soil_texture=req.soil_texture,
        seed_population=req.seed_population,
        soil_ph_min=req.soil_ph_min,
        soil_ph_max=req.soil_ph_max,
    )
    d1, c1, d2, c2 = cls["D1"], cls["C1"], cls["D2"], cls["C2"]

    if c1 is None and req.soil_texture:
        warnings.append(
            f"soil_texture '{req.soil_texture}' was not recognised. "
            "C1 adjustment skipped. Check the /config endpoint for valid texture names."
        )

    # ── 3. Decision-tree payoff ──────────────────────────────────────────────
    tree = compute_payoff(d1, c1, d2, c2)

    # ── 4. Historical scenarios + comparable cases ───────────────────────────
    sim = compute_scenarios(
        state=req.state,
        crop=req.crop,
        d1=d1, c1=c1, d2=d2, c2=c2,
        payoff_sc_ha=tree["payoff_sc_ha"],
    )

    # ── 5. Narrative ─────────────────────────────────────────────────────────
    sc = sim["scenarios"]
    narrative = generate_narrative(
        d1=d1, c1=c1, d2=d2, c2=c2,
        state=req.state,
        pessimistic=sc["pessimistic"]["yield_sc_ha"],
        most_likely=sc["most_likely"]["yield_sc_ha"],
        optimistic=sc["optimistic"]["yield_sc_ha"],
        n_comparable=len(sim["comparable_cases"]),
    )

    # ── 6. Assemble response ─────────────────────────────────────────────────
    return {
        "classification": {"D1": d1, "C1": c1, "D2": d2, "C2": c2},
        "decision_tree": tree,
        "scenarios": sc,
        "comparable_cases": sim["comparable_cases"],
        "cv_seed_pct": sim["cv_seed_pct"],
        "plasticity_index": sim["plasticity_index"],
        "narrative": narrative,
        "model_assumptions": {
            "immutable": config.IMMUTABLE_ASSUMPTIONS,
            "auditable": {
                "D1_class": d1,
                "C1_class": c1,
                "D2_class": d2,
                "C2_class": c2,
                "planting_month": cls["planting_month"],
                "soil_ph_avg": cls["soil_ph_avg"],
            },
        },
        "validation_warnings": warnings,
    }


# ── Serve frontend — must be last, after all API routes ───────────────────────

_frontend_dir = Path(__file__).parent / "Simulador"
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
