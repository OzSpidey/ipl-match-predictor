"""IPL Analytics Dashboard — Plotly Dash
Run: python dashboard.py  →  http://localhost:8050
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────────
DATA_PATH = Path("data/matches.csv")

TEAM_COLORS = {
    "Mumbai Indians":               "#005DA0",
    "Chennai Super Kings":          "#F9CD05",
    "Royal Challengers Bangalore":  "#EC1C24",
    "Royal Challengers Bengaluru":  "#EC1C24",
    "Kolkata Knight Riders":        "#3A225D",
    "Sunrisers Hyderabad":          "#F7A721",
    "Delhi Capitals":               "#0078BC",
    "Delhi Daredevils":             "#0078BC",
    "Punjab Kings":                 "#ED1B24",
    "Kings XI Punjab":              "#ED1B24",
    "Rajasthan Royals":             "#EA1A85",
    "Lucknow Super Giants":         "#A72056",
    "Gujarat Titans":               "#9CA3AF",
    "Rising Pune Supergiants":      "#6F4E37",
    "Rising Pune Supergiant":       "#6F4E37",
    "Gujarat Lions":                "#FF6B00",
    "Pune Warriors":                "#0A2D6E",
    "Kochi Tuskers Kerala":         "#F06522",
    "Deccan Chargers":              "#FFA500",
}

TEAM_SHORT = {
    "Mumbai Indians":               "MI",
    "Chennai Super Kings":          "CSK",
    "Royal Challengers Bangalore":  "RCB",
    "Royal Challengers Bengaluru":  "RCB",
    "Kolkata Knight Riders":        "KKR",
    "Sunrisers Hyderabad":          "SRH",
    "Delhi Capitals":               "DC",
    "Delhi Daredevils":             "DD",
    "Punjab Kings":                 "PBKS",
    "Kings XI Punjab":              "KXIP",
    "Rajasthan Royals":             "RR",
    "Lucknow Super Giants":         "LSG",
    "Gujarat Titans":               "GT",
    "Rising Pune Supergiants":      "RPS",
    "Rising Pune Supergiant":       "RPS",
    "Gujarat Lions":                "GL",
    "Pune Warriors":                "PWI",
    "Kochi Tuskers Kerala":         "KTK",
    "Deccan Chargers":              "DCH",
}

VENUE_COORDS = {
    "Wankhede Stadium":                               (18.938,  72.825),
    "Eden Gardens":                                   (22.565,  88.343),
    "M Chinnaswamy Stadium":                          (12.979,  77.599),
    "MA Chidambaram Stadium":                         (13.064,  80.279),
    "M. A. Chidambaram Stadium":                      (13.064,  80.279),
    "Arun Jaitley Stadium":                           (28.637,  77.237),
    "Feroz Shah Kotla":                               (28.637,  77.237),
    "Rajiv Gandhi International Cricket Stadium":     (17.404,  78.536),
    "Punjab Cricket Association IS Bindra Stadium":   (30.734,  76.816),
    "Punjab Cricket Association Stadium":             (30.734,  76.816),
    "Sawai Mansingh Stadium":                         (26.904,  75.813),
    "Narendra Modi Stadium":                          (23.090,  72.600),
    "Brabourne Stadium":                              (18.933,  72.824),
    "DY Patil Stadium":                               (19.064,  73.001),
    "Dr DY Patil Sports Academy":                     (19.064,  73.001),
    "Maharashtra Cricket Association Stadium":        (18.647,  73.804),
    "Subrata Roy Sahara Stadium":                     (18.519,  73.863),
    "Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium": (17.730, 83.319),
    "Holkar Cricket Stadium":                         (22.720,  75.857),
    "JSCA International Stadium Complex":             (23.344,  85.310),
    "Barsapara Cricket Stadium":                      (26.196,  91.680),
    "Himachal Pradesh Cricket Association Stadium":   (31.634,  76.819),
    "Green Park":                                     (26.424,  80.348),
}

BG       = "#0a0a1a"
CARD_BG  = "rgba(18,18,42,0.95)"
BORDER   = "rgba(255,255,255,0.08)"
TEXT     = "#e2e2f0"
MUTED    = "#6b7280"
ACCENT   = "#7c3aed"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT, family="Inter, system-ui, sans-serif"),
    margin=dict(l=50, r=30, t=44, b=40),
)


# ── Data ───────────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    NAME_MAP = {
        "Royal Challengers Bengaluru": "Royal Challengers Bangalore",
        "Delhi Daredevils":            "Delhi Capitals",
        "Kings XI Punjab":             "Punjab Kings",
        "Rising Pune Supergiant":      "Rising Pune Supergiants",
    }
    for col in ("team1", "team2", "winner", "toss_winner"):
        df[col] = df[col].replace(NAME_MAP)
    df["season"] = df["season"].astype(int)
    return df.dropna(subset=["winner"])


DF      = load_data()
SEASONS = sorted(DF["season"].unique())

MATCH_COUNTS = {
    t: ((DF["team1"] == t) | (DF["team2"] == t)).sum()
    for t in set(DF["team1"]) | set(DF["team2"])
}
MAIN_TEAMS = sorted(
    [t for t, c in MATCH_COUNTS.items() if c >= 20],
    key=lambda t: -MATCH_COUNTS[t],
)
ALL_TEAMS = sorted(MATCH_COUNTS.keys())


# ── UI helpers ─────────────────────────────────────────────────────────────────
def tc(name: str) -> str:
    return TEAM_COLORS.get(name, ACCENT)


def card(children, extra_style=None):
    s = {
        "background": CARD_BG,
        "border": f"1px solid {BORDER}",
        "borderRadius": "16px",
        "padding": "20px",
    }
    if extra_style:
        s.update(extra_style)
    return html.Div(children, style=s)


def kpi(label, value, color=ACCENT):
    return html.Div([
        html.Div(value, style={"fontSize": "2rem", "fontWeight": "800",
                               "color": color, "lineHeight": "1.1"}),
        html.Div(label, style={"fontSize": "0.72rem", "color": MUTED,
                               "marginTop": "4px", "textTransform": "uppercase",
                               "letterSpacing": "0.05em"}),
    ], style={
        "background": CARD_BG, "border": f"1px solid {BORDER}",
        "borderRadius": "12px", "padding": "16px 20px",
        "textAlign": "center", "flex": "1", "minWidth": "130px",
    })


def dropdown(id_, options, value, multi=False):
    return dcc.Dropdown(
        id=id_, options=options, value=value,
        multi=multi, clearable=False,
        className="ipl-dropdown",
        style={"marginBottom": "4px"},
    )


# ── Chart builders ─────────────────────────────────────────────────────────────

def fig_win_rate_bar():
    rows = []
    for t in MAIN_TEAMS:
        p = MATCH_COUNTS[t]
        w = (DF["winner"] == t).sum()
        rows.append({"team": t, "short": TEAM_SHORT.get(t, t[:6]),
                     "wr": w / p, "wins": w, "played": p})
    df_r = pd.DataFrame(rows).sort_values("wr")
    fig = go.Figure(go.Bar(
        x=df_r["wr"], y=df_r["short"], orientation="h",
        marker_color=[tc(t) for t in df_r["team"]],
        text=[f"{v:.0%}" for v in df_r["wr"]], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Win rate: %{x:.1%}<br>Won %{customdata[0]}/%{customdata[1]}<extra></extra>",
        customdata=list(zip(df_r["wins"], df_r["played"])),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=440,
        xaxis=dict(showgrid=False, showticklabels=False, range=[0, 0.9]),
        yaxis=dict(showgrid=False),
        title=dict(text="Overall Win Rate by Team", x=0.5),
    )
    return fig


def fig_matches_per_season():
    grp = DF.groupby("season").size().reset_index(name="matches")
    fig = go.Figure(go.Bar(
        x=grp["season"], y=grp["matches"],
        marker_color=ACCENT,
        text=grp["matches"], textposition="outside",
        hovertemplate="<b>%{x}</b>: %{y} matches<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=280,
        bargap=0.3,
        xaxis=dict(dtick=1, tickangle=-45, showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        title=dict(text="Matches per Season", x=0.5),
    )
    return fig


def fig_season_race():
    cum = {t: 0 for t in MAIN_TEAMS}
    rows = []
    for s in SEASONS:
        s_df = DF[DF["season"] == s]
        for t in MAIN_TEAMS:
            cum[t] += (s_df["winner"] == t).sum()
        for t in MAIN_TEAMS:
            if cum[t] > 0:
                rows.append({"season": str(s), "team": t,
                             "short": TEAM_SHORT.get(t, t[:6]),
                             "cumulative_wins": cum[t]})

    df_r = (pd.DataFrame(rows)
              .sort_values(["season", "cumulative_wins"], ascending=[True, False]))

    active = [t for t in MAIN_TEAMS if cum[t] > 0]
    fig = px.bar(
        df_r, x="short", y="cumulative_wins", color="team",
        animation_frame="season",
        color_discrete_map={t: tc(t) for t in active},
        labels={"cumulative_wins": "Cumulative Wins", "short": ""},
        range_y=[0, df_r["cumulative_wins"].max() + 8],
    )
    fig.update_layout(
        **PLOTLY_LAYOUT, height=440, showlegend=False,
        title=dict(text="Cumulative Wins Race — press ▶ Play", x=0.5),
        xaxis=dict(showgrid=False, categoryorder="total descending"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        updatemenus=[{
            "type": "buttons", "showactive": False,
            "x": 0.5, "y": -0.14, "xanchor": "center",
            "bgcolor": "#1a1a38", "bordercolor": BORDER,
            "font": {"color": TEXT},
            "buttons": [
                {"label": "▶  Play",  "method": "animate",
                 "args": [None, {"frame": {"duration": 700, "redraw": True},
                                 "fromcurrent": True}]},
                {"label": "⏸ Pause", "method": "animate",
                 "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                   "mode": "immediate"}]},
            ],
        }],
        sliders=[{
            "active": 0,
            "steps": [{"args": [[s], {"frame": {"duration": 700, "redraw": True},
                                      "mode": "immediate"}],
                        "label": s, "method": "animate"}
                       for s in df_r["season"].unique()],
            "x": 0.05, "len": 0.9, "xanchor": "left",
            "y": -0.04, "yanchor": "top",
            "bgcolor": "#1a1a38", "bordercolor": BORDER,
            "font": {"color": TEXT, "size": 10},
            "currentvalue": {"prefix": "Season: ", "font": {"color": TEXT, "size": 12},
                             "visible": True, "xanchor": "center"},
        }],
    )
    return fig


def fig_season_line(teams=None):
    teams = teams or ["Mumbai Indians", "Chennai Super Kings",
                      "Royal Challengers Bangalore", "Kolkata Knight Riders"]
    rows = []
    for s in SEASONS:
        s_df = DF[DF["season"] == s]
        for t in teams:
            p = ((s_df["team1"] == t) | (s_df["team2"] == t)).sum()
            w = (s_df["winner"] == t).sum()
            if p > 0:
                rows.append({"season": s, "team": TEAM_SHORT.get(t, t[:6]),
                             "full": t, "win_rate": w / p})
    if not rows:
        return go.Figure(layout=PLOTLY_LAYOUT)
    df_r = pd.DataFrame(rows)
    fig = px.line(df_r, x="season", y="win_rate", color="team",
        color_discrete_map={TEAM_SHORT.get(t, t[:6]): tc(t) for t in teams},
        labels={"win_rate": "Win Rate", "season": "Season", "team": ""},
        markers=True,
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=300,
        yaxis=dict(tickformat=".0%", showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        xaxis=dict(dtick=1, tickangle=-45, showgrid=False),
        title=dict(text="Season-by-Season Win Rate", x=0.5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def fig_radar(team: str):
    p = MATCH_COUNTS.get(team, 0)
    w = (DF["winner"] == team).sum()
    win_rate = w / p if p else 0

    recent = DF[(DF["team1"] == team) | (DF["team2"] == team)].tail(20)
    form = (recent["winner"] == team).mean() if len(recent) else 0

    season_rates = []
    for s in SEASONS:
        s_df = DF[DF["season"] == s]
        sp = ((s_df["team1"] == team) | (s_df["team2"] == team)).sum()
        sw = (s_df["winner"] == team).sum()
        if sp >= 5:
            season_rates.append(sw / sp)
    consistency = max(0.0, 1 - float(np.std(season_rates))) if season_rates else 0

    experience = p / max(MATCH_COUNTS.values())

    titles = 0
    for s in SEASONS:
        s_df = DF[DF["season"] == s]
        season_wins = s_df.groupby("winner").size()
        if len(season_wins) and season_wins.get(team, 0) == season_wins.max():
            titles += 1
    title_score = min(titles / 5.0, 1.0)

    dims = ["Win Rate", "Recent Form", "Consistency", "Experience", "Titles"]
    vals = [win_rate, form, consistency, experience, title_score]

    fig = go.Figure(go.Scatterpolar(
        r=vals + [vals[0]],
        theta=dims + [dims[0]],
        fill="toself",
        fillcolor=tc(team) + "33",
        line=dict(color=tc(team), width=2.5),
        hovertemplate="%{theta}: %{r:.2f}<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=340,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 1], showticklabels=False,
                            gridcolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)",
                             tickfont=dict(size=11)),
        ),
        showlegend=False,
        title=dict(text=f"{TEAM_SHORT.get(team, team)} — Performance Profile", x=0.5),
    )
    return fig


def fig_season_wins_losses(team: str):
    rows = []
    for s in SEASONS:
        s_df = DF[DF["season"] == s]
        p = ((s_df["team1"] == team) | (s_df["team2"] == team)).sum()
        w = (s_df["winner"] == team).sum()
        if p > 0:
            rows.append({"season": s, "wins": w, "losses": p - w})
    if not rows:
        return go.Figure(layout=PLOTLY_LAYOUT)
    df_r = pd.DataFrame(rows)
    color = tc(team)
    fig = go.Figure([
        go.Bar(name="Wins",   x=df_r["season"], y=df_r["wins"],
               marker_color=color),
        go.Bar(name="Losses", x=df_r["season"], y=df_r["losses"],
               marker_color="rgba(255,255,255,0.12)"),
    ])
    fig.update_layout(**PLOTLY_LAYOUT, height=280, barmode="stack",
        xaxis=dict(dtick=1, tickangle=-45, showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        title=dict(text="Wins & Losses by Season", x=0.5),
    )
    return fig


def fig_h2h_heatmap():
    teams = [t for t in MAIN_TEAMS if MATCH_COUNTS.get(t, 0) >= 40][:12]
    shorts = [TEAM_SHORT.get(t, t[:5]) for t in teams]
    n = len(teams)
    matrix = np.full((n, n), np.nan)
    annot  = [[""] * n for _ in range(n)]

    for i, t1 in enumerate(teams):
        for j, t2 in enumerate(teams):
            if i == j:
                continue
            mask = (
                ((DF["team1"] == t1) & (DF["team2"] == t2)) |
                ((DF["team1"] == t2) & (DF["team2"] == t1))
            )
            m = DF[mask]
            if len(m) == 0:
                continue
            w1 = (m["winner"] == t1).sum()
            matrix[i][j] = w1 / len(m)
            annot[i][j]  = f"{w1}/{len(m)}"

    fig = go.Figure(go.Heatmap(
        z=matrix, x=shorts, y=shorts,
        colorscale=[[0, "#1a1a3e"], [0.5, "#4c1d95"], [1, "#7c3aed"]],
        zmin=0, zmax=1,
        text=annot, texttemplate="%{text}",
        hovertemplate="<b>%{y}</b> vs <b>%{x}</b><br>Win rate: %{z:.1%} (%{text})<extra></extra>",
        colorbar=dict(tickformat=".0%", title="Win Rate",
                      tickfont=dict(color=TEXT), title_font=dict(color=TEXT)),
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=500,
        xaxis=dict(side="top", showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(showgrid=False, autorange="reversed", tickfont=dict(size=11)),
        title=dict(text="Head-to-Head Win Rate  (row team beats column team)", x=0.5),
    )
    return fig


def fig_h2h_detail(team1: str, team2: str):
    mask = (
        ((DF["team1"] == team1) & (DF["team2"] == team2)) |
        ((DF["team1"] == team2) & (DF["team2"] == team1))
    )
    m = DF[mask]
    if len(m) == 0:
        return go.Figure(layout={**PLOTLY_LAYOUT,
                                  "title": {"text": "No matches found", "x": 0.5}})

    w1 = (m["winner"] == team1).sum()
    w2 = (m["winner"] == team2).sum()
    s1 = TEAM_SHORT.get(team1, team1[:6])
    s2 = TEAM_SHORT.get(team2, team2[:6])

    fig = go.Figure([
        go.Bar(x=[s1], y=[w1], marker_color=tc(team1),
               text=[w1], textposition="outside", name=s1),
        go.Bar(x=[s2], y=[w2], marker_color=tc(team2),
               text=[w2], textposition="outside", name=s2),
    ])
    fig.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False,
        title=dict(text=f"{s1} vs {s2}  —  {len(m)} encounters", x=0.5),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        xaxis=dict(showgrid=False),
    )
    return fig


def fig_h2h_season_bar(team1: str, team2: str):
    mask = (
        ((DF["team1"] == team1) & (DF["team2"] == team2)) |
        ((DF["team1"] == team2) & (DF["team2"] == team1))
    )
    m = DF[mask]
    if len(m) == 0:
        return go.Figure(layout=PLOTLY_LAYOUT)
    s1 = TEAM_SHORT.get(team1, team1[:6])
    s2 = TEAM_SHORT.get(team2, team2[:6])
    rows = []
    for s in sorted(m["season"].unique()):
        ms = m[m["season"] == s]
        rows.append({"season": s,
                     s1: (ms["winner"] == team1).sum(),
                     s2: (ms["winner"] == team2).sum()})
    df_r = pd.DataFrame(rows)
    fig = go.Figure([
        go.Bar(x=df_r["season"], y=df_r[s1], name=s1, marker_color=tc(team1)),
        go.Bar(x=df_r["season"], y=df_r[s2], name=s2, marker_color=tc(team2)),
    ])
    fig.update_layout(**PLOTLY_LAYOUT, height=220, barmode="group",
        title=dict(text="Wins per Season", x=0.5),
        xaxis=dict(dtick=1, tickangle=-45, showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def fig_venue_map():
    rows = []
    for venue, (lat, lon) in VENUE_COORDS.items():
        v_df = DF[DF["venue"] == venue]
        if len(v_df) < 5:
            continue
        bat_first = v_df[
            ((v_df["toss_decision"] == "bat")   & (v_df["toss_winner"] == v_df["winner"])) |
            ((v_df["toss_decision"] == "field") & (v_df["toss_winner"] != v_df["winner"]))
        ].shape[0] / len(v_df)
        rows.append({"venue": venue, "lat": lat, "lon": lon,
                     "matches": len(v_df), "bat_win": bat_first})
    if not rows:
        return go.Figure(layout=PLOTLY_LAYOUT)
    df_v = pd.DataFrame(rows)
    india = df_v[(df_v["lat"] > 6) & (df_v["lat"] < 37) &
                 (df_v["lon"] > 68) & (df_v["lon"] < 98)]

    fig = go.Figure(go.Scattergeo(
        lat=india["lat"], lon=india["lon"],
        mode="markers",
        marker=dict(
            size=india["matches"] / 2.8,
            color=india["bat_win"],
            colorscale=[[0, "#1a3a6e"], [0.5, "#4c1d95"], [1, "#ec1c24"]],
            cmin=0.3, cmax=0.7,
            colorbar=dict(
                title="Bat-First<br>Win %",
                tickformat=".0%",
                tickfont=dict(color=TEXT),
                title_font=dict(color=TEXT),
            ),
            line=dict(color="rgba(255,255,255,0.25)", width=1),
        ),
        text=india["venue"],
        customdata=list(zip(india["matches"], india["bat_win"])),
        hovertemplate="<b>%{text}</b><br>Matches: %{customdata[0]}<br>Bat-first win: %{customdata[1]:.0%}<extra></extra>",
    ))
    fig.update_geos(
        scope="asia",
        center=dict(lat=22, lon=82),
        projection_scale=4.0,
        showland=True,  landcolor="rgba(25,25,55,0.95)",
        showocean=True, oceancolor="rgba(8,8,28,0.95)",
        showcoastlines=True, coastlinecolor="rgba(255,255,255,0.18)",
        showcountries=True, countrycolor="rgba(255,255,255,0.1)",
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(**PLOTLY_LAYOUT, height=520,
        title=dict(text="IPL Venues  —  Bubble = Matches, Colour = Bat-First Win %", x=0.5),
    )
    return fig


def fig_venue_bar():
    rows = []
    for venue in DF["venue"].unique():
        v_df = DF[DF["venue"] == venue]
        if len(v_df) < 10:
            continue
        bat_first = v_df[
            ((v_df["toss_decision"] == "bat")   & (v_df["toss_winner"] == v_df["winner"])) |
            ((v_df["toss_decision"] == "field") & (v_df["toss_winner"] != v_df["winner"]))
        ].shape[0] / len(v_df)
        rows.append({"venue": venue[:32], "bat_win": bat_first, "n": len(v_df)})
    df_v = pd.DataFrame(rows).sort_values("bat_win")
    colors = ["#ec1c24" if v > 0.55 else ("#7c3aed" if v > 0.45 else "#005DA0")
              for v in df_v["bat_win"]]
    fig = go.Figure(go.Bar(
        x=df_v["bat_win"], y=df_v["venue"],
        orientation="h", marker_color=colors,
        text=[f"{v:.0%}" for v in df_v["bat_win"]], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Bat-first: %{x:.1%}<br>n=%{customdata}<extra></extra>",
        customdata=df_v["n"],
    ))
    fig.add_vline(x=0.5, line=dict(color="rgba(255,255,255,0.25)", dash="dash"))
    fig.update_layout(**PLOTLY_LAYOUT, height=520,
        xaxis=dict(showgrid=False, showticklabels=False, range=[0, 0.85]),
        yaxis=dict(showgrid=False),
        title=dict(text="Bat-First Win % by Venue", x=0.5),
        margin=dict(l=270, r=70, t=44, b=40),
    )
    return fig


def fig_toss_win_rate():
    rows = []
    for t in MAIN_TEAMS:
        toss_df = DF[DF["toss_winner"] == t]
        if len(toss_df) < 10:
            continue
        wr = (toss_df["winner"] == t).mean()
        rows.append({"team": TEAM_SHORT.get(t, t[:6]), "full": t, "wr": wr})
    df_r = pd.DataFrame(rows).sort_values("wr")
    fig = go.Figure(go.Bar(
        x=df_r["wr"], y=df_r["team"],
        orientation="h", marker_color=[tc(r["full"]) for _, r in df_r.iterrows()],
        text=[f"{v:.0%}" for v in df_r["wr"]], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Match win after toss: %{x:.1%}<extra></extra>",
    ))
    fig.add_vline(x=0.5, line=dict(color="rgba(255,255,255,0.25)", dash="dash"),
                  annotation_text="50 %", annotation_font=dict(color=MUTED, size=10),
                  annotation_position="top right")
    fig.update_layout(**PLOTLY_LAYOUT, height=400,
        xaxis=dict(showgrid=False, showticklabels=False, range=[0, 0.85]),
        yaxis=dict(showgrid=False),
        title=dict(text="Match Win Rate After Winning Toss", x=0.5),
    )
    return fig


def fig_toss_decision_trend():
    rows = []
    for s in SEASONS:
        s_df = DF[DF["season"] == s]
        if len(s_df) == 0:
            continue
        fp = (s_df["toss_decision"] == "field").mean()
        rows.append({"season": s, "Field First": fp, "Bat First": 1 - fp})
    df_r = pd.DataFrame(rows)
    fig = go.Figure([
        go.Scatter(x=df_r["season"], y=df_r["Bat First"],
                   name="Bat First", mode="lines+markers",
                   line=dict(color="#F9CD05", width=2.5),
                   fill="tozeroy", fillcolor="rgba(249,205,5,0.07)"),
        go.Scatter(x=df_r["season"], y=df_r["Field First"],
                   name="Field First", mode="lines+markers",
                   line=dict(color=ACCENT, width=2.5),
                   fill="tozeroy", fillcolor="rgba(124,58,237,0.07)"),
    ])
    fig.update_layout(**PLOTLY_LAYOUT, height=300,
        xaxis=dict(dtick=1, tickangle=-45, showgrid=False),
        yaxis=dict(tickformat=".0%", range=[0, 1],
                   showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
        title=dict(text="Toss Decision Trend by Season", x=0.5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


# ── Layout ─────────────────────────────────────────────────────────────────────
TAB_STYLE = {
    "padding": "10px 20px", "borderRadius": "8px 8px 0 0",
    "border": "none", "background": "transparent",
    "color": MUTED, "fontWeight": "600", "fontSize": "0.875rem",
}
TAB_SEL = {**TAB_STYLE, "color": TEXT, "background": CARD_BG,
           "borderBottom": f"2px solid {ACCENT}"}


def make_layout():
    tot_m = len(DF)
    tot_s = DF["season"].nunique()
    tot_v = DF["venue"].nunique()
    tot_t = len(ALL_TEAMS)
    top_t = DF["winner"].value_counts().idxmax()
    top_w = DF["winner"].value_counts().max()

    return html.Div([
        # Header
        html.Div([
            html.H1("🏏  IPL Analytics Dashboard",
                    style={"fontSize": "1.8rem", "fontWeight": "900",
                           "margin": "0 0 4px", "color": TEXT,
                           "letterSpacing": "-0.02em"}),
            html.P(
                f"2008 – 2026  ·  {tot_m:,} matches  ·  {tot_s} seasons  ·  CricSheet data",
                style={"margin": 0, "color": MUTED, "fontSize": "0.85rem"},
            ),
        ], style={
            "background": "linear-gradient(135deg,rgba(124,58,237,0.22),rgba(79,142,247,0.10))",
            "borderBottom": f"1px solid {BORDER}",
            "padding": "22px 32px",
        }),

        # Tab bar
        dcc.Tabs(id="tabs", value="overview", children=[
            dcc.Tab(label="📊 Overview",      value="overview", style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label="🏆 Season Race",   value="season",   style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label="📈 Team Analysis", value="team",     style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label="⚔️  Head-to-Head", value="h2h",      style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label="🗺  Venue Map",    value="venue",    style=TAB_STYLE, selected_style=TAB_SEL),
            dcc.Tab(label="🎲 Toss Analysis", value="toss",     style=TAB_STYLE, selected_style=TAB_SEL),
        ], style={
            "background": BG,
            "borderBottom": f"1px solid {BORDER}",
            "padding": "0 32px",
        }),

        html.Div(id="tab-content", style={"padding": "28px 32px", "minHeight": "82vh"}),

        html.Div(
            "IPL Analytics Dashboard  ·  Plotly Dash  ·  1,201 matches  ·  CricSheet",
            style={"textAlign": "center", "color": MUTED, "fontSize": "0.72rem",
                   "padding": "14px", "borderTop": f"1px solid {BORDER}"},
        ),
    ], style={"background": BG, "minHeight": "100vh",
              "fontFamily": "Inter, system-ui, sans-serif", "color": TEXT})


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    title="IPL Analytics Dashboard",
    suppress_callback_exceptions=True,
)
app.layout = make_layout


# ── Callbacks ──────────────────────────────────────────────────────────────────
@app.callback(Output("tab-content", "children"), Input("tabs", "value"))
def render_tab(tab):
    top_t = DF["winner"].value_counts().idxmax()
    top_w = int(DF["winner"].value_counts().max())

    # ── Overview ──────────────────────────────────────────────────────────────
    if tab == "overview":
        return html.Div([
            html.Div([
                kpi("Total Matches",  f"{len(DF):,}",                             "#7c3aed"),
                kpi("IPL Seasons",    str(DF["season"].nunique()),                 "#F7A721"),
                kpi("Teams",          str(len(ALL_TEAMS)),                         "#4F8EF7"),
                kpi("Venues",         str(DF["venue"].nunique()),                  "#00b894"),
                kpi("Most Wins",
                    f"{TEAM_SHORT.get(top_t, top_t[:6])} · {top_w}",             "#F9CD05"),
            ], style={"display": "flex", "gap": "14px", "flexWrap": "wrap", "marginBottom": "22px"}),
            html.Div([
                card([dcc.Graph(figure=fig_win_rate_bar(),
                                config={"displayModeBar": False})],
                     {"flex": "2", "minWidth": "360px"}),
                card([dcc.Graph(figure=fig_matches_per_season(),
                                config={"displayModeBar": False})],
                     {"flex": "1", "minWidth": "300px"}),
            ], style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}),
        ])

    # ── Season Race ───────────────────────────────────────────────────────────
    if tab == "season":
        default_teams = ["Mumbai Indians", "Chennai Super Kings",
                         "Royal Challengers Bangalore", "Kolkata Knight Riders",
                         "Sunrisers Hyderabad"]
        return html.Div([
            card([dcc.Graph(figure=fig_season_race(),
                            config={"displayModeBar": False})],
                 {"marginBottom": "22px"}),
            card([
                html.Label("Compare teams:", style={"color": MUTED, "fontSize": "0.78rem",
                                                    "marginBottom": "8px", "display": "block",
                                                    "textTransform": "uppercase",
                                                    "letterSpacing": "0.05em"}),
                dropdown("season-teams",
                         [{"label": TEAM_SHORT.get(t, t[:6]) + "  —  " + t, "value": t}
                          for t in MAIN_TEAMS],
                         default_teams, multi=True),
                dcc.Graph(id="season-line", config={"displayModeBar": False}),
            ]),
        ])

    # ── Team Analysis ─────────────────────────────────────────────────────────
    if tab == "team":
        return html.Div([
            card([
                html.Label("Select Team:", style={"color": MUTED, "fontSize": "0.78rem",
                                                   "marginBottom": "8px", "display": "block",
                                                   "textTransform": "uppercase",
                                                   "letterSpacing": "0.05em"}),
                dropdown("team-select",
                         [{"label": TEAM_SHORT.get(t, t[:6]) + "  —  " + t, "value": t}
                          for t in MAIN_TEAMS],
                         "Mumbai Indians"),
            ], {"marginBottom": "22px"}),
            html.Div([
                card([dcc.Graph(id="team-radar",  config={"displayModeBar": False})],
                     {"flex": "1", "minWidth": "300px"}),
                card([dcc.Graph(id="team-bars",   config={"displayModeBar": False})],
                     {"flex": "2", "minWidth": "300px"}),
            ], style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}),
        ])

    # ── Head-to-Head ──────────────────────────────────────────────────────────
    if tab == "h2h":
        return html.Div([
            card([dcc.Graph(figure=fig_h2h_heatmap(),
                            config={"displayModeBar": False})],
                 {"marginBottom": "22px"}),
            card([
                html.Div([
                    html.Div([
                        html.Label("Team 1:", style={"color": MUTED, "fontSize": "0.78rem",
                                                     "marginBottom": "6px", "display": "block",
                                                     "textTransform": "uppercase"}),
                        dropdown("h2h-t1",
                                 [{"label": t, "value": t} for t in MAIN_TEAMS],
                                 "Mumbai Indians"),
                    ], style={"flex": "1"}),
                    html.Div([
                        html.Label("Team 2:", style={"color": MUTED, "fontSize": "0.78rem",
                                                     "marginBottom": "6px", "display": "block",
                                                     "textTransform": "uppercase"}),
                        dropdown("h2h-t2",
                                 [{"label": t, "value": t} for t in MAIN_TEAMS],
                                 "Chennai Super Kings"),
                    ], style={"flex": "1"}),
                ], style={"display": "flex", "gap": "20px", "marginBottom": "16px"}),
                html.Div([
                    html.Div([dcc.Graph(id="h2h-bar",
                                        config={"displayModeBar": False})],
                             style={"flex": "1"}),
                    html.Div([dcc.Graph(id="h2h-season",
                                        config={"displayModeBar": False})],
                             style={"flex": "2"}),
                ], style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}),
            ]),
        ])

    # ── Venue Map ─────────────────────────────────────────────────────────────
    if tab == "venue":
        return html.Div([
            html.Div([
                card([dcc.Graph(figure=fig_venue_map(),
                                config={"displayModeBar": False})],
                     {"flex": "1", "minWidth": "340px"}),
                card([dcc.Graph(figure=fig_venue_bar(),
                                config={"displayModeBar": False})],
                     {"flex": "1", "minWidth": "340px"}),
            ], style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}),
        ])

    # ── Toss Analysis ─────────────────────────────────────────────────────────
    if tab == "toss":
        overall = (DF["toss_winner"] == DF["winner"]).mean()
        field_pct = (DF["toss_decision"] == "field").mean()
        return html.Div([
            html.Div([
                kpi("Toss Winner Wins Match", f"{overall:.1%}",   "#7c3aed"),
                kpi("Chose to Field First",   f"{field_pct:.1%}", "#F7A721"),
                kpi("Matches Analysed",        f"{len(DF):,}",    "#4F8EF7"),
            ], style={"display": "flex", "gap": "14px", "flexWrap": "wrap", "marginBottom": "22px"}),
            html.Div([
                card([dcc.Graph(figure=fig_toss_win_rate(),
                                config={"displayModeBar": False})],
                     {"flex": "1", "minWidth": "320px"}),
                card([dcc.Graph(figure=fig_toss_decision_trend(),
                                config={"displayModeBar": False})],
                     {"flex": "1", "minWidth": "320px"}),
            ], style={"display": "flex", "gap": "20px", "flexWrap": "wrap"}),
        ])


@app.callback(Output("season-line", "figure"), Input("season-teams", "value"))
def cb_season_line(teams):
    return fig_season_line(teams or [])


@app.callback(
    [Output("team-radar", "figure"), Output("team-bars", "figure")],
    Input("team-select", "value"),
)
def cb_team(team):
    return fig_radar(team), fig_season_wins_losses(team)


@app.callback(
    [Output("h2h-bar", "figure"), Output("h2h-season", "figure")],
    [Input("h2h-t1", "value"), Input("h2h-t2", "value")],
)
def cb_h2h(t1, t2):
    return fig_h2h_detail(t1, t2), fig_h2h_season_bar(t1, t2)


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🏏  IPL Analytics Dashboard")
    print("    → http://localhost:8050\n")
    app.run(debug=False, port=8050, host="0.0.0.0")
