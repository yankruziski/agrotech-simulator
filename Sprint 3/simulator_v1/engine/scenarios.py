"""
Calculates the three yield scenarios (Pessimistic / Most Likely / Optimistic)
from historical records matching the user's classification.
"""

import numpy as np
import pandas as pd
from typing import Optional
import config
from data import loader
from engine.classifier import classify_c1, classify_d2, classify_c2


def _get_class_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["D1_class"] = out["planting_month"].map(
        lambda m: next(
            (cls for cls, info in config.PLANTING_WINDOW.items() if m in info["months"]),
            None,
        )
    )
    out["C1_class"] = out["soil_texture"].map(classify_c1)
    out["D2_class"] = out["seed_actual_population_per_hectare"].map(
        lambda p: classify_d2(int(p)) if pd.notna(p) else None
    )
    out["C2_class"] = out.apply(
        lambda r: classify_c2(
            r["soil_ph_min"] if pd.notna(r["soil_ph_min"]) else None,
            r["soil_ph_max"] if pd.notna(r["soil_ph_max"]) else None,
        ),
        axis=1,
    )
    return out


def _similarity_score(row: pd.Series, d1: str, c1: Optional[str], d2: Optional[str], c2: Optional[str]) -> int:
    """Percentage of classes that match (0–100)."""
    classes = [("D1_class", d1), ("C1_class", c1), ("D2_class", d2), ("C2_class", c2)]
    matched = sum(
        1 for col, ref in classes
        if ref is not None and pd.notna(row.get(col)) and row.get(col) == ref
    )
    total = sum(1 for _, ref in classes if ref is not None)
    return int(matched / total * 100) if total else 0


def _key_divergence(row: pd.Series, d1: str, c1: Optional[str], d2: Optional[str], c2: Optional[str]) -> str:
    labels = {"D1_class": "planting window", "C1_class": "soil texture",
              "D2_class": "seed population", "C2_class": "soil pH"}
    diffs = [
        f"{labels[col]} ({row.get(col)} vs {ref})"
        for col, ref in [("D1_class", d1), ("C1_class", c1), ("D2_class", d2), ("C2_class", c2)]
        if ref is not None and pd.notna(row.get(col)) and row.get(col) != ref
    ]
    return ", ".join(diffs) if diffs else "All classes match"


def compute_scenarios(
    state: str,
    crop: str,
    d1: str,
    c1: Optional[str],
    d2: Optional[str],
    c2: Optional[str],
    payoff_sc_ha: float,
) -> dict:
    df = loader.get()
    classified = _get_class_columns(df)

    base_mask = (
        (classified["state"].str.upper() == state.upper()) &
        (classified["crop_name"].str.lower().str.contains(crop.lower(), na=False))
    )

    mask_full = base_mask & (classified["D1_class"] == d1)
    if c1:
        mask_full = mask_full & (classified["C1_class"] == c1)
    if d2:
        mask_full = mask_full & (classified["D2_class"] == d2)
    if c2:
        mask_full = mask_full & (classified["C2_class"] == c2)

    subset = classified[mask_full & classified["yield_sc_ha"].notna()]

    mask_d1 = base_mask & (classified["D1_class"] == d1)

    source = "historical_data"
    if len(subset) >= config.MIN_COMPARABLE_FOR_PERCENTILES:
        p25 = float(np.percentile(subset["yield_sc_ha"], 25))
        p50 = float(np.percentile(subset["yield_sc_ha"], 50))
        p75 = float(np.percentile(subset["yield_sc_ha"], 75))
    else:
        d1_group = classified[mask_d1 & classified["yield_sc_ha"].notna()]
        std = float(d1_group["yield_sc_ha"].std()) if len(d1_group) > 1 else 6.0
        p25 = payoff_sc_ha - std
        p50 = payoff_sc_ha
        p75 = payoff_sc_ha + std
        source = "fallback_stddev"

    # CV of seed distribution from matched records
    pool_for_metrics = subset if len(subset) >= 3 else classified[mask_d1 & classified["yield_sc_ha"].notna()]
    seed_series = pool_for_metrics["seed_actual_population_per_hectare"].dropna()
    if len(seed_series) > 1 and seed_series.mean() > 0:
        cv_seed = round(float(seed_series.std() / seed_series.mean() * 100), 1)
    else:
        cv_seed = None

    # Phenotypic plasticity: yield range relative to baseline
    plasticity = round((p75 - p25) / p50, 2) if p50 > 0 else None

    scenarios = {
        "pessimistic": {
            "yield_sc_ha": round(p25, 1),
            "percentile": "P25",
            "source": source,
            "description": _scenario_desc("pessimistic", p25, d1, c1, d2, c2),
        },
        "most_likely": {
            "yield_sc_ha": round(p50, 1),
            "percentile": "P50 / Expected Value",
            "source": source,
            "description": _scenario_desc("most_likely", p50, d1, c1, d2, c2),
        },
        "optimistic": {
            "yield_sc_ha": round(p75, 1),
            "percentile": "P75",
            "source": source,
            "description": _scenario_desc("optimistic", p75, d1, c1, d2, c2),
        },
    }

    comparable_pool = classified[mask_full & classified["yield_sc_ha"].notna()].copy()
    if len(comparable_pool) == 0:
        comparable_pool = classified[mask_d1 & classified["yield_sc_ha"].notna()].copy()

    cases = _pick_comparable_cases(comparable_pool, d1, c1, d2, c2)

    return {
        "scenarios": scenarios,
        "comparable_cases": cases,
        "cv_seed_pct": cv_seed,
        "plasticity_index": plasticity,
    }


def _scenario_desc(kind: str, value: float, d1: str, c1: Optional[str], d2: Optional[str], c2: Optional[str]) -> str:
    d1_txt = {"Early": "optimal early planting window", "Normal": "standard planting window", "Late": "delayed planting window"}.get(d1, d1)
    if kind == "pessimistic":
        factors = []
        if c1 == "Challenging":
            factors.append("sandy soil reducing water retention")
        if d2 == "Low":
            factors.append("sub-optimal seed density")
        if c2 in ("Intermediary", "Challenging"):
            factors.append("limiting soil pH")
        desc = ", ".join(factors) if factors else "adverse agronomic combination for this configuration"
        return f"Below-average outcome assuming {desc}."
    if kind == "most_likely":
        return f"Expected outcome for {d1_txt} in this region, based on historical field records with similar configuration."
    if kind == "optimistic":
        factors = []
        if c1 == "Favorable":
            factors.append("clay soil maximising water retention")
        if d2 == "Ideal":
            factors.append("ideal seed density")
        if c2 == "Favorable":
            factors.append("optimal pH nutrient availability")
        desc = ", ".join(factors) if factors else "favourable agronomic conditions"
        return f"Above-average outcome with {desc}."
    return ""


def _pick_comparable_cases(
    pool: pd.DataFrame,
    d1: str,
    c1: Optional[str],
    d2: Optional[str],
    c2: Optional[str],
) -> list[dict]:
    if pool.empty:
        return []

    sample = pool.sample(n=min(config.MAX_COMPARABLE_CASES, len(pool)), random_state=42)

    cases = []
    for i, (_, row) in enumerate(sample.iterrows(), start=1):
        sim = _similarity_score(row, d1, c1, d2, c2)
        div = _key_divergence(row, d1, c1, d2, c2)

        crop_year = str(row["crop_year"]) if pd.notna(row.get("crop_year")) else "—"
        field_id  = str(row.get("field_uuid", ""))[:8].upper() if pd.notna(row.get("field_uuid")) else f"CASE-{i:03d}"

        cases.append({
            "case_id": field_id,
            "crop_year": crop_year,
            "similarity_pct": sim,
            "state": str(row.get("state", "")),
            "crop": str(row.get("crop_name", "")),
            "planting_month": int(row["planting_month"]) if pd.notna(row.get("planting_month")) else 0,
            "soil_texture": str(row["soil_texture"]) if pd.notna(row.get("soil_texture")) else None,
            "soil_ph_avg": round(float(row["soil_ph_avg"]), 2) if pd.notna(row.get("soil_ph_avg")) else None,
            "seed_population_per_ha": round(float(row["seed_actual_population_per_hectare"]), 0) if pd.notna(row.get("seed_actual_population_per_hectare")) else None,
            "observed_yield_sc_ha": round(float(row["yield_sc_ha"]), 1),
            "D1_class": str(row.get("D1_class", d1)),
            "C1_class": str(row["C1_class"]) if pd.notna(row.get("C1_class")) else None,
            "D2_class": str(row["D2_class"]) if pd.notna(row.get("D2_class")) else None,
            "C2_class": str(row["C2_class"]) if pd.notna(row.get("C2_class")) else None,
            "key_divergence": div,
        })
    return sorted(cases, key=lambda x: x["similarity_pct"], reverse=True)
