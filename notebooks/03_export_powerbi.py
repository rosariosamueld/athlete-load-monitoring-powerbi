from pathlib import Path
import pandas as pd

from src.io import load_data
from src.preprocess import prep_sessions, prep_wellness, validate_ranges
from src.features import compute_rolling_load, compute_readiness_score, merge_daily, add_simple_flags
from src.powerbi_export import export_powerbi


def main():
    PROJECT_ROOT = Path(__file__).resolve().parents[1]

    # Load
    players, sessions, wellness = load_data(PROJECT_ROOT)

    # Preprocess
    sessions_clean = prep_sessions(sessions)
    wellness_clean = prep_wellness(wellness, fill_method="ffill")
    validate_ranges(sessions_clean, wellness_clean)

    # Features
    sessions_feat = compute_rolling_load(sessions_clean, load_col="internal_load", windows=(7, 28))
    wellness_feat = compute_readiness_score(wellness_clean, method="simple", standardize_within_player=True)

    # Merge + flags
    daily = merge_daily(players, sessions_feat, wellness_feat)
    daily = add_simple_flags(daily, load_col="internal_load_7d", readiness_col="readiness_score")

    # Export PowerBI-ready tables
    out_dir = PROJECT_ROOT / "outputs" / "powerbi"
    paths = export_powerbi(players=players, daily=daily, out_dir=out_dir)

    print("Wrote PowerBI tables:")
    for k, v in paths.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
