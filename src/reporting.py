from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _latest_date(daily: pd.DataFrame) -> pd.Timestamp:
    return pd.to_datetime(daily["date"]).max()


def _window_slice(df: pd.DataFrame, end_date: pd.Timestamp, days: int = 14) -> pd.DataFrame:
    end_date = pd.to_datetime(end_date)
    start_date = end_date - pd.Timedelta(days=days - 1)
    out = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()
    return out


def make_player_snapshot_plot(
    daily: pd.DataFrame,
    player_id: str,
    snapshot_date: pd.Timestamp | None = None,
    lookback_days: int = 28,
) -> plt.Figure:
    """
    Produces a coach-friendly snapshot plot:
    - internal_load (daily)
    - internal_load_7d (rolling)
    - readiness_score (z-score)
    """
    d = daily[daily["player_id"] == player_id].copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values("date")

    if snapshot_date is None:
        snapshot_date = _latest_date(d)
    snapshot_date = pd.to_datetime(snapshot_date)

    d = _window_slice(d, snapshot_date, days=lookback_days)

    fig, ax1 = plt.subplots(figsize=(11, 4.5))

    # Left axis: loads
    ax1.plot(d["date"], d["internal_load"], label="internal_load")
    if "internal_load_7d" in d.columns:
        ax1.plot(d["date"], d["internal_load_7d"], label="internal_load_7d")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Load")
    ax1.tick_params(axis="x", rotation=35)

    # Right axis: readiness
    ax2 = ax1.twinx()
    if "readiness_score" in d.columns:
        ax2.plot(d["date"], d["readiness_score"], label="readiness_score")
        ax2.set_ylabel("Readiness (z)")

    # Snapshot vertical line
    ax1.axvline(snapshot_date, linestyle="--")

    # Title
    name = d["player_name"].iloc[0] if "player_name" in d.columns and len(d) else player_id
    fig.suptitle(f"Player Snapshot: {name} ({player_id}) | through {snapshot_date.date()}")

    # Combined legend
    lines = ax1.get_lines() + ax2.get_lines()
    labels = [ln.get_label() for ln in lines]
    ax1.legend(lines, labels, loc="upper left")

    fig.tight_layout()
    return fig


def make_player_snapshot_summary(
    daily: pd.DataFrame,
    player_id: str,
    snapshot_date: pd.Timestamp | None = None,
    lookback_days: int = 7,
) -> str:
    """
    Produces a short, practitioner-readable summary:
    - recent 7d load vs prior 7d
    - readiness today vs recent average
    - flags if present
    """
    d = daily[daily["player_id"] == player_id].copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values("date")

    if snapshot_date is None:
        snapshot_date = _latest_date(d)
    snapshot_date = pd.to_datetime(snapshot_date)

    # Locate snapshot row
    row = d[d["date"] == snapshot_date]
    if row.empty:
        # If exact date not present, use latest prior date
        row = d[d["date"] <= snapshot_date].tail(1)
        if row.empty:
            return f"No data found for player_id={player_id}."
        snapshot_date = row["date"].iloc[0]

    # 7d vs previous 7d (using internal_load)
    last_7 = d[(d["date"] > snapshot_date - pd.Timedelta(days=7)) & (d["date"] <= snapshot_date)]
    prev_7 = d[(d["date"] > snapshot_date - pd.Timedelta(days=14)) & (d["date"] <= snapshot_date - pd.Timedelta(days=7))]

    last7_load = float(last_7["internal_load"].sum()) if not last_7.empty else np.nan
    prev7_load = float(prev_7["internal_load"].sum()) if not prev_7.empty else np.nan

    pct_change = np.nan
    if np.isfinite(last7_load) and np.isfinite(prev7_load) and prev7_load > 0:
        pct_change = (last7_load - prev7_load) / prev7_load

    # Readiness
    readiness_today = row["readiness_score"].iloc[0] if "readiness_score" in row.columns else np.nan
    readiness_7d_avg = float(last_7["readiness_score"].mean()) if ("readiness_score" in d.columns and not last_7.empty) else np.nan

    # Flags
    load_spike = bool(row["flag_load_spike"].iloc[0]) if "flag_load_spike" in row.columns else False
    low_readiness = bool(row["flag_low_readiness"].iloc[0]) if "flag_low_readiness" in row.columns else False

    # Identity
    name = row["player_name"].iloc[0] if "player_name" in row.columns else player_id
    pos = row["position"].iloc[0] if "position" in row.columns else ""
    status = row["status"].iloc[0] if "status" in row.columns else ""

    lines = []
    lines.append(f"Player: {name} ({player_id})  Position: {pos}  Status: {status}")
    lines.append(f"Snapshot date: {snapshot_date.date()}")

    if np.isfinite(last7_load):
        if np.isfinite(pct_change):
            lines.append(f"Last 7 days internal load: {last7_load:.0f}  (change vs prior 7 days: {pct_change*100:.0f}%)")
        else:
            lines.append(f"Last 7 days internal load: {last7_load:.0f}")

    if np.isfinite(readiness_today):
        if np.isfinite(readiness_7d_avg):
            lines.append(f"Readiness (z): today {readiness_today:.2f},  7-day avg {readiness_7d_avg:.2f}")
        else:
            lines.append(f"Readiness (z): today {readiness_today:.2f}")

    alerts = []
    if load_spike:
        alerts.append("load spike")
    if low_readiness:
        alerts.append("low readiness")

    if alerts:
        lines.append("Alerts: " + ", ".join(alerts))
    else:
        lines.append("Alerts: none")

    return "\n".join(lines)


def export_player_snapshot(
    daily: pd.DataFrame,
    player_id: str,
    out_dir: Path,
    snapshot_date: pd.Timestamp | None = None,
    lookback_days: int = 28,
) -> Tuple[Path, Path]:
    """
    Writes:
    - PNG snapshot plot
    - TXT summary
    Returns (png_path, txt_path)
    """
    _ensure_dir(out_dir)
    fig_dir = out_dir / "figures"
    _ensure_dir(fig_dir)

    if snapshot_date is None:
        snapshot_date = _latest_date(daily[daily["player_id"] == player_id])
    snapshot_date = pd.to_datetime(snapshot_date)

    fig = make_player_snapshot_plot(daily, player_id, snapshot_date=snapshot_date, lookback_days=lookback_days)
    summary = make_player_snapshot_summary(daily, player_id, snapshot_date=snapshot_date)

    png_path = fig_dir / f"player_{player_id}_snapshot_{snapshot_date.date()}.png"
    txt_path = out_dir / f"player_{player_id}_summary_{snapshot_date.date()}.txt"

    fig.savefig(png_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    txt_path.write_text(summary, encoding="utf-8")

    return png_path, txt_path

def make_team_daily_table(
    daily: pd.DataFrame,
    snapshot_date: pd.Timestamp,
) -> pd.DataFrame:
    """
    Returns a team daily table (one date) sorted by internal_load_7d descending.
    Includes key columns commonly used by performance staff.
    """
    snapshot_date = pd.to_datetime(snapshot_date)
    d0 = daily.copy()
    d0["date"] = pd.to_datetime(d0["date"])
    d0 = d0[d0["date"] == snapshot_date].copy()

    cols = [
        "date",
        "player_id",
        "player_name",
        "position",
        "status",
        "session_type",
        "minutes",
        "sRPE",
        "internal_load",
        "internal_load_7d",
        "internal_load_28d",
        "readiness_score",
        "flag_load_spike",
        "flag_low_readiness",
    ]
    # Keep only columns that exist (defensive)
    cols = [c for c in cols if c in d0.columns]

    out = d0[cols].sort_values(
        by=("internal_load_7d" if "internal_load_7d" in d0.columns else "internal_load"),
        ascending=False,
    ).reset_index(drop=True)

    return out


def export_team_daily_report(
    daily: pd.DataFrame,
    out_dir: Path,
    snapshot_date: pd.Timestamp,
) -> Path:
    """
    Writes a CSV team report for the snapshot date.
    Returns the path to the CSV.
    """
    _ensure_dir(out_dir)
    snapshot_date = pd.to_datetime(snapshot_date)

    team_table = make_team_daily_table(daily, snapshot_date)
    csv_path = out_dir / f"team_report_{snapshot_date.date()}.csv"
    team_table.to_csv(csv_path, index=False)

    return csv_path

def make_calendar_dim(dates: pd.Series) -> pd.DataFrame:
    """Create a calendar dimension table for PowerBI relationships."""
    d = pd.to_datetime(pd.Series(dates).dropna().unique())
    cal = pd.DataFrame({"date": pd.to_datetime(sorted(d))})
    cal["date_key"] = cal["date"].dt.strftime("%Y%m%d").astype(int)
    cal["year"] = cal["date"].dt.year
    cal["month"] = cal["date"].dt.month
    cal["month_name"] = cal["date"].dt.strftime("%b")
    cal["week"] = cal["date"].dt.isocalendar().week.astype(int)
    cal["day"] = cal["date"].dt.day
    cal["day_name"] = cal["date"].dt.strftime("%a")
    cal["is_weekend"] = cal["date"].dt.weekday >= 5
    return cal


def make_players_dim(players: pd.DataFrame) -> pd.DataFrame:
    """Players dimension table."""
    dim = players.copy()
    # Optional: enforce consistent types
    dim["player_id"] = dim["player_id"].astype(str)
    return dim


def make_daily_fact(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Fact table: one row per player per date, PowerBI-friendly.
    Adds integer date_key for relationships.
    """
    df = daily.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype(int)

    # Ensure IDs are strings
    df["player_id"] = df["player_id"].astype(str)

    # Keep a stable, readable column set
    keep = [
        "date", "date_key", "player_id",
        "session_type", "minutes", "sRPE",
        "external_load", "total_accels", "jump_count", "avg_hr",
        "internal_load", "internal_load_7d", "internal_load_28d",
        "readiness_raw", "readiness_score",
        "load_pct_change", "flag_load_spike", "flag_low_readiness",
        "position", "status", "player_name",
    ]
    keep = [c for c in keep if c in df.columns]
    df = df[keep].sort_values(["player_id", "date"]).reset_index(drop=True)

    # Make booleans explicit (PowerBI handles True/False well)
    for c in ["flag_load_spike", "flag_low_readiness"]:
        if c in df.columns:
            df[c] = df[c].fillna(False).astype(bool)

    return df


def export_powerbi_tables(
    players: pd.DataFrame,
    daily: pd.DataFrame,
    out_dir: Path,
) -> dict:
    """
    Writes:
      outputs/powerbi/dim_players.csv
      outputs/powerbi/dim_calendar.csv
      outputs/powerbi/fact_daily.csv
    Returns dict of paths.
    """
    _ensure_dir(out_dir)
    pb_dir = out_dir / "powerbi"
    _ensure_dir(pb_dir)

    dim_players = make_players_dim(players)
    dim_calendar = make_calendar_dim(daily["date"])
    fact_daily = make_daily_fact(daily)

    p1 = pb_dir / "dim_players.csv"
    p2 = pb_dir / "dim_calendar.csv"
    p3 = pb_dir / "fact_daily.csv"

    dim_players.to_csv(p1, index=False)
    dim_calendar.to_csv(p2, index=False)
    fact_daily.to_csv(p3, index=False)

    return {"dim_players": p1, "dim_calendar": p2, "fact_daily": p3}