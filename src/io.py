"""
I/O and validation helpers for the load monitoring portfolio project.

Design goals:
- Keep functions small and testable.
- Fail fast on schema issues.
- Avoid heavy dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple

import pandas as pd


REQUIRED_PLAYERS_COLS = ["player_id", "player_name", "position", "status"]
REQUIRED_SESSIONS_COLS = [
    "date", "player_id", "session_type", "minutes", "sRPE",
    "external_load", "total_accels", "jump_count"
]
REQUIRED_WELLNESS_COLS = [
    "date", "player_id", "sleep_hours", "sleep_quality",
    "soreness", "fatigue", "stress", "mood"
]


class SchemaError(ValueError):
    """Raised when an input DataFrame does not meet minimum schema requirements."""


def load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV with no implicit parsing beyond pandas defaults."""
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)


def validate_schema(df: pd.DataFrame, required_cols: Iterable[str], df_name: str) -> None:
    """Ensure df contains the required columns."""
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise SchemaError(f"{df_name} is missing required columns: {missing}")


def load_data(project_root: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load players, sessions, and wellness data from the project's data/ directory.

    Expected paths:
      data/players.csv
      data/sessions.csv
      data/wellness.csv
    """
    data_dir = project_root / "data"
    players = load_csv(data_dir / "players.csv")
    sessions = load_csv(data_dir / "sessions.csv")
    wellness = load_csv(data_dir / "wellness.csv")

    validate_schema(players, REQUIRED_PLAYERS_COLS, "players")
    validate_schema(sessions, REQUIRED_SESSIONS_COLS, "sessions")
    validate_schema(wellness, REQUIRED_WELLNESS_COLS, "wellness")

    return players, sessions, wellness
