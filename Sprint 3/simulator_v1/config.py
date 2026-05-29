"""
Central configuration — single source of truth for all model parameters.
The frontend must never hardcode any of these values; it fetches them via GET /config.
"""

VALID_STATES = ["MG", "PR", "MS", "GO"]
VALID_CROPS = ["soybeans"]
VALID_SEASON_CODES = ["Summer", "Safrinha", "Winter"]

# Soil texture → C1 class mapping
TEXTURE_CLASS: dict[str, list[str]] = {
    "Favorable": [
        "clay", "very clay", "medium-to-clay", "clay-to-very-clay",
        "argilosa", "muito argilosa", "média-argilosa",
    ],
    "Intermediary": [
        "clay-loam", "loam", "medium", "medium texture", "loam-to-clay-loam",
        "franco-argilosa", "franca", "média", "textura média", "franco-argilo-arenosa",
    ],
    "Challenging": [
        "sandy", "arenosa", "areia",
    ],
}

# D1: planting month → class and base yield (sc/ha)
PLANTING_WINDOW: dict[str, dict] = {
    "Early":  {"months": [9, 10],      "base_sc_ha": 64, "adj_sc_ha":  4},
    "Normal": {"months": [11],         "base_sc_ha": 60, "adj_sc_ha":  0},
    "Late":   {"months": [12, 1, 2, 3],"base_sc_ha": 52, "adj_sc_ha": -8},
}

# D2: seed population thresholds (seeds/ha)
SEED_POP_THRESHOLDS = {
    "low_max":   280_000,
    "ideal_max": 320_000,
}

# Adjustments sc/ha
C1_ADJ: dict[str, int] = {"Favorable": 4, "Intermediary": 0, "Challenging": -6}
D2_ADJ: dict[str, int] = {"Low": -3, "Ideal": 2, "High": -1}
C2_ADJ: dict[str, int] = {"Favorable": 4, "Intermediary": 0, "Challenging": -6}

# pH class boundaries
PH_CLASSES: dict[str, dict] = {
    "Favorable":   {"rule": "5.5 ≤ pH ≤ 6.5",   "adj_sc_ha": 4},
    "Intermediary": {"rule": "5.0 ≤ pH < 5.5",   "adj_sc_ha": 0},
    "Challenging":  {"rule": "< 5.0 or > 6.5",   "adj_sc_ha": -6},
}

# Kg → sack conversion (Brazilian standard for soybeans)
KG_TO_SC = 60.0

# Minimum comparable cases before falling back to stddev-based scenarios
MIN_COMPARABLE_FOR_PERCENTILES = 5

# Number of comparable cases to return
MAX_COMPARABLE_CASES = 5

# Immutable model assumptions exposed in the output
IMMUTABLE_ASSUMPTIONS = [
    "D1 base values from Bayer agronomic slide model: Early=64, Normal=60, Late=52 sc/ha",
    "C1 adjustments: Favorable=+4, Intermediary=0, Challenging=−6 sc/ha",
    "D2 adjustments: Low=−3, Ideal=+2, High=−1 sc/ha (Low ≤280,000; Ideal 280,001–320,000; High >320,000 seeds/ha)",
    "C2 adjustments: Favorable=+4, Intermediary=0, Challenging=−6 sc/ha (Favorable 5.5–6.5; Intermediary 5.0–<5.5; Challenging <5.0 or >6.5)",
    "Yield unit: sc/ha = kg/ha ÷ 60 (Brazilian standard)",
    "Independence assumed between D1, C1, D2, C2 for joint probability",
    "pH average = (soil_ph_min + soil_ph_max) / 2",
]

# Outlier threshold for seed population used during data loading
SEED_POP_OUTLIER_MAX = 2_000_000
