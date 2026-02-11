from __future__ import annotations

from pathlib import Path
import pandas as pd


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def make_calendar_dim(dates: pd.Series) -> pd.DataFrame:
    d = pd.to_datetime(pd.Series(dates).dropna().unique())
    cal = pd.DataFrame({"date": pd.to_datetime(sorted(d))})
    cal["date_key"] = cal["date"].dt.strftime("%Y%m%d").astype(int)
    cal["year"] = cal["date"].dt.year
    cal["month"] = cal["date"].dt.month
    cal["month_name"] = cal["date"].dt.strftime("%b")
    cal["week"] = cal["date"].dt.isocalendar().week.astype(int)
    cal["day"] = cal["date"].dt.day
    cal["day_name"] = cal["date"].dt.strftime("%a")
    cal["is_weekend"] = (cal["date"].dt.weekday >= 5)
    return cal


def make_players_dim(players: pd.DataFrame) -> pd.DataFrame:
    dim = players.copy()
    dim["player_id"] = dim["player_id"].astype(str)
    return dim


def make_fact_daily(daily: pd.DataFrame) -> pd.DataFrame:
    df = daily.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["player_id"] = df["player_id"].astype(str)

    keep = [
        "date", "date_key", "player_id",
        "player_name", "position", "status",
        "session_type", "minutes", "sRPE",
        "external_load", "total_accels", "jump_count", "avg_hr",
        "internal_load", "internal_load_7d", "internal_load_28d",
        "readiness_raw", "readiness_score",
        "load_pct_change", "flag_load_spike", "flag_low_readiness",
    ]
    keep = [c for c in keep if c in df.columns]
    df = df[keep].sort_values(["player_id", "date"]).reset_index(drop=True)

    # Ensure flags are booleans
    for c in ["flag_load_spike", "flag_low_readiness"]:
        if c in df.columns:
            df[c] = df[c].fillna(False).astype(bool)

    return df


def export_powerbi(players: pd.DataFrame, daily: pd.DataFrame, out_dir: Path) -> dict:
    """
    Writes CSVs:
      out_dir/dim_players.csv
      out_dir/dim_calendar.csv
      out_dir/fact_daily.csv
    """
    ensure_dir(out_dir)

    dim_players = make_players_dim(players)
    dim_calendar = make_calendar_dim(daily["date"])
    fact_daily = make_fact_daily(daily)

    p_players = out_dir / "dim_players.csv"
    p_calendar = out_dir / "dim_calendar.csv"
    p_fact = out_dir / "fact_daily.csv"

    dim_players.to_csv(p_players, index=False)
    dim_calendar.to_csv(p_calendar, index=False)
    fact_daily.to_csv(p_fact, index=False)

    return {"dim_players": p_players, "dim_calendar": p_calendar, "fact_daily": p_fact}