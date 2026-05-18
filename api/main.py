"""
IPL Predictor — FastAPI Backend
Loads trained models + historical data, computes live features, returns predictions.
"""

import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE    = Path(__file__).parent.parent
MODELS  = BASE / "models"
DATA    = BASE / "data"

app = FastAPI(title="IPL Match Predictor API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load artefacts once at startup ────────────────────────────────────────────
_ensemble   = None
_metadata   = None
_feat_df    = None
_teams_meta = None
_venues_meta= None

def _load():
    global _ensemble, _metadata, _feat_df, _teams_meta, _venues_meta
    _ensemble    = joblib.load(MODELS / "ensemble.pkl")
    _metadata    = json.loads((MODELS / "metadata.json").read_text())
    _feat_df     = pd.read_parquet(MODELS / "features.parquet")
    _teams_meta  = json.loads((DATA   / "teams.json").read_text())
    _venues_meta = json.loads((DATA   / "venues.json").read_text())


@app.on_event("startup")
def startup():
    try:
        _load()
    except Exception as e:
        print(f"[warn] Could not load models: {e}. Run train.py first.")


# ── Feature computation for a live prediction request ────────────────────────

def _compute_live_features(
    team1: str, team2: str, venue: str,
    toss_winner: str, toss_decision: str,
) -> np.ndarray:
    df = _feat_df

    # Use last computed stats per team (last row involving that team)
    def last_stat(team: str, col: str, fallback: float = 0.5) -> float:
        rows = df[(df["team1"] == team) | (df["team2"] == team)]
        if rows.empty:
            return fallback
        row = rows.iloc[-1]
        if row["team1"] == team:
            return float(row[col])
        # Mirror col for team2
        mirror = col.replace("team1", "team2")
        return float(row.get(mirror, fallback))

    t1_owr     = last_stat(team1, "team1_overall_wr")
    t2_owr     = last_stat(team2, "team2_overall_wr")
    t1_f5      = last_stat(team1, "team1_form5")
    t2_f5      = last_stat(team2, "team2_form5")
    t1_f10     = last_stat(team1, "team1_form10")
    t2_f10     = last_stat(team2, "team2_form10")

    # H2H
    h2h_rows = df[
        ((df["team1"] == team1) & (df["team2"] == team2)) |
        ((df["team1"] == team2) & (df["team2"] == team1))
    ]
    if not h2h_rows.empty:
        t1_wins  = (h2h_rows["winner"] == team1).sum()
        h2h_rate = t1_wins / len(h2h_rows)
    else:
        h2h_rate = 0.5

    # Venue win rates
    t1_vwr = _venue_wr(df, team1, venue)
    t2_vwr = _venue_wr(df, team2, venue)

    toss_t1    = int(toss_winner == team1)
    bat_first  = int(toss_decision == "bat")
    t_and_bat  = int(toss_winner == team1 and toss_decision == "bat")
    season_norm = (2026 - 2008) / 18.0   # current season

    feats = np.array([
        t1_owr, t2_owr,
        t1_f5,  t2_f5,
        t1_f10, t2_f10,
        h2h_rate,
        t1_vwr, t2_vwr,
        toss_t1, bat_first, t_and_bat,
        season_norm,
        t1_owr - t2_owr,
        t1_f5  - t2_f5,
        t1_f10 - t2_f10,
        t1_vwr - t2_vwr,
    ], dtype=float).reshape(1, -1)
    return feats


def _venue_wr(df: pd.DataFrame, team: str, venue: str) -> float:
    v_rows = df[
        ((df["team1"] == team) | (df["team2"] == team)) &
        (df["venue"] == venue)
    ]
    if v_rows.empty:
        return 0.5
    wins = (v_rows["winner"] == team).sum()
    return float(wins / len(v_rows))


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": _ensemble is not None}


@app.get("/api/teams")
def get_teams():
    if _teams_meta is None:
        raise HTTPException(503, "Models not loaded")
    return _teams_meta


@app.get("/api/venues")
def get_venues():
    if _venues_meta is None:
        raise HTTPException(503, "Models not loaded")
    return _venues_meta


class PredictRequest(BaseModel):
    team1:          str
    team2:          str
    venue:          str
    toss_winner:    str
    toss_decision:  str   # "bat" | "field"


@app.post("/api/predict")
def predict(req: PredictRequest):
    if _ensemble is None:
        raise HTTPException(503, "Model not loaded — run train.py first")

    feats = _compute_live_features(
        req.team1, req.team2, req.venue,
        req.toss_winner, req.toss_decision,
    )
    prob_team1 = float(_ensemble.predict_proba(feats)[0][1])
    prob_team2 = 1 - prob_team1
    winner     = req.team1 if prob_team1 > 0.5 else req.team2

    confidence = (
        "very high" if max(prob_team1, prob_team2) > 0.72 else
        "high"      if max(prob_team1, prob_team2) > 0.62 else
        "moderate"  if max(prob_team1, prob_team2) > 0.54 else
        "low"
    )

    factors = _explain(req.team1, req.team2, req.toss_winner, req.toss_decision, feats)

    # Expose raw feature values so the What-If simulator can seed its sliders
    feat_vals = {
        "team1_overall_wr": round(float(feats[0][0]), 3),
        "team2_overall_wr": round(float(feats[0][1]), 3),
        "team1_form5":      round(float(feats[0][2]), 3),
        "team2_form5":      round(float(feats[0][3]), 3),
        "team1_form10":     round(float(feats[0][4]), 3),
        "team2_form10":     round(float(feats[0][5]), 3),
        "h2h_win_rate":     round(float(feats[0][6]), 3),
        "team1_venue_wr":   round(float(feats[0][7]), 3),
        "team2_venue_wr":   round(float(feats[0][8]), 3),
        "season_norm":      round(float(feats[0][12]), 3),
    }

    return {
        "team1_win_probability": round(prob_team1, 4),
        "team2_win_probability": round(prob_team2, 4),
        "predicted_winner":      winner,
        "confidence":            confidence,
        "key_factors":           factors,
        "features":              feat_vals,
    }


class WhatIfRequest(BaseModel):
    team1:            str
    team2:            str
    team1_overall_wr: float = 0.5
    team2_overall_wr: float = 0.5
    team1_form5:      float = 0.5
    team2_form5:      float = 0.5
    team1_form10:     float = 0.5
    team2_form10:     float = 0.5
    h2h_win_rate:     float = 0.5
    team1_venue_wr:   float = 0.5
    team2_venue_wr:   float = 0.5
    toss_winner:      str   = ""
    toss_decision:    str   = "bat"
    season_norm:      float = (2026 - 2008) / 18.0


@app.post("/api/what-if")
def what_if(req: WhatIfRequest):
    if _ensemble is None:
        raise HTTPException(503, "Model not loaded")

    toss_t1   = int(req.toss_winner == req.team1)
    bat_first = int(req.toss_decision == "bat")
    t_and_bat = int(req.toss_winner == req.team1 and req.toss_decision == "bat")

    feats = np.array([
        req.team1_overall_wr,  req.team2_overall_wr,
        req.team1_form5,       req.team2_form5,
        req.team1_form10,      req.team2_form10,
        req.h2h_win_rate,
        req.team1_venue_wr,    req.team2_venue_wr,
        toss_t1, bat_first, t_and_bat,
        req.season_norm,
        req.team1_overall_wr - req.team2_overall_wr,
        req.team1_form5      - req.team2_form5,
        req.team1_form10     - req.team2_form10,
        req.team1_venue_wr   - req.team2_venue_wr,
    ], dtype=float).reshape(1, -1)

    prob_t1 = float(_ensemble.predict_proba(feats)[0][1])
    return {
        "team1_win_probability": round(prob_t1, 4),
        "team2_win_probability": round(1 - prob_t1, 4),
        "predicted_winner":      req.team1 if prob_t1 > 0.5 else req.team2,
    }


def _explain(team1, team2, toss_winner, toss_decision, feats) -> list[dict]:
    f = feats[0]
    factors = []

    wr_diff = f[13]
    if abs(wr_diff) > 0.03:
        stronger = team1 if wr_diff > 0 else team2
        factors.append({"label": f"Season win rate advantage", "team": stronger,
                         "delta": abs(wr_diff)})

    form_diff = f[14]
    if abs(form_diff) > 0.05:
        hotter = team1 if form_diff > 0 else team2
        factors.append({"label": "Better recent form (last 5)", "team": hotter,
                         "delta": abs(form_diff)})

    venue_diff = f[16]
    if abs(venue_diff) > 0.04:
        better_venue = team1 if venue_diff > 0 else team2
        factors.append({"label": "Venue advantage", "team": better_venue,
                         "delta": abs(venue_diff)})

    h2h = f[6]
    if h2h > 0.55:
        factors.append({"label": "Head-to-head record", "team": team1, "delta": h2h - 0.5})
    elif h2h < 0.45:
        factors.append({"label": "Head-to-head record", "team": team2, "delta": 0.5 - h2h})

    if toss_winner:
        factors.append({"label": f"Toss won — chose to {toss_decision}",
                         "team": toss_winner, "delta": 0.03})

    factors.sort(key=lambda x: -x["delta"])
    return factors[:4]


@app.get("/api/team-stats/{team}")
def team_stats(team: str):
    if _feat_df is None:
        raise HTTPException(503, "Data not loaded")
    df = _feat_df
    t1_rows = df[df["team1"] == team]
    t2_rows = df[df["team2"] == team]
    all_rows = pd.concat([t1_rows, t2_rows]).sort_values("date")
    if all_rows.empty:
        raise HTTPException(404, f"Team {team} not found")

    wins  = (all_rows["winner"] == team).sum()
    total = len(all_rows)
    win_rate = round(float(wins / total), 3)

    # Season-by-season
    by_season = []
    for season, grp in all_rows.groupby("season"):
        sw = int((grp["winner"] == team).sum())
        sp = int(len(grp))
        by_season.append({"season": int(season), "wins": sw, "played": sp,
                           "win_rate": round(sw / sp, 3)})

    # Last 5 matches
    recent = all_rows.tail(5)[["date", "team1", "team2", "winner", "venue"]].copy()
    recent["date"] = recent["date"].astype(str)
    recent["result"] = recent.apply(
        lambda r: "W" if r["winner"] == team else "L", axis=1
    )
    recent_list = recent[["date", "team1", "team2", "winner", "result", "venue"]].to_dict("records")

    meta = _teams_meta.get(team, {})
    return {
        "team":       team,
        "name":       meta.get("name", team),
        "color":      meta.get("color", "#ccc"),
        "titles":     meta.get("titles", 0),
        "total_played": int(total),
        "total_wins":   int(wins),
        "overall_win_rate": win_rate,
        "by_season":  by_season,
        "recent_matches": recent_list,
    }


@app.get("/api/h2h/{team1}/{team2}")
def h2h(team1: str, team2: str):
    if _feat_df is None:
        raise HTTPException(503, "Data not loaded")
    df = _feat_df
    mask = (
        ((df["team1"] == team1) & (df["team2"] == team2)) |
        ((df["team1"] == team2) & (df["team2"] == team1))
    )
    rows = df[mask].sort_values("date")
    if rows.empty:
        return {"team1": team1, "team2": team2, "total": 0,
                "team1_wins": 0, "team2_wins": 0, "matches": []}

    t1_wins = int((rows["winner"] == team1).sum())
    t2_wins = int((rows["winner"] == team2).sum())

    matches = []
    for _, r in rows.iterrows():
        matches.append({
            "date":    str(r["date"])[:10],
            "venue":   r["venue"],
            "winner":  r["winner"],
            "season":  int(r["season"]),
        })

    # Last 5
    last5 = [(m["winner"]) for m in matches[-5:]]
    return {
        "team1": team1, "team2": team2,
        "total": len(rows),
        "team1_wins": t1_wins,
        "team2_wins": t2_wins,
        "last5": last5,
        "matches": matches,
    }


@app.get("/api/venue-stats/{venue_name:path}")
def venue_stats(venue_name: str):
    if _feat_df is None:
        raise HTTPException(503, "Data not loaded")
    df = _feat_df
    rows = df[df["venue"] == venue_name]
    if rows.empty:
        raise HTTPException(404, "Venue not found")

    total = len(rows)
    bat_first_wins = int(rows[
        ((rows["team1"] == rows["winner"]))
    ].shape[0])  # approximation — team1 is usually batting first in data

    by_team = {}
    for _, r in rows.iterrows():
        for team_col in ["team1", "team2"]:
            t = r[team_col]
            if t not in by_team:
                by_team[t] = {"played": 0, "wins": 0}
            by_team[t]["played"] += 1
            if r["winner"] == t:
                by_team[t]["wins"] += 1

    team_stats_list = sorted(
        [{"team": t, **v, "win_rate": round(v["wins"] / v["played"], 3)}
         for t, v in by_team.items()],
        key=lambda x: -x["win_rate"],
    )

    return {
        "venue": venue_name,
        "total_matches": total,
        "team_stats": team_stats_list,
    }


@app.get("/api/model-metrics")
def model_metrics():
    if _metadata is None:
        raise HTTPException(503, "Metadata not loaded")
    return _metadata


@app.get("/api/recent-matches")
def recent_matches(n: int = 15):
    if _feat_df is None:
        raise HTTPException(503, "Data not loaded")
    df = _feat_df.tail(n).copy()
    df["date"] = df["date"].astype(str)
    return df[["date", "team1", "team2", "venue", "winner", "season"]].to_dict("records")
