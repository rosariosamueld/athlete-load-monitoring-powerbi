# Athlete Load Monitoring Dashboard (Power BI)

Interactive performance monitoring dashboard built in Power BI to track player internal load and readiness over time. Designed as a portfolio project aligned with team-sport performance analytics workflows.

## What this shows
- Star schema data model:
  - `fact_daily` (daily workload + readiness metrics)
  - `dim_calendar` (date dimension)
  - `dim_players` (player dimension)
- Player-level drill-down with single-select slicer
- Time-series trends for rolling workload (7-day) and readiness
- Controlled slicer interactions to prevent over-filtering of trend visuals

## Tools
- Power BI (data model, relationships, report visuals)
- Python (data preparation + export to Power BI-friendly tables)

## Repo structure
- `outputs/powerbi/` – tables exported for Power BI (CSV)
- `docs/screenshots/` – dashboard and model images
- `src/` and `notebooks/` – data pipeline and walkthrough scripts

## Screenshots
### Model view
![Model](docs/screenshots/model_view.png)

### Player snapshot page
![Player Snapshot](docs/screenshots/player_snapshot.png)

## How to run
1. Create and activate a Python virtual environment
2. Install requirements
3. Run the starter walkthrough (exports CSVs to `outputs/powerbi/`)

```bash
python -m venv .venv
# activate venv (Windows PowerShell)
.\.venv\Scripts\activate
pip install -r requirements.txt
python notebooks/01_starter_walkthrough.py
```

## Notes on data
This repo is intended as a portfolio example using ananomized player identifiers.

---

## Screenshots
This repo includes example screenshots of the Power BI model and report pages in `docs/screenshots/`:
- `model_view.png` (data model + relationships)
- `player_snapshot.png` (load and readiness trends)

## Reproducibility (optional)
If you want to regenerate the Power BI-ready tables from the Python pipeline, install dependencies:

- `requirements.txt`:
  - pandas
  - numpy
  - matplotlib

  ---

  Created By:

  Samuel Rosario, PhD