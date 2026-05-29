"""
Loads and joins the planting + harvest CSVs once at startup.
The resulting DataFrame is kept in memory; no database is used.
"""

import pandas as pd
from pathlib import Path

# Adjust these paths relative to the repo root if needed
_BASE = Path(__file__).parent.parent.parent  # Sprint 3/
PLANTING_CSV = _BASE / "data" / "planting_summary_brazil.csv"
HARVEST_CSV  = _BASE.parent / "Sprint 2" / "payoffMatrix" / "harvest_summary_brazil.csv"

# Slim, pre-joined dataset produced by build_dataset.py. Preferred in production:
# it is already filtered/derived, so startup skips the heavy merge (~240 MB → ~58 MB RAM).
SLIM_CSV = _BASE / "data" / "simulator_dataset.csv"

_df: pd.DataFrame | None = None


def load(force_raw: bool = False) -> pd.DataFrame:
    """Load the dataset once on startup.

    If the slim pre-processed dataset exists (and force_raw is False), read it
    directly. Otherwise build it from the raw planting + harvest CSVs.
    """
    global _df

    if not force_raw and SLIM_CSV.exists():
        _df = pd.read_csv(SLIM_CSV, low_memory=False)
        return _df

    planting = pd.read_csv(PLANTING_CSV, low_memory=False)
    harvest  = pd.read_csv(HARVEST_CSV,  low_memory=False)

    # Join on field_uuid + season
    joined = planting.merge(
        harvest[["field_uuid", "concrete_growing_season_name", "average_yield"]],
        on=["field_uuid", "concrete_growing_season_name"],
        how="inner",
    )

    # Filter soybeans only (corn support deferred)
    joined = joined[joined["crop_name"].str.lower().str.contains("soy", na=False)].copy()

    # Remove seed-population outliers
    joined = joined[joined["seed_actual_population_per_hectare"] <= 2_000_000]

    # Convert yield kg/ha → sc/ha
    joined["yield_sc_ha"] = joined["average_yield"] / 60.0

    # Derive useful columns
    joined["planting_month"] = pd.to_datetime(
        joined["planting_date"], errors="coerce"
    ).dt.month

    joined["soil_ph_avg"] = (
        pd.to_numeric(joined["soil_ph_min"], errors="coerce") +
        pd.to_numeric(joined["soil_ph_max"], errors="coerce")
    ) / 2

    _df = joined
    return _df


def get() -> pd.DataFrame:
    if _df is None:
        raise RuntimeError("Dataset not loaded. Call loader.load() first.")
    return _df
