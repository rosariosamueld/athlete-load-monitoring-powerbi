"""
Feature engineering: rolling loads, readiness scoring, and daily merge table.
"""

from __future__ import annotations

from typing import Iterable, Sequence, Tuple

import numpy as np
import pandas as pd


def compute_rolling_load(
    sessions: pd.DataFrame,
    load_col: str = "internal_load",
    windows: Sequence[int] = (7, 28),
    min_periods: int = 1,
) -> pd.DataFrame:
    """
    Compute rolling sums of load for each player.

    Produces columns like:
      internal_load_7d, internal_load_28d
    """
    out = sessions.copy()
    out = out.sort_values(["player_id", "date"]).reset_index(drop=True)

    for w in windows:
        colname = f"{load_col}_{w}d"
        out[colname] = (
            out.groupby("player_id")[load_col]
            .rolling(window=w, min_periods=min_periods)
            .sum()
            .reset_index(level=0, drop=True)
        )
    return out


def compute_readiness_score(
    wellness: pd.DataFrame,
    method: str = "simple",
    standardize_within_player: bool = True,
) -> pd.DataFrame:
    """
    Compute a readiness score from wellness entries.

    method='simple':
      readiness_raw = sleep_quality + mood - soreness - fatigue - stress

    If standardize_within_player=True:
      readiness_score is z-scored within each player so "low readiness" is comparable
      across players with different baselines.
    """
    out = wellness.copy()

    if method != "simple":
        raise ValueError("Only method='simple' is implemented in the starter version.")

    out["readiness_raw"] = (
        out["sleep_quality"].astype(float)
        + out["mood"].astype(float)
        - out["soreness"].astype(float)
        - out["fatigue"].astype(float)
        - out["stress"].astype(float)
    )

    if standardize_within_player:
        def zscore(s: pd.Series) -> pd.Series:
            mu = s.mean()
            sd = s.std(ddof=0)
            if sd == 0 or np.isnan(sd):
                return s * 0.0
            return (s - mu) / sd

        out["readiness_score"] = out.groupby("player_id")["readiness_raw"].transform(zscore)
    else:
        out["readiness_score"] = out["readiness_raw"]

    return out


def merge_daily(
    players: pd.DataFrame,
    sessions: pd.DataFrame,
    wellness: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge players + sessions + wellness to a daily table with one row per player-date.

    Assumes sessions and wellness already have datetime 'date' column.
    """
    # Keep key identity columns
    p = players[["player_id", "player_name", "position", "status"]].copy()

    # Merge sessions & wellness on player/date
    daily = pd.merge(
        sessions,
        wellness,
        on=["player_id", "date"],
        how="left",
        validate="one_to_one",
        suffixes=("", "_well")
    )

    # Add player info
    daily = pd.merge(daily, p, on="player_id", how="left", validate="many_to_one")
    daily = daily.sort_values(["player_id", "date"]).reset_index(drop=True)
    return daily


def add_simple_flags(
    daily: pd.DataFrame,
    load_col: str = "internal_load_7d",
    readiness_col: str = "readiness_score",
    load_spike_pct: float = 0.25,
    readiness_z_thresh: float = -1.0,
) -> pd.DataFrame:
    """
    Add a few practical flags:
    - load_spike: day-to-day % change in rolling load exceeds threshold
    - low_readiness: readiness z-score below threshold (default -1 SD)
    """
    out = daily.copy().sort_values(["player_id", "date"]).reset_index(drop=True)

    # Percent change in rolling load within player
    out["load_pct_change"] = out.groupby("player_id")[load_col].pct_change()
    out["flag_load_spike"] = out["load_pct_change"] > load_spike_pct

    # Low readiness threshold
    out["flag_low_readiness"] = out[readiness_col] < readiness_z_thresh

    return out
