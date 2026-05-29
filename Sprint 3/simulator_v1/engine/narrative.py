"""
Generates a plain-language recommendation paragraph from the classification
and scenario results. Template-based — no LLM dependency.
"""

from typing import Optional


_D1_DESC = {
    "Early":  "early planting window (September–October)",
    "Normal": "normal planting window (November)",
    "Late":   "late planting window (December–March)",
}

_C1_DESC = {
    "Favorable":    "favorable clay soil",
    "Intermediary": "intermediary loam soil",
    "Challenging":  "challenging sandy soil",
}

_D2_DESC = {
    "Low":   "seed population below the recommended range (≤ 280,000 seeds/ha), which reduces area utilisation",
    "Ideal": "seed population in the ideal range (280,001–320,000 seeds/ha), maximising yield potential",
    "High":  "seed population above the recommended range (> 320,000 seeds/ha), which may increase inter-plant competition",
}

_C2_DESC = {
    "Favorable":   "favorable soil pH (5.5–6.5), supporting optimal nutrient availability",
    "Intermediary": "intermediary soil pH (5.0–<5.5), which may limit nutrient uptake",
    "Challenging":  "challenging soil pH (< 5.0 or > 6.5), significantly impairing crop nutrition",
}


def generate(
    d1: str,
    c1: Optional[str],
    d2: Optional[str],
    c2: Optional[str],
    state: str,
    pessimistic: float,
    most_likely: float,
    optimistic: float,
    n_comparable: int,
) -> str:
    parts: list[str] = []

    d1_txt = _D1_DESC.get(d1, d1)
    parts.append(
        f"Based on your {d1_txt} in {state}, the model projects a most likely yield "
        f"of {most_likely:.1f} sc/ha, with a range from {pessimistic:.1f} sc/ha (pessimistic) "
        f"to {optimistic:.1f} sc/ha (optimistic)."
    )

    if c1:
        c1_txt = _C1_DESC.get(c1, c1)
        parts.append(f"Your field presents {c1_txt}.")

    if d2:
        d2_txt = _D2_DESC.get(d2, d2)
        parts.append(f"The configured {d2_txt}.")

    if c2:
        c2_txt = _C2_DESC.get(c2, c2)
        parts.append(f"Soil chemistry shows {c2_txt}.")

    if d2 == "Low":
        parts.append(
            "Consider adjusting seed density toward the ideal range (280,000–320,000 seeds/ha) "
            "to improve area utilisation in the next season."
        )
    elif c2 == "Intermediary":
        parts.append(
            "Liming to bring pH closer to the 5.5–6.5 range may recover up to 4 sc/ha "
            "by improving phosphorus and micronutrient availability."
        )
    elif c2 == "Challenging":
        parts.append(
            "Soil pH correction is strongly recommended before planting. "
            "The current pH significantly reduces nutrient availability and expected yield."
        )

    if n_comparable > 0:
        parts.append(
            f"{n_comparable} comparable historical field{'s' if n_comparable > 1 else ''} "
            f"from {state} with a similar configuration confirm{'s' if n_comparable == 1 else ''} "
            "this yield range."
        )

    return " ".join(parts)
