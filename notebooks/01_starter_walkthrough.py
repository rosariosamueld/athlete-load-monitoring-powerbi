# %% [markdown]
# # Fever-style Load Monitoring: Starter Walkthrough
#
# This notebook shows an end-to-end run of the starter pipeline:
# - Load CSVs
# - Preprocess + range checks
# - Compute rolling load + readiness score
# - Merge to a daily table
# - Create a basic plot

# %%
from pathlib import Path

import pandas as pd

from src.io import load_data
from src.preprocess import prep_sessions, prep_wellness, validate_ranges
from src.features import compute_rolling_load, compute_readiness_score, merge_daily, add_simple_flags
from src.visualization import plot_player_timeseries

# %%
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
players, sessions, wellness = load_data(PROJECT_ROOT)

# %%
sessions_clean = prep_sessions(sessions)
wellness_clean = prep_wellness(wellness, fill_method="ffill")

validate_ranges(sessions_clean, wellness_clean)

# %%
sessions_feat = compute_rolling_load(sessions_clean, load_col="internal_load", windows=(7, 28))
wellness_feat = compute_readiness_score(wellness_clean, method="simple", standardize_within_player=True)

daily = merge_daily(players, sessions_feat, wellness_feat)
daily = add_simple_flags(daily, load_col="internal_load_7d", readiness_col="readiness_score")

daily.head()

# %%
# Example: plot one player
player_id = daily["player_id"].iloc[0]
fig = plot_player_timeseries(daily, player_id=player_id, cols=("internal_load", "internal_load_7d", "readiness_score"))
fig # type: ignore