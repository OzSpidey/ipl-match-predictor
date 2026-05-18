import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import TeamLogo from "./TeamLogo";
import { postPredict, fetchWhatIf } from "../api/client";

// ── Debounce hook ──────────────────────────────────────────────────────────
function useDebounce(value, delay) {
  const [dv, setDv] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDv(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return dv;
}

// ── Slider config ──────────────────────────────────────────────────────────
const SLIDERS = [
  { key: "team1_form5",      label: "Recent Form (last 5)",  group: "form",    team: 1 },
  { key: "team2_form5",      label: "Recent Form (last 5)",  group: "form",    team: 2 },
  { key: "team1_form10",     label: "Recent Form (last 10)", group: "form",    team: 1 },
  { key: "team2_form10",     label: "Recent Form (last 10)", group: "form",    team: 2 },
  { key: "team1_overall_wr", label: "Overall Win Rate",      group: "winrate", team: 1 },
  { key: "team2_overall_wr", label: "Overall Win Rate",      group: "winrate", team: 2 },
  { key: "h2h_win_rate",     label: "H2H Win Rate (team 1)", group: "h2h",     team: 1 },
  { key: "team1_venue_wr",   label: "Venue Win Rate",        group: "venue",   team: 1 },
  { key: "team2_venue_wr",   label: "Venue Win Rate",        group: "venue",   team: 2 },
];

const GROUPS = {
  form:    "🔥 Recent Form",
  winrate: "📈 Historical Win Rate",
  h2h:     "⚔️  Head-to-Head",
  venue:   "🏟 Venue Strength",
};

// ── Half-circle probability gauge ─────────────────────────────────────────
function ProbGauge({ prob, baseline, color, size = 170, team, meta }) {
  const cx   = size / 2;
  const cy   = Math.round(size * 0.58);
  const r    = Math.round(size * 0.38);
  const sw   = 12;
  const circ = Math.PI * r;   // half-circle arc length

  const clamp = v => Math.max(0.002, Math.min(0.998, v));
  const dash  = v => circ * (1 - clamp(v));

  // Full half-circle path (left → right through top)
  const arc = `M ${cx - r} ${cy} A ${r} ${r} 0 0 0 ${cx + r} ${cy}`;

  // Needle dot position
  const na = Math.PI * (1 - clamp(prob));
  const nx = cx + r * Math.cos(na);
  const ny = cy - r * Math.sin(na);

  return (
    <div className="flex flex-col items-center gap-2">
      <TeamLogo team={team} meta={meta} size={38} glow />
      <svg width={size} height={cy + sw} viewBox={`0 0 ${size} ${cy + sw}`}>
        {/* Track */}
        <path d={arc} fill="none" stroke="#1a1a38" strokeWidth={sw} strokeLinecap="round" />
        {/* Baseline ghost arc */}
        {baseline !== null && (
          <path
            d={arc} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round"
            strokeDasharray={circ} strokeDashoffset={dash(baseline)} opacity={0.2}
          />
        )}
        {/* Live fill arc — CSS transition for smooth animation */}
        <path
          d={arc} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={dash(prob)}
          style={{ transition: "stroke-dashoffset 0.42s cubic-bezier(0.34,1.2,0.64,1)" }}
        />
        {/* Needle dot — animated via transform on <g> */}
        <g style={{
          transform: `translate(${nx}px, ${ny}px)`,
          transition: "transform 0.42s cubic-bezier(0.34,1.2,0.64,1)",
        }}>
          <circle cx={0} cy={0} r={6} fill={color} />
          <circle cx={0} cy={0} r={3} fill="white" opacity={0.8} />
        </g>
        {/* Percentage label */}
        <text
          x={cx} y={cy - 8}
          textAnchor="middle" fill="white"
          fontSize={size * 0.16} fontWeight="800"
          fontFamily="system-ui, -apple-system, sans-serif"
          style={{ userSelect: "none" }}
        >
          {Math.round(prob * 100)}%
        </text>
      </svg>
      <span className="text-xs font-bold -mt-1" style={{ color }}>{team}</span>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────
export default function WhatIf({ teams, venues }) {
  const teamIds = Object.keys(teams);

  const [team1,        setTeam1]        = useState("MI");
  const [team2,        setTeam2]        = useState("CSK");
  const [venue,        setVenue]        = useState(venues[0]?.name ?? "");
  const [tossWinner,   setTossWinner]   = useState("team1");
  const [tossDecision, setTossDecision] = useState("bat");

  const [baseline,    setBaseline]    = useState(null);  // { prob, features }
  const [vals,        setVals]        = useState({});
  const [liveProb,    setLiveProb]    = useState(null);
  const [loadingBase, setLoadingBase] = useState(false);
  const [loadingLive, setLoadingLive] = useState(false);

  const debouncedVals = useDebounce(vals, 200);

  // ── Load baseline ────────────────────────────────────────────
  const loadBaseline = async () => {
    if (team1 === team2) return;
    setLoadingBase(true);
    try {
      const res = await postPredict({
        team1, team2, venue,
        toss_winner:   tossWinner === "team1" ? team1 : team2,
        toss_decision: tossDecision,
      });
      setBaseline({ prob: res.team1_win_probability, features: res.features });
      setVals({ ...res.features });
      setLiveProb(res.team1_win_probability);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingBase(false);
    }
  };

  // ── Re-evaluate on slider or toss change ─────────────────────
  useEffect(() => {
    if (!baseline || !Object.keys(debouncedVals).length) return;
    setLoadingLive(true);
    fetchWhatIf({
      team1, team2,
      ...debouncedVals,
      season_norm:   baseline.features.season_norm,
      toss_winner:   tossWinner === "team1" ? team1 : team2,
      toss_decision: tossDecision,
    })
      .then(r => setLiveProb(r.team1_win_probability))
      .catch(console.error)
      .finally(() => setLoadingLive(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedVals, tossWinner, tossDecision]);

  const t1c = teams[team1]?.color ?? "#7c3aed";
  const t2c = teams[team2]?.color ?? "#ea580c";
  const p1  = liveProb ?? 0.5;
  const p2  = 1 - p1;
  const probDelta    = baseline ? (p1 - baseline.prob) * 100 : 0;
  const winnerFlipped = baseline && (p1 > 0.5) !== (baseline.prob > 0.5);
  const predicted    = p1 > 0.5 ? team1 : team2;
  const pwColor      = predicted === team1 ? t1c : t2c;

  const modified = SLIDERS
    .filter(s => baseline && Math.abs((vals[s.key] ?? 0.5) - (baseline.features[s.key] ?? 0.5)) > 0.005)
    .sort((a, b) =>
      Math.abs((vals[b.key] ?? 0) - (baseline?.features[b.key] ?? 0)) -
      Math.abs((vals[a.key] ?? 0) - (baseline?.features[a.key] ?? 0))
    );

  const selectCls = "bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-violet-500";

  return (
    <div className="space-y-6">

      {/* ── Setup card ──────────────────────────────────────── */}
      <div className="glass p-6">
        <h2 className="text-xl font-black mb-1">⚗️ What-If Simulator</h2>
        <p className="text-sm text-gray-500 mb-5">
          Load a matchup, then drag sliders to see how each factor shifts the
          win probability live — "what if MI's form dropped by 20%?"
        </p>

        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1.5">Team 1</label>
            <select value={team1} onChange={e => { setTeam1(e.target.value); setBaseline(null); }} className={selectCls}>
              {teamIds.map(t => <option key={t} value={t} className="bg-[#12122a]">{t}</option>)}
            </select>
          </div>

          <span className="text-gray-600 font-bold self-end pb-2.5">vs</span>

          <div>
            <label className="block text-xs text-gray-500 mb-1.5">Team 2</label>
            <select value={team2} onChange={e => { setTeam2(e.target.value); setBaseline(null); }} className={selectCls}>
              {teamIds.filter(t => t !== team1).map(t => <option key={t} value={t} className="bg-[#12122a]">{t}</option>)}
            </select>
          </div>

          <div className="flex-1 min-w-[180px]">
            <label className="block text-xs text-gray-500 mb-1.5">Venue</label>
            <select value={venue} onChange={e => { setVenue(e.target.value); setBaseline(null); }} className={`w-full ${selectCls}`}>
              {venues.map(v => (
                <option key={v.name} value={v.name} className="bg-[#12122a]">
                  {v.name} ({v.city})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1.5">Toss Winner</label>
            <div className="flex gap-1">
              {[["team1", team1, t1c], ["team2", team2, t2c]].map(([side, name, col]) => (
                <button key={side} onClick={() => setTossWinner(side)}
                  className="px-3 py-2 rounded-xl text-xs font-bold border-2 transition-all"
                  style={{ borderColor: col, background: tossWinner === side ? col + "22" : "transparent", color: tossWinner === side ? col : "#6b7280" }}>
                  {name}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1.5">Decision</label>
            <div className="flex gap-1">
              {["bat", "field"].map(d => (
                <button key={d} onClick={() => setTossDecision(d)}
                  className="px-3 py-2 rounded-xl text-xs font-bold capitalize border-2 transition-all"
                  style={{ borderColor: "#7c3aed", background: tossDecision === d ? "#7c3aed22" : "transparent", color: tossDecision === d ? "#a78bfa" : "#6b7280" }}>
                  {d}
                </button>
              ))}
            </div>
          </div>

          <motion.button whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }}
            onClick={loadBaseline} disabled={loadingBase || team1 === team2}
            className="px-6 py-2.5 rounded-xl font-bold text-sm text-white disabled:opacity-40"
            style={{ background: "linear-gradient(135deg, #7c3aed, #4f46e5)" }}>
            {loadingBase ? "Loading…" : baseline ? "↺ Reload" : "Load Baseline"}
          </motion.button>
        </div>
      </div>

      {/* ── Empty state ─────────────────────────────────────── */}
      {!baseline && (
        <div className="glass p-16 text-center">
          <div className="text-7xl mb-5 select-none">⚗️</div>
          <p className="text-gray-300 font-semibold text-lg mb-2">
            Select a matchup and click{" "}
            <span className="text-violet-400 font-bold">Load Baseline</span>
          </p>
          <p className="text-gray-600 text-sm">
            Then drag sliders to ask counterfactuals — see probability shift in real time
          </p>
        </div>
      )}

      {/* ── Simulator ───────────────────────────────────────── */}
      {baseline && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-start">

          {/* ── LEFT: Slider panels ── */}
          <div className="lg:col-span-3 space-y-4">
            {Object.entries(GROUPS).map(([groupKey, groupLabel]) => {
              const items = SLIDERS.filter(s => s.group === groupKey);
              return (
                <div key={groupKey} className="glass p-5">
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-5">
                    {groupLabel}
                  </h3>
                  <div className="space-y-6">
                    {items.map(cfg => {
                      const val   = vals[cfg.key] ?? 0.5;
                      const base  = baseline.features[cfg.key] ?? 0.5;
                      const diff  = val - base;
                      const dirty = Math.abs(diff) > 0.005;
                      const tName = cfg.team === 1 ? team1 : team2;
                      const tCol  = cfg.team === 1 ? t1c   : t2c;
                      const tMeta = cfg.team === 1 ? teams[team1] : teams[team2];

                      return (
                        <div key={cfg.key}>
                          {/* Row header */}
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2 flex-wrap">
                              <TeamLogo team={tName} meta={tMeta} size={16} />
                              <span className="text-sm text-gray-300 font-medium">
                                {tName} — {cfg.label}
                              </span>
                              <AnimatePresence>
                                {dirty && (
                                  <motion.span
                                    initial={{ opacity: 0, scale: 0.6 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.6 }}
                                    className="text-xs px-1.5 py-0.5 rounded font-bold"
                                    style={{
                                      background: diff > 0 ? "#16a34a22" : "#dc262622",
                                      color:      diff > 0 ? "#4ade80"   : "#f87171",
                                    }}>
                                    {diff > 0 ? "+" : ""}{(diff * 100).toFixed(0)}%
                                  </motion.span>
                                )}
                              </AnimatePresence>
                            </div>
                            <div className="flex items-center gap-1.5 shrink-0">
                              <span className="text-sm font-mono font-bold" style={{ color: tCol }}>
                                {(val * 100).toFixed(0)}%
                              </span>
                              {dirty && (
                                <button
                                  onClick={() => setVals(v => ({ ...v, [cfg.key]: base }))}
                                  className="text-gray-600 hover:text-gray-200 text-sm transition-colors"
                                  title="Reset to baseline">
                                  ↩
                                </button>
                              )}
                            </div>
                          </div>

                          {/* Slider track with baseline tick */}
                          <div className="relative flex items-center h-6">
                            {/* Baseline tick */}
                            <div
                              className="absolute w-px h-5 z-10 pointer-events-none rounded-full"
                              style={{ left: `${base * 100}%`, background: tCol, opacity: 0.7 }}
                              title={`Baseline: ${(base * 100).toFixed(0)}%`}
                            />
                            <input
                              type="range" min={0} max={1} step={0.01} value={val}
                              onChange={e => setVals(v => ({ ...v, [cfg.key]: parseFloat(e.target.value) }))}
                              className="ipl-slider w-full"
                              style={{ "--fill": tCol, "--pct": `${val * 100}%` }}
                            />
                          </div>

                          <div className="flex justify-between text-xs text-gray-700 mt-1 px-0.5">
                            <span>0%</span>
                            <span className="text-gray-600 tabular-nums">
                              baseline: {(base * 100).toFixed(0)}%
                            </span>
                            <span>100%</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}

            {/* Live toss toggles */}
            <div className="glass p-5">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">🎲 Toss</h3>
              <div className="flex flex-wrap gap-6">
                <div>
                  <p className="text-xs text-gray-500 mb-2">Winner</p>
                  <div className="flex gap-2">
                    {[["team1", team1, t1c], ["team2", team2, t2c]].map(([side, name, col]) => (
                      <button key={side} onClick={() => setTossWinner(side)}
                        className="flex items-center gap-2 px-3 py-2 rounded-xl border-2 text-sm font-bold transition-all"
                        style={{ borderColor: col, background: tossWinner === side ? col + "22" : "transparent", color: tossWinner === side ? col : "#6b7280" }}>
                        <TeamLogo team={name} meta={teams[name]} size={16} />
                        {name}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-2">Decision</p>
                  <div className="flex gap-2">
                    {["bat", "field"].map(d => (
                      <button key={d} onClick={() => setTossDecision(d)}
                        className="px-4 py-2 rounded-xl border-2 text-sm font-bold capitalize transition-all"
                        style={{ borderColor: "#7c3aed", background: tossDecision === d ? "#7c3aed22" : "transparent", color: tossDecision === d ? "#a78bfa" : "#6b7280" }}>
                        {d}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <button
              onClick={() => setVals({ ...baseline.features })}
              className="w-full py-3 rounded-xl border border-white/10 text-sm text-gray-500 hover:text-white hover:border-white/25 transition-all">
              Reset All Sliders to Baseline
            </button>
          </div>

          {/* ── RIGHT: Live result panel ── */}
          <div className="lg:col-span-2">
            <div className="glass p-6 sticky top-20 space-y-5">

              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">Live Probability</h3>
                {loadingLive && (
                  <div className="w-3.5 h-3.5 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
                )}
              </div>

              {/* Dual gauges */}
              <div className="flex items-start justify-around pt-1">
                <ProbGauge prob={p1} baseline={baseline.prob}      color={t1c} size={155} team={team1} meta={teams[team1]} />
                <div className="self-center text-gray-600 font-bold text-sm mt-8">vs</div>
                <ProbGauge prob={p2} baseline={1 - baseline.prob}  color={t2c} size={155} team={team2} meta={teams[team2]} />
              </div>

              {/* Baseline vs current row */}
              <div className="bg-white/3 rounded-xl p-3 space-y-1.5 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Baseline ({team1})</span>
                  <span className="font-mono text-gray-400">{(baseline.prob * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">What-If</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-white">{(p1 * 100).toFixed(1)}%</span>
                    <AnimatePresence mode="wait">
                      {Math.abs(probDelta) > 0.05 && (
                        <motion.span
                          key={Math.round(probDelta * 10)}
                          initial={{ opacity: 0, y: -3 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0 }}
                          className="text-xs font-bold tabular-nums"
                          style={{ color: probDelta > 0 ? "#4ade80" : "#f87171" }}>
                          {probDelta > 0 ? "+" : ""}{probDelta.toFixed(1)}%
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              </div>

              {/* Animated win-share bar */}
              <div className="rounded-xl overflow-hidden h-3 flex">
                <div
                  className="h-full transition-all duration-500"
                  style={{ width: `${p1 * 100}%`, background: t1c }}
                />
                <div className="h-full flex-1" style={{ background: t2c }} />
              </div>
              <div className="flex justify-between text-xs font-bold -mt-3">
                <span style={{ color: t1c }}>{team1} {(p1 * 100).toFixed(0)}%</span>
                <span style={{ color: t2c }}>{(p2 * 100).toFixed(0)}% {team2}</span>
              </div>

              {/* Winner badge */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={predicted}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="rounded-2xl p-4 text-center"
                  style={{ background: pwColor + "15", border: `1px solid ${pwColor}40` }}>
                  <p className="text-xs text-gray-500 mb-2">Predicted Winner</p>
                  <div className="flex items-center justify-center gap-3">
                    <TeamLogo team={predicted} meta={teams[predicted]} size={38} glow />
                    <span className="text-xl font-black" style={{ color: pwColor }}>{predicted}</span>
                  </div>
                  <AnimatePresence>
                    {winnerFlipped && (
                      <motion.p
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="text-amber-400 text-sm font-bold mt-2">
                        ⚡ Winner flipped from{" "}
                        <span>{predicted === team1 ? team2 : team1}</span>!
                      </motion.p>
                    )}
                  </AnimatePresence>
                </motion.div>
              </AnimatePresence>

              {/* What changed list */}
              <AnimatePresence>
                {modified.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}>
                    <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
                      What Changed
                    </p>
                    <div className="space-y-1.5">
                      {modified.map(cfg => {
                        const d     = (vals[cfg.key] ?? 0.5) - (baseline.features[cfg.key] ?? 0.5);
                        const tName = cfg.team === 1 ? team1 : team2;
                        const tCol  = cfg.team === 1 ? t1c   : t2c;
                        return (
                          <motion.div
                            key={cfg.key}
                            initial={{ opacity: 0, x: 8 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="flex items-center justify-between text-xs">
                            <span className="text-gray-400">
                              <span className="font-bold" style={{ color: tCol }}>{tName}</span>
                              {" "}{cfg.label}
                            </span>
                            <span className="font-mono font-bold" style={{ color: d > 0 ? "#4ade80" : "#f87171" }}>
                              {d > 0 ? "+" : ""}{(d * 100).toFixed(0)}%
                            </span>
                          </motion.div>
                        );
                      })}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
