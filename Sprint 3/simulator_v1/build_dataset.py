"""
Builds the slim, pre-processed dataset used by the deployed simulator.

The two raw CSVs (planting 105 MB + harvest 9 MB) are joined, filtered to
soybeans, and reduced to only the columns the engine actually consumes. The
result (~20 MB, ~58 MB in RAM vs 240 MB for the full join) is written to
data/simulator_dataset.csv and is what loader.py reads in production.

Run once locally whenever the raw data changes:
    python build_dataset.py
"""

from pathlib import Path
from data import loader

# Columns consumed by engine/classifier.py and engine/scenarios.py
USED_COLUMNS = [
    "state",
    "crop_name",
    "crop_year",
    "field_uuid",
    "planting_month",
    "soil_texture",
    "seed_actual_population_per_hectare",
    "soil_ph_min",
    "soil_ph_max",
    "soil_ph_avg",
    "yield_sc_ha",
]

OUT_PATH = Path(__file__).parent.parent / "data" / "simulator_dataset.csv"


def main() -> None:
    df = loader.load(force_raw=True)  # full join/filter/derive from raw CSVs
    have = [c for c in USED_COLUMNS if c in df.columns]
    missing = set(USED_COLUMNS) - set(have)
    if missing:
        print(f"[warn] columns not found and skipped: {sorted(missing)}")
    slim = df[have].copy()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    slim.to_csv(OUT_PATH, index=False)
    mb = OUT_PATH.stat().st_size / 1e6
    print(f"[ok] wrote {len(slim):,} rows × {len(have)} cols → {OUT_PATH} ({mb:.1f} MB)")


if __name__ == "__main__":
    main()
