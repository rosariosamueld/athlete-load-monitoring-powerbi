from pathlib import Path
import pandas as pd

from src.io import load_data
from src.preprocess import prep_sessions, prep_wellness, validate_ranges
from src.features import compute_rolling_load, compute_readiness_score, merge_daily, add_simple_flags
from src.reporting import (
    export_player_snapshot,
    export_team_daily_report,
    export_powerbi_tables,
)


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
    daily["date"] = pd.to_datetime(daily["date"])

    # Snapshot date
    snapshot_date = daily["date"].max()
    d0 = daily[daily["date"] == snapshot_date].copy()

    out_dir = PROJECT_ROOT / "outputs"

    print("\n=== DAILY STANDUP ===")
    print(f"Snapshot date: {snapshot_date.date()}")
    print(f"Rows for date: {len(d0)}")

    # Top 5 by 7d load
    top_load = (
        d0.sort_values("internal_load_7d", ascending=False)
        .loc[:, ["player_id", "player_name", "internal_load_7d", "internal_load", "session_type", "minutes", "sRPE"]]
        .head(5)
    )
    print("\nTop 5 by 7-day internal load:")
    print(top_load.to_string(index=False))

    # Bottom 5 by readiness
    low_ready = (
        d0.sort_values("readiness_score", ascending=True)
        .loc[:, ["player_id", "player_name", "readiness_score", "internal_load_7d", "session_type"]]
        .head(5)
    )
    print("\nBottom 5 by readiness (z):")
    print(low_ready.to_string(index=False))

    # Flagged athletes
    flagged = d0[(d0["flag_load_spike"] == True) | (d0["flag_low_readiness"] == True)].copy()
    if len(flagged):
        cols = ["player_id", "player_name", "flag_load_spike", "flag_low_readiness", "internal_load_7d", "readiness_score"]
        print("\nFlagged athletes:")
        print(flagged[cols].sort_values(["flag_low_readiness", "flag_load_spike"], ascending=False).to_string(index=False))
    else:
        print("\nFlagged athletes: none")

    # Export team report CSV (good for email/share)
    team_csv = export_team_daily_report(daily, out_dir=out_dir, snapshot_date=snapshot_date)
    print("\nWrote team report CSV:")
    print(team_csv)

    # Export PowerBI tables
    pb_paths = export_powerbi_tables(players=players, daily=daily, out_dir=out_dir)
    print("\nWrote PowerBI tables:")
    for k, v in pb_paths.items():
        print(f"{k}: {v}")

    # Two player snapshots:
    high_load_pid = d0.sort_values("internal_load_7d", ascending=False)["player_id"].iloc[0]
    low_ready_pid = d0.sort_values("readiness_score", ascending=True)["player_id"].iloc[0]

    print("\nSnapshot players:")
    print(f"High 7d load: {high_load_pid}")
    print(f"Low readiness: {low_ready_pid}")

    pids = [high_load_pid]
    if low_ready_pid != high_load_pid:
        pids.append(low_ready_pid)

    for pid in pids:
        png_path, txt_path = export_player_snapshot(
            daily,
            player_id=pid,
            out_dir=out_dir,
            snapshot_date=snapshot_date,
            lookback_days=28,
        )
        print("\nWrote player snapshot:")
        print(png_path)
        print(txt_path)

    print("\nDone.\n")


if __name__ == "__main__":
    main()
