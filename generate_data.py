"""
IPL Data Generator / Downloader
Tries to download real data from public sources; falls back to realistic synthetic data.
"""

import os
import random
import json
import requests
import pandas as pd
import numpy as np
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ── All teams (current + historical) ─────────────────────────────────────────
# win_rate reflects actual IPL career performance
ALL_TEAMS = {
    # Current franchises
    "MI":   {"name": "Mumbai Indians",            "color": "#004BA0", "secondary": "#FCFCFC", "titles": 5, "win_rate": 0.557, "active": True},
    "CSK":  {"name": "Chennai Super Kings",       "color": "#FFCC00", "secondary": "#0081E9", "titles": 5, "win_rate": 0.580, "active": True},
    "KKR":  {"name": "Kolkata Knight Riders",     "color": "#3A225D", "secondary": "#F2C012", "titles": 3, "win_rate": 0.510, "active": True},
    "RCB":  {"name": "Royal Challengers Bengaluru","color":"#EC1C24", "secondary": "#000000", "titles": 0, "win_rate": 0.468, "active": True},
    "SRH":  {"name": "Sunrisers Hyderabad",       "color": "#FF822A", "secondary": "#FFFFFF", "titles": 2, "win_rate": 0.508, "active": True},
    "DC":   {"name": "Delhi Capitals",            "color": "#17479E", "secondary": "#EF1B23", "titles": 0, "win_rate": 0.485, "active": True},
    "PBKS": {"name": "Punjab Kings",              "color": "#ED1B24", "secondary": "#84231E", "titles": 0, "win_rate": 0.455, "active": True},
    "RR":   {"name": "Rajasthan Royals",          "color": "#EA1A85", "secondary": "#254AA5", "titles": 2, "win_rate": 0.493, "active": True},
    "LSG":  {"name": "Lucknow Super Giants",      "color": "#A72056", "secondary": "#FFFFFF", "titles": 0, "win_rate": 0.518, "active": True},
    "GT":   {"name": "Gujarat Titans",            "color": "#1D2951", "secondary": "#0B4973", "titles": 1, "win_rate": 0.562, "active": True},
    # Historical / defunct franchises
    "RPS":  {"name": "Rising Pune Supergiant",    "color": "#9B0D51", "secondary": "#FFFFFF", "titles": 0, "win_rate": 0.490, "active": False},
    "GL":   {"name": "Gujarat Lions",             "color": "#E77C11", "secondary": "#FFFFFF", "titles": 0, "win_rate": 0.452, "active": False},
    "PWI":  {"name": "Pune Warriors India",       "color": "#1BA9C7", "secondary": "#FFFFFF", "titles": 0, "win_rate": 0.368, "active": False},
    "DC08": {"name": "Deccan Chargers",           "color": "#FFC107", "secondary": "#000000", "titles": 1, "win_rate": 0.422, "active": False},
}

# Only current teams exported to the UI / predictor
TEAMS = {k: v for k, v in ALL_TEAMS.items() if v["active"]}

# ── Venue list ────────────────────────────────────────────────────────────────
VENUES = [
    {"name": "Wankhede Stadium",             "city": "Mumbai",     "home": "MI",   "avg_score": 172, "bat_first_win_pct": 0.48},
    {"name": "M. A. Chidambaram Stadium",    "city": "Chennai",    "home": "CSK",  "avg_score": 161, "bat_first_win_pct": 0.52},
    {"name": "Eden Gardens",                 "city": "Kolkata",    "home": "KKR",  "avg_score": 168, "bat_first_win_pct": 0.47},
    {"name": "M. Chinnaswamy Stadium",       "city": "Bengaluru",  "home": "RCB",  "avg_score": 178, "bat_first_win_pct": 0.45},
    {"name": "Rajiv Gandhi Intl. Stadium",   "city": "Hyderabad",  "home": "SRH",  "avg_score": 162, "bat_first_win_pct": 0.50},
    {"name": "Arun Jaitley Stadium",         "city": "Delhi",      "home": "DC",   "avg_score": 165, "bat_first_win_pct": 0.49},
    {"name": "PCA IS Bindra Stadium",        "city": "Mohali",     "home": "PBKS", "avg_score": 167, "bat_first_win_pct": 0.51},
    {"name": "Sawai Mansingh Stadium",       "city": "Jaipur",     "home": "RR",   "avg_score": 163, "bat_first_win_pct": 0.53},
    {"name": "Narendra Modi Stadium",        "city": "Ahmedabad",  "home": "GT",   "avg_score": 170, "bat_first_win_pct": 0.50},
    {"name": "BRSABV Ekana Stadium",         "city": "Lucknow",    "home": "LSG",  "avg_score": 164, "bat_first_win_pct": 0.51},
    {"name": "Maharashtra Cricket Assoc. Stadium", "city": "Pune", "home": "RPS",  "avg_score": 166, "bat_first_win_pct": 0.49},
    {"name": "Saurashtra Cricket Assoc. Stadium",  "city": "Rajkot","home": "GL",  "avg_score": 165, "bat_first_win_pct": 0.50},
    {"name": "DY Patil Sports Academy",      "city": "Mumbai",     "home": None,   "avg_score": 175, "bat_first_win_pct": 0.46},
    {"name": "Brabourne Stadium",            "city": "Mumbai",     "home": None,   "avg_score": 173, "bat_first_win_pct": 0.47},
    {"name": "Uppal Stadium",                "city": "Hyderabad",  "home": "DC08", "avg_score": 160, "bat_first_win_pct": 0.51},
]

# ── Historically accurate team rosters per season ────────────────────────────
#
# Key facts:
#   2008-2012 : 8 teams (Deccan Chargers instead of SRH; DC was Delhi Daredevils)
#   2011      : 10 teams (added Kochi Tuskers Kerala & Pune Warriors India)
#   2012      : 9 teams  (Kochi Tuskers folded after one season)
#   2013      : 9 teams  (Pune Warriors folded mid-season; treated as 8 below)
#   2013+     : Deccan Chargers replaced by SRH
#   2016-2017 : CSK and RR were BANNED (spot-fixing); replaced by RPS and GL
#   2018      : CSK and RR return; RPS and GL gone
#   2022+     : 10 teams — LSG and GT added
#
SEASON_TEAMS = {
    2008: ["MI", "CSK", "KKR", "RCB", "DC08", "DC",  "PBKS", "RR"],
    2009: ["MI", "CSK", "KKR", "RCB", "DC08", "DC",  "PBKS", "RR"],
    2010: ["MI", "CSK", "KKR", "RCB", "DC08", "DC",  "PBKS", "RR"],
    2011: ["MI", "CSK", "KKR", "RCB", "DC08", "DC",  "PBKS", "RR", "PWI"],
    2012: ["MI", "CSK", "KKR", "RCB", "DC08", "DC",  "PBKS", "RR", "PWI"],
    2013: ["MI", "CSK", "KKR", "RCB", "SRH",  "DC",  "PBKS", "RR"],
    2014: ["MI", "CSK", "KKR", "RCB", "SRH",  "DC",  "PBKS", "RR"],
    2015: ["MI", "CSK", "KKR", "RCB", "SRH",  "DC",  "PBKS", "RR"],
    # CSK & RR banned — replaced by RPS and GL
    2016: ["MI", "RPS", "KKR", "RCB", "SRH",  "DC",  "PBKS", "GL"],
    2017: ["MI", "RPS", "KKR", "RCB", "SRH",  "DC",  "PBKS", "GL"],
    # CSK & RR return
    2018: ["MI", "CSK", "KKR", "RCB", "SRH",  "DC",  "PBKS", "RR"],
    2019: ["MI", "CSK", "KKR", "RCB", "SRH",  "DC",  "PBKS", "RR"],
    2020: ["MI", "CSK", "KKR", "RCB", "SRH",  "DC",  "PBKS", "RR"],
    2021: ["MI", "CSK", "KKR", "RCB", "SRH",  "DC",  "PBKS", "RR"],
    # LSG & GT join
    2022: ["MI", "CSK", "KKR", "RCB", "SRH",  "DC",  "PBKS", "RR", "LSG", "GT"],
    2023: ["MI", "CSK", "KKR", "RCB", "SRH",  "DC",  "PBKS", "RR", "LSG", "GT"],
    2024: ["MI", "CSK", "KKR", "RCB", "SRH",  "DC",  "PBKS", "RR", "LSG", "GT"],
    2025: ["MI", "CSK", "KKR", "RCB", "SRH",  "DC",  "PBKS", "RR", "LSG", "GT"],
    2026: ["MI", "CSK", "KKR", "RCB", "SRH",  "DC",  "PBKS", "RR", "LSG", "GT"],
}


def _team_matchup_probability(team1: str, team2: str, venue: dict) -> float:
    """Compute P(team1 wins) based on base rates, home advantage, and venue."""
    r1 = ALL_TEAMS[team1]["win_rate"]
    r2 = ALL_TEAMS[team2]["win_rate"]
    prob = r1 / (r1 + r2)

    if venue["home"] == team1:
        prob = min(0.80, prob + 0.12)
    elif venue["home"] == team2:
        prob = max(0.20, prob - 0.12)

    return prob


def _make_season_matches(season: int) -> list[dict]:
    teams = SEASON_TEAMS[season]
    season_venues = [v for v in VENUES if v["home"] in teams or v["home"] is None]
    matches = []

    # Round-robin: each pair plays twice
    pairs = [(a, b) for i, a in enumerate(teams) for b in teams[i + 1:]]
    random.shuffle(pairs)

    start_date = date(season, 3, 22)
    match_date = start_date

    for pair in pairs:
        for swap in range(2):
            team1, team2 = (pair[0], pair[1]) if swap == 0 else (pair[1], pair[0])
            venue = random.choice(season_venues)
            toss_winner = random.choice([team1, team2])
            bat_first_win_pct = venue["bat_first_win_pct"]
            toss_decision = "bat" if random.random() < 0.55 else "field"

            win_prob = _team_matchup_probability(team1, team2, venue)
            if toss_winner == team1 and toss_decision == "bat" and bat_first_win_pct > 0.5:
                win_prob = min(0.80, win_prob + 0.03)
            elif toss_winner == team2 and toss_decision == "bat" and bat_first_win_pct > 0.5:
                win_prob = max(0.20, win_prob - 0.03)

            winner = team1 if random.random() < win_prob else team2
            win_type = random.choice(["runs", "wickets"])
            win_margin = (
                random.randint(1, 78) if win_type == "runs"
                else random.randint(1, 10)
            )

            matches.append({
                "id":           len(matches) + 1,
                "season":       season,
                "date":         match_date.isoformat(),
                "team1":        team1,
                "team2":        team2,
                "venue":        venue["name"],
                "city":         venue["city"],
                "toss_winner":  toss_winner,
                "toss_decision": toss_decision,
                "winner":       winner,
                "win_type":     win_type,
                "win_margin":   win_margin,
            })
            match_date += timedelta(days=random.randint(1, 3))

    # Playoffs (4 extra matches)
    top4 = random.sample(teams, 4)
    for i in range(4):
        t1, t2 = top4[i % 4], top4[(i + 1) % 4]
        if t1 == t2:
            continue
        venue = random.choice(season_venues)
        w = t1 if random.random() < 0.5 else t2
        matches.append({
            "id": len(matches) + 1, "season": season,
            "date": match_date.isoformat(),
            "team1": t1, "team2": t2,
            "venue": venue["name"], "city": venue["city"],
            "toss_winner": random.choice([t1, t2]),
            "toss_decision": random.choice(["bat", "field"]),
            "winner": w, "win_type": random.choice(["runs", "wickets"]),
            "win_margin": random.randint(1, 40),
        })
        match_date += timedelta(days=2)

    return matches


def generate_ipl_data() -> pd.DataFrame:
    random.seed(42)
    np.random.seed(42)

    all_matches = []
    for season in range(2008, 2027):
        all_matches.extend(_make_season_matches(season))

    df = pd.DataFrame(all_matches)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["id"] = range(1, len(df) + 1)
    return df


# ── Full name -> short code mapping (covers all historical names) ─────────────
TEAM_NAME_TO_CODE = {
    "Mumbai Indians":              "MI",
    "Chennai Super Kings":         "CSK",
    "Kolkata Knight Riders":       "KKR",
    "Royal Challengers Bangalore": "RCB",
    "Royal Challengers Bengaluru": "RCB",
    "Sunrisers Hyderabad":         "SRH",
    "Deccan Chargers":             "DC08",
    "Delhi Capitals":              "DC",
    "Delhi Daredevils":            "DC",
    "Kings XI Punjab":             "PBKS",
    "Punjab Kings":                "PBKS",
    "Rajasthan Royals":            "RR",
    "Lucknow Super Giants":        "LSG",
    "Gujarat Titans":              "GT",
    "Rising Pune Supergiant":      "RPS",
    "Rising Pune Supergiants":     "RPS",
    "Gujarat Lions":               "GL",
    "Pune Warriors India":         "PWI",
    "Pune Warriors":               "PWI",
    "Kochi Tuskers Kerala":        "KTK",
}


def _parse_cricsheet_zip(zip_bytes: bytes) -> pd.DataFrame:
    """Parse CricSheet IPL JSON zip into a match-level DataFrame."""
    import zipfile, io as _io

    rows = []
    with zipfile.ZipFile(_io.BytesIO(zip_bytes)) as zf:
        json_files = [f for f in zf.namelist() if f.endswith(".json")]
        print(f"[data]   Found {len(json_files)} JSON files in archive")
        for fname in json_files:
            try:
                data = json.loads(zf.read(fname))
                info = data.get("info", {})

                teams = info.get("teams", [])
                if len(teams) != 2:
                    continue

                outcome = info.get("outcome", {})
                # Skip abandoned or no-result matches
                if "winner" not in outcome:
                    continue

                winner_full  = outcome["winner"]
                by           = outcome.get("by", {})
                win_type     = "runs" if "runs" in by else "wickets" if "wickets" in by else "runs"
                win_margin   = by.get("runs", by.get("wickets", 0))

                toss         = info.get("toss", {})
                toss_winner  = toss.get("winner", teams[0])
                toss_decision= toss.get("decision", "bat")

                dates   = info.get("dates", [])
                date_str= str(dates[0]) if dates else "2008-01-01"

                # Season: CricSheet uses "2008", "2022/23", or "2007/08"
                # For IPL all matches run April-June within one calendar year,
                # so we derive season from the match date (most reliable).
                season = int(str(dates[0])[:4]) if dates else int(str(info.get("season", "2008")).split("/")[0])

                venue = info.get("venue", "Unknown Venue")
                city  = info.get("city",  "Unknown City")

                # Normalize full names to short codes
                t1_full = teams[0]
                t2_full = teams[1]
                t1 = TEAM_NAME_TO_CODE.get(t1_full, t1_full)
                t2 = TEAM_NAME_TO_CODE.get(t2_full, t2_full)
                w  = TEAM_NAME_TO_CODE.get(winner_full, winner_full)
                tw = TEAM_NAME_TO_CODE.get(toss_winner, toss_winner)

                rows.append({
                    "season":       season,
                    "date":         date_str,
                    "team1":        t1,
                    "team2":        t2,
                    "venue":        venue,
                    "city":         city,
                    "toss_winner":  tw,
                    "toss_decision":toss_decision,
                    "winner":       w,
                    "win_type":     win_type,
                    "win_margin":   int(win_margin),
                })
            except Exception:
                continue

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["id"] = range(1, len(df) + 1)
    return df


def download_cricsheet_data() -> pd.DataFrame | None:
    """
    Download all IPL matches from cricsheet.org (free, official ball-by-ball data).
    Returns a match-level DataFrame, or None if the download fails.
    """
    url = "https://cricsheet.org/downloads/ipl_json.zip"
    print(f"[data] Fetching CricSheet IPL data from {url} …")
    try:
        resp = requests.get(url, timeout=90,
                            headers={"User-Agent": "Mozilla/5.0 (compatible; IPL-ML-project)"})
        if resp.status_code != 200:
            print(f"[data]   HTTP {resp.status_code} — falling back to synthetic data")
            return None
        print(f"[data]   Downloaded {len(resp.content) / 1e6:.1f} MB — parsing…")
        df = _parse_cricsheet_zip(resp.content)
        if df.empty:
            print("[data]   Parsed 0 matches — falling back")
            return None
        print(f"[data]   Parsed {len(df)} real matches, seasons {df.season.min()}-{df.season.max()}")
        return df
    except Exception as e:
        print(f"[data]   Download error: {e} — falling back to synthetic data")
        return None


def _top_up_missing_seasons(real_df: pd.DataFrame) -> pd.DataFrame:
    """
    If recent seasons (2025, 2026) are absent from the real data, generate
    synthetic matches for those seasons and append them.
    """
    random.seed(999)
    np.random.seed(999)
    present = set(real_df["season"].unique())
    extra = []
    for yr in [2025, 2026]:
        if yr not in present:
            print(f"[data]   Season {yr} not in real data — generating synthetic")
            extra.extend(_make_season_matches(yr))
    if not extra:
        return real_df
    extra_df = pd.DataFrame(extra)
    extra_df["date"] = pd.to_datetime(extra_df["date"])
    combined = pd.concat([real_df, extra_df], ignore_index=True)
    combined = combined.sort_values("date").reset_index(drop=True)
    combined["id"] = range(1, len(combined) + 1)
    return combined


def main():
    out_path    = DATA_DIR / "matches.csv"
    meta_path   = DATA_DIR / "teams.json"
    venues_path = DATA_DIR / "venues.json"

    if out_path.exists():
        print(f"[data] {out_path} already exists — delete it to re-fetch")
    else:
        df = download_cricsheet_data()
        if df is not None:
            df = _top_up_missing_seasons(df)
            df.to_csv(out_path, index=False)
            seasons = sorted(df.season.unique())
            print(f"[data] Saved {len(df)} matches, seasons: {seasons[0]}-{seasons[-1]} -> {out_path}")
        else:
            print("[data] Generating synthetic IPL data (2008-2026) as fallback…")
            df = generate_ipl_data()
            df.to_csv(out_path, index=False)
            print(f"[data] Generated {len(df)} matches -> {out_path}")

    meta_path.write_text(json.dumps(TEAMS, indent=2))
    venues_path.write_text(json.dumps(VENUES, indent=2))
    print(f"[data] Metadata written to {meta_path} and {venues_path}")


if __name__ == "__main__":
    main()
