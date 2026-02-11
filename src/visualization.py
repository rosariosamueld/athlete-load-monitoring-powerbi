"""
Visualization helpers.

Note: Keep plots coach-friendly:
- clear labels
- minimal clutter
- consistent units and time axis
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

import matplotlib.pyplot as plt
import pandas as pd


def plot_player_timeseries(
    daily: pd.DataFrame,
    player_id: str,
    cols: Sequence[str] = ("internal_load", "internal_load_7d", "readiness_score"),
    title: Optional[str] = None,
):
    """Line plot of selected metrics for a single player across time."""
    d = daily[daily["player_id"] == player_id].copy()
    d = d.sort_values("date")
    fig, ax = plt.subplots(figsize=(10, 4))
    for c in cols:
        if c in d.columns:
            ax.plot(d["date"], d[c], label=c)
    ax.set_xlabel("Date")
    ax.set_ylabel("Value")
    ax.set_title(title or f"Player {player_id} trend")
    ax.legend(loc="best")
    fig.autofmt_xdate()
    return fig


def plot_team_overview(
    daily: pd.DataFrame,
    snapshot_date: pd.Timestamp,
    metric: str = "internal_load_7d",
    top_n: int = 10,
):
    """Bar chart of a team snapshot on a given date (top N by metric)."""
    d = daily[daily["date"] == snapshot_date].copy()
    d = d.sort_values(metric, ascending=False).head(top_n)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(d["player_id"], d[metric])
    ax.set_xlabel("Player")
    ax.set_ylabel(metric)
    ax.set_title(f"Team overview on {snapshot_date.date()} ({metric})")
    return fig
