"""
Implements the additive payoff formula:
  Payoff = D1_base + C1_adj + D2_adj + C2_adj

Returns None for any adjustment whose class is unknown (input not provided).
The total payoff is computed over available components only.
"""

from typing import Optional
import config


def compute_payoff(
    d1: str,
    c1: Optional[str],
    d2: Optional[str],
    c2: Optional[str],
) -> dict:
    d1_base = config.PLANTING_WINDOW[d1]["base_sc_ha"]
    c1_adj  = config.C1_ADJ.get(c1) if c1 else None
    d2_adj  = config.D2_ADJ.get(d2) if d2 else None
    c2_adj  = config.C2_ADJ.get(c2) if c2 else None

    total = float(d1_base)
    if c1_adj is not None:
        total += c1_adj
    if d2_adj is not None:
        total += d2_adj
    if c2_adj is not None:
        total += c2_adj

    return {
        "payoff_sc_ha": round(total, 2),
        "components": {
            "D1_base": d1_base,
            "C1_adj":  c1_adj,
            "D2_adj":  d2_adj,
            "C2_adj":  c2_adj,
        },
    }
