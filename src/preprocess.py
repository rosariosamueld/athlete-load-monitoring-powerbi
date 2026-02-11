"""
Preprocessing steps: type coercion, range checks, and light cleaning.

We keep preprocessing separate from feature engineering so that:
- schema/typing problems are fixed early
- downstream functions can assume consistent dtypes
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd


class RangeError(ValueError):
    """Raised when values fall outside expected ranges."""


def _to_datetime(df: pd.DataFrame, col: str = "date") -> pd.DataFrame:
    out = df.copy()
    out[col] = pd.to_datetime(out[col], errors="coerce")
    if out[col].isna().any():
        bad = out.loc[out[col].isna()]
        raise ValueError(f"Failed to parse some dates in column '{col}'. Example rows:\n{bad.head(5)}")
    return out


def validate_ranges(sessions: pd.DataFrame, wellness: pd.DataFrame) -> None:
    """Basic sanity checks. Adjust as needed."""
    s = sessions
    w = wellness

    if (s["minutes"] < 0).any():
        raise RangeError("sessions.minutes contains negative values.")
    if ((s["sRPE"] < 0) | (s["sRPE"] > 10)).any():
        raise RangeError("sessions.sRPE should be in [0, 10].")
    if (s["external_load"] < 0).any():
        raise RangeError("sessions.external_load contains negative values.")
    for c in ["total_accels", "jump_count"]:
        if (s[c] < 0).any():
            raise RangeError(f"sessions.{c} contains negative values.")

    if ((w["sleep_quality"] < 1) | (w["sleep_quality"] > 5)).any():
        # Allow missing; check only non-missing
        non_missing = w["sleep_quality"].dropna()
        if ((non_missing < 1) | (non_missing > 5)).any():
            raise RangeError("wellness.sleep_quality should be in [1, 5].")
    for c in ["soreness", "fatigue", "stress", "mood"]:
        non_missing = w[c].dropna()
        if ((non_missing < 1) | (non_missing > 10)).any():
            raise RangeError(f"wellness.{c} should be in [1, 10].")
    non_missing_sleep = w["sleep_hours"].dropna()
    if ((non_missing_sleep < 0) | (non_missing_sleep > 24)).any():
        raise RangeError("wellness.sleep_hours should be in [0, 24].")


def prep_sessions(sessions: pd.DataFrame) -> pd.DataFrame:
    """
    Clean sessions:
    - parse date
    - coerce numeric columns
    - compute internal_load = minutes * sRPE
    - sort by player/date
    """
    out = _to_datetime(sessions, "date")

    num_cols = ["minutes", "sRPE", "external_load", "total_accels", "jump_count"]
    for c in num_cols:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out["internal_load"] = out["minutes"] * out["sRPE"]

    out = out.sort_values(["player_id", "date"]).reset_index(drop=True)
    return out


def prep_wellness(wellness: pd.DataFrame, fill_method: str = "ffill") -> pd.DataFrame:
    """
    Clean wellness:
    - parse date
    - coerce numeric columns
    - optionally forward-fill missing entries within player (common in daily wellness tools)
    """
    out = _to_datetime(wellness, "date")

    num_cols = ["sleep_hours", "sleep_quality", "soreness", "fatigue", "stress", "mood"]
    for c in num_cols:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out = out.sort_values(["player_id", "date"]).reset_index(drop=True)
    
    if fill_method == "ffill":
        out[num_cols] = out.groupby("player_id")[num_cols].ffill()
    elif fill_method == "bfill":
        out[num_cols] = out.groupby("player_id")[num_cols].bfill()
    elif fill_method == "none":
        pass
    else:
        raise ValueError("fill_method must be one of: 'ffill', 'bfill', 'none'")

    return out
