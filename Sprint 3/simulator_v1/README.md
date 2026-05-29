# Bayer Yield Simulator — Backend v1

Python/FastAPI backend for the soybean yield decision-tree simulator.  
No database. All model parameters are served via API so the frontend has zero hardcoded agronomic values.

---

## Requirements

- Python 3.11+
- The two source CSVs must be present at:
  - `Sprint 3/data/planting_summary_brazil.csv`
  - `Sprint 2/payoffMatrix/harvest_summary_brazil.csv`

---

## Setup

```bash
# from Sprint 3/simulator_v1/
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
The web simulator (responsive — works on desktop and mobile) is served at the same URL.  
Interactive API docs: `http://localhost:8000/docs`

---

## Dataset

The engine consumes a slim, pre-processed dataset committed at
`Sprint 3/data/simulator_dataset.csv` (~20 MB, ~58 MB in RAM). It is generated
from the two raw CSVs by joining, filtering to soybeans, and keeping only the 11
columns the model uses:

```bash
# from Sprint 3/simulator_v1/ — only needed if the raw data changes
python build_dataset.py
```

At startup `loader.py` reads the slim dataset if present; otherwise it rebuilds
from the raw CSVs. Results are identical either way — the slim file just keeps
the app inside free-tier memory limits.

---

## Deploy to the web (public URL)

The repo ships a Render Blueprint (`render.yaml` at the repo root):

1. Push the repo to GitHub/GitLab.
2. On [render.com](https://render.com) → **New → Blueprint** → connect the repo.
   Render reads `render.yaml` and provisions a free web service automatically.
3. Wait for the build; the app goes live at `https://<service-name>.onrender.com`.

Build/start are pre-configured:
- Build: `pip install -r "Sprint 3/simulator_v1/requirements.txt"`
- Start: `cd "Sprint 3/simulator_v1" && uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`

> Free tier sleeps after ~15 min idle; the first request then takes ~30 s to wake.

**Live URL:** _add your Render URL here after the first deploy._

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check — confirms data is loaded |
| `GET` | `/config` | All model parameters and valid input options for the frontend |
| `POST` | `/simulate` | Runs the simulation and returns scenarios + narrative |

---

## POST /simulate — example

**Request:**
```json
{
  "state": "MG",
  "crop": "soybeans",
  "planting_date": "2024-10-15",
  "season_code": "Summer",
  "soil_texture": "clay",
  "soil_ph_min": 5.8,
  "soil_ph_max": 6.2,
  "seed_population": 300000
}
```

**Response (abbreviated):**
```json
{
  "classification": { "D1": "Early", "C1": "Favorable", "D2": "Ideal", "C2": "Adequate" },
  "decision_tree":  { "payoff_sc_ha": 74, "components": { "D1_base": 64, "C1_adj": 4, "D2_adj": 2, "C2_adj": 4 } },
  "scenarios": {
    "pessimistic": { "yield_sc_ha": 61.4, "percentile": "P25" },
    "most_likely":  { "yield_sc_ha": 74.0, "percentile": "P50 / Expected Value" },
    "optimistic":   { "yield_sc_ha": 80.7, "percentile": "P75" }
  },
  "comparable_cases": [ ... ],
  "narrative": "Based on your early planting window ...",
  "model_assumptions": { "immutable": [...], "auditable": {...} },
  "validation_warnings": []
}
```

---

## Project structure

```
simulator_v1/
├── main.py              # FastAPI app, routes, serves the web frontend
├── build_dataset.py     # Builds the slim dataset from the raw CSVs
├── config.py            # All model parameters (single source of truth)
├── models.py            # Pydantic request/response schemas
├── Simulador/           # Responsive web frontend (index.html)
├── engine/
│   ├── classifier.py    # Maps inputs → D1 / C1 / D2 / C2 classes
│   ├── decision_tree.py # Payoff = D1_base + C1_adj + D2_adj + C2_adj
│   ├── scenarios.py     # P25 / P50 / P75 from historical records
│   └── narrative.py     # Plain-language recommendation text
├── data/
│   └── loader.py        # Loads and joins CSVs once at startup
└── requirements.txt
```

---

## Decision-tree logic

```
Payoff (sc/ha) = D1_base + C1_adj + D2_adj + C2_adj

D1 — Planting Date:   Early (Sep–Oct) = 64 | Normal (Nov) = 60 | Late (Dec–Mar) = 52
C1 — Soil Texture:    Favorable = +4 | Intermediary = 0 | Challenging = −6
D2 — Seed Population: Low (≤280k) = −3 | Ideal (280,001–320,000) = +2 | High (>320k) = −1
C2 — Soil pH:         Favorable (5.5–6.5) = +4 | Intermediary (5.0–<5.5) = 0 | Challenging (<5.0 or >6.5) = −6
```

> Thresholds above are the single source of truth in `config.py` and are served to the
> frontend via `GET /config` — nothing agronomic is hardcoded in the UI.

Scenarios (P25/P50/P75) are derived from historical records in the dataset that match  
the same D1/C1/D2/C2 classes as the user's input. If fewer than 5 matching records exist,  
the fallback uses the decision-tree payoff ± one standard deviation of the D1 group.
