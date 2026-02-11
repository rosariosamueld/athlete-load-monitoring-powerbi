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

## How to run (optional)
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

## Screenshot checklist (these are what recruiters actually understand)
Put these two images into `docs/screenshots/`:

1) **Model view** screenshot (show the relationships)
2) **Player Snapshot page** screenshot (load + readiness trends)

In Power BI:
- View → Model → screenshot
- Report view → Player Snapshot → screenshot

Name them exactly:
- `model_view.png`
- `player_snapshot.png`

---

## Requirements file (optional but nice)
If you have Python scripts, add `requirements.txt`:

```txt
pandas
numpy
matplotlib