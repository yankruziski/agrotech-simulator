"""
Maps raw user inputs to the four decision-tree variable classes:
  D1 — Planting Date  (Early / Normal / Late)
  C1 — Soil Texture   (Favorable / Intermediary / Challenging)
  D2 — Seed Population (Low / Ideal / High)
  C2 — Soil pH        (Favorable / Intermediary / Challenging)
"""

from datetime import date
from dateutil.parser import parse as parse_date
from typing import Optional
import config


def classify_d1(planting_date_str: str) -> tuple[str, int]:
    """Returns (class_name, planting_month)."""
    dt: date = parse_date(planting_date_str).date()
    month = dt.month
    for cls, info in config.PLANTING_WINDOW.items():
        if month in info["months"]:
            return cls, month
    # Should never happen given ISO date input, but default to Late
    return "Late", month


def classify_c1(soil_texture: Optional[str]) -> Optional[str]:
    if not soil_texture:
        return None
    texture_lower = soil_texture.lower().strip()
    for cls, textures in config.TEXTURE_CLASS.items():
        if texture_lower in [t.lower() for t in textures]:
            return cls
    # Partial match fallback
    for cls, textures in config.TEXTURE_CLASS.items():
        if any(t.lower() in texture_lower or texture_lower in t.lower() for t in textures):
            return cls
    return None


def classify_d2(seed_population: Optional[int]) -> Optional[str]:
    if seed_population is None:
        return None
    if seed_population <= config.SEED_POP_THRESHOLDS["low_max"]:
        return "Low"
    if seed_population <= config.SEED_POP_THRESHOLDS["ideal_max"]:
        return "Ideal"
    return "High"


def classify_c2(ph_min: Optional[float], ph_max: Optional[float]) -> Optional[str]:
    if ph_min is None or ph_max is None:
        return None
    ph_avg = (ph_min + ph_max) / 2
    if 5.5 <= ph_avg <= 6.5:
        return "Favorable"
    if 5.0 <= ph_avg < 5.5:
        return "Intermediary"
    return "Challenging"


def classify_all(
    planting_date: str,
    soil_texture: Optional[str],
    seed_population: Optional[int],
    soil_ph_min: Optional[float],
    soil_ph_max: Optional[float],
) -> dict:
    d1_class, month = classify_d1(planting_date)
    return {
        "D1": d1_class,
        "C1": classify_c1(soil_texture),
        "D2": classify_d2(seed_population),
        "C2": classify_c2(soil_ph_min, soil_ph_max),
        "planting_month": month,
        "soil_ph_avg": (
            (soil_ph_min + soil_ph_max) / 2
            if soil_ph_min is not None and soil_ph_max is not None
            else None
        ),
    }
