"""
Feature engineering with strict temporal isolation — no future leakage.
For every match row, all statistics are computed from matches BEFORE that date.
"""

import numpy as np
import pandas as pd
from pathlib import Path


def _expanding_win_rate(df: pd.DataFrame, team_col: str) -> pd.Series:
    """Per-team expanding win rate up to (but not including) the current match."""
    win_counts: dict = {}
    play_counts: dict = {}
    rates = []
    for _, row in df.iterrows():
        team = row[team_col]
        w = win_counts.get(team, 0)
        p = play_counts.get(team, 0)
        rates.append(w / p if p > 0 else 0.5)
        # Update after reading
        play_counts[team] = p + 1
        if row["winner"] == team:
            win_counts[team] = w + 1
    return pd.Series(rates, index=df.index)


def _rolling_form(df: pd.DataFrame, team_col: str, n: int) -> pd.Series:
    """Win rate over the last N matches per team (before current match)."""
    team_history: dict[str, list[int]] = {}
    rates = []
    for _, row in df.iterrows():
        team = row[team_col]
        hist = team_history.get(team, [])
        window = hist[-n:] if len(hist) >= n else hist
        rates.append(np.mean(window) if window else 0.5)
        team_history.setdefault(team, []).append(1 if row["winner"] == team else 0)
    return pd.Series(rates, index=df.index)


def _h2h_rate(df: pd.DataFrame) -> pd.Series:
    """team1's win rate in all previous head-to-head encounters with team2."""
    h2h_wins: dict[tuple, int] = {}
    h2h_played: dict[tuple, int] = {}
    rates = []
    for _, row in df.iterrows():
        t1, t2 = row["team1"], row["team2"]
        key = tuple(sorted([t1, t2]))
        total = h2h_played.get(key, 0)
        t1_wins = h2h_wins.get((t1, t2), 0)
        rates.append(t1_wins / total if total > 0 else 0.5)
        h2h_played[key] = total + 1
        if row["winner"] == t1:
            h2h_wins[(t1, t2)] = h2h_wins.get((t1, t2), 0) + 1
        else:
            h2h_wins[(t2, t1)] = h2h_wins.get((t2, t1), 0) + 1
    return pd.Series(rates, index=df.index)


def _venue_win_rate(df: pd.DataFrame, team_col: str) -> pd.Series:
    """Win rate per team per venue before the current match."""
    venue_wins: dict[tuple, int] = {}
    venue_played: dict[tuple, int] = {}
    rates = []
    for _, row in df.iterrows():
        team, venue = row[team_col], row["venue"]
        key = (team, venue)
        w = venue_wins.get(key, 0)
        p = venue_played.get(key, 0)
        rates.append(w / p if p > 0 else 0.5)
        venue_played[key] = p + 1
        if row["winner"] == team:
            venue_wins[key] = w + 1
    return pd.Series(rates, index=df.index)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("date").reset_index(drop=True)

    df["team1_overall_wr"]     = _expanding_win_rate(df, "team1")
    df["team2_overall_wr"]     = _expanding_win_rate(df, "team2")
    df["team1_form5"]          = _rolling_form(df, "team1", 5)
    df["team2_form5"]          = _rolling_form(df, "team2", 5)
    df["team1_form10"]         = _rolling_form(df, "team1", 10)
    df["team2_form10"]         = _rolling_form(df, "team2", 10)
    df["h2h_win_rate_team1"]   = _h2h_rate(df)
    df["team1_venue_wr"]       = _venue_win_rate(df, "team1")
    df["team2_venue_wr"]       = _venue_win_rate(df, "team2")

    # Toss features
    df["toss_winner_is_team1"] = (df["toss_winner"] == df["team1"]).astype(int)
    df["bat_first"]            = (df["toss_decision"] == "bat").astype(int)
    df["toss_and_bat_team1"]   = (
        (df["toss_winner"] == df["team1"]) & (df["toss_decision"] == "bat")
    ).astype(int)

    # Season encoding (normalize 2008-2024)
    df["season_norm"] = (df["season"] - 2008) / 18.0

    # Win rate differentials (signed, captures relative strength)
    df["wr_diff"]       = df["team1_overall_wr"]  - df["team2_overall_wr"]
    df["form5_diff"]    = df["team1_form5"]        - df["team2_form5"]
    df["form10_diff"]   = df["team1_form10"]       - df["team2_form10"]
    df["venue_wr_diff"] = df["team1_venue_wr"]     - df["team2_venue_wr"]

    # Target
    df["team1_won"] = (df["winner"] == df["team1"]).astype(int)

    return df


FEATURE_COLS = [
    "team1_overall_wr", "team2_overall_wr",
    "team1_form5",      "team2_form5",
    "team1_form10",     "team2_form10",
    "h2h_win_rate_team1",
    "team1_venue_wr",   "team2_venue_wr",
    "toss_winner_is_team1", "bat_first", "toss_and_bat_team1",
    "season_norm",
    "wr_diff", "form5_diff", "form10_diff", "venue_wr_diff",
]


if __name__ == "__main__":
    df = pd.read_csv(Path("data/matches.csv"), parse_dates=["date"])
    feat_df = build_features(df)
    print(feat_df[FEATURE_COLS + ["team1_won"]].head())
    print(f"\nClass balance: {feat_df['team1_won'].mean():.3f} (should be ~0.50)")
