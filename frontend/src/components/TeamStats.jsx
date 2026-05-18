import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from "recharts";
import { fetchTeamStats } from "../api/client";
import TeamLogo from "./TeamLogo";

export default function TeamStats({ teams }) {
  const [selected, setSelected] = useState("MI");
  const [stats,    setStats]    = useState(null);
  const [busy,     setBusy]     = useState(false);

  useEffect(() => {
    if (!selected) return;
    setBusy(true);
    fetchTeamStats(selected).then(setStats).catch(console.error).finally(() => setBusy(false));
  }, [selected]);

  const meta  = teams[selected];
  const color = meta?.color || "#7c3aed";

  const radarData = stats ? [
    { metric: "Win Rate",    value: Math.round((stats.overall_win_rate || 0) * 100) },
    { metric: "Titles",      value: Math.round(((stats.titles || 0) / 5) * 100) },
    { metric: "Experience",  value: Math.round(Math.min((stats.total_played || 0) / 200, 1) * 100) },
    { metric: "Recent Form", value: stats.recent_matches
        ? Math.round((stats.recent_matches.filter(m => m.result === "W").length / Math.max(stats.recent_matches.length, 1)) * 100)
        : 50 },
    { metric: "Consistency", value: stats.by_season
        ? Math.round((stats.by_season.filter(s => s.win_rate >= 0.5).length / Math.max(stats.by_season.length, 1)) * 100)
        : 50 },
  ] : [];

  return (
    <div className="space-y-6">
      {/* Team selector */}
      <div className="glass p-6">
        <h2 className="text-lg font-bold mb-4">📊 Team Analytics</h2>
        <div className="flex flex-wrap gap-3">
          {Object.entries(teams).map(([id, m]) => (
            <motion.button
              key={id}
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setSelected(id)}
              className="flex items-center gap-2 px-3 py-2 rounded-xl border-2 transition-all duration-200"
              style={{
                borderColor: m.color,
                background:  selected === id ? m.color + "22" : "transparent",
                boxShadow:   selected === id ? `0 0 14px ${m.color}44` : "none",
                opacity:     selected === id ? 1 : 0.45,
              }}
            >
              <TeamLogo team={id} meta={m} size={24} />
              <span className="text-xs font-bold" style={{ color: selected === id ? m.color : "#888" }}>
                {id}
              </span>
            </motion.button>
          ))}
        </div>
      </div>

      {busy && (
        <div className="text-center text-gray-500 animate-pulse py-8">Loading team data…</div>
      )}

      {!busy && stats && (
        <>
          {/* Team hero card */}
          <motion.div
            className="glass overflow-hidden"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="h-1.5" style={{ background: `linear-gradient(90deg, ${color}, transparent)` }} />
            <div className="p-6 flex flex-col sm:flex-row items-center sm:items-start gap-6">
              {/* Large logo */}
              <div
                className="w-28 h-28 rounded-3xl flex items-center justify-center shrink-0"
                style={{ background: color + "18", border: `2px solid ${color}44` }}
              >
                <TeamLogo team={selected} meta={meta} size={90} glow />
              </div>

              {/* Team info */}
              <div className="flex-1 text-center sm:text-left">
                <h3 className="text-2xl font-black" style={{ color }}>{meta?.name}</h3>
                <p className="text-gray-500 text-sm mt-0.5">
                  {stats.total_played} matches played • Est. IPL 2008
                </p>

                {/* Trophy count */}
                {stats.titles > 0 && (
                  <div className="flex items-center gap-2 mt-2 justify-center sm:justify-start">
                    {Array.from({ length: stats.titles }).map((_, i) => (
                      <motion.div
                        key={i}
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: i * 0.1, type: "spring" }}
                        className="flex flex-col items-center"
                      >
                        <span className="text-2xl">🏆</span>
                      </motion.div>
                    ))}
                    <span className="text-sm text-amber-400 font-bold ml-1">
                      {stats.titles}× IPL Champions
                    </span>
                  </div>
                )}

                {stats.titles === 0 && (
                  <p className="text-sm text-gray-600 mt-2 italic">Yet to win the IPL title</p>
                )}

                {/* Quick stats */}
                <div className="flex gap-4 mt-4 justify-center sm:justify-start">
                  {[
                    { label: "Win Rate",  value: `${(stats.overall_win_rate * 100).toFixed(1)}%` },
                    { label: "Wins",      value: stats.total_wins },
                    { label: "Played",    value: stats.total_played },
                  ].map(s => (
                    <div key={s.label} className="text-center">
                      <p className="text-xl font-black" style={{ color }}>{s.value}</p>
                      <p className="text-xs text-gray-600">{s.label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>

          {/* Charts row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Season win rate line */}
            <div className="glass p-5">
              <h3 className="text-sm font-semibold text-gray-400 mb-4">Win Rate by Season</h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={stats.by_season}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e1e40" />
                  <XAxis dataKey="season" tick={{ fill: "#6b7280", fontSize: 10 }} />
                  <YAxis
                    tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                    tick={{ fill: "#6b7280", fontSize: 10 }}
                    domain={[0, 1]}
                  />
                  <Tooltip
                    contentStyle={{ background: "#12122a", border: "1px solid #1e1e40", borderRadius: 10 }}
                    formatter={v => [`${(v * 100).toFixed(1)}%`, "Win Rate"]}
                    labelStyle={{ color: "#fff" }}
                  />
                  <Line
                    type="monotone" dataKey="win_rate"
                    stroke={color} strokeWidth={2.5}
                    dot={{ r: 3, fill: color, strokeWidth: 0 }}
                    activeDot={{ r: 6, fill: color, stroke: color + "55", strokeWidth: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Radar */}
            <div className="glass p-5">
              <h3 className="text-sm font-semibold text-gray-400 mb-4">Team Profile</h3>
              <ResponsiveContainer width="100%" height={200}>
                <RadarChart data={radarData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
                  <PolarGrid stroke="#1e1e40" />
                  <PolarAngleAxis dataKey="metric" tick={{ fill: "#9ca3af", fontSize: 10 }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar
                    dataKey="value" stroke={color} fill={color}
                    fillOpacity={0.28} strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recent form */}
          {stats.recent_matches?.length > 0 && (
            <div className="glass p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-gray-400">Recent Form</h3>
                <span className="text-xs text-gray-600">
                  {stats.recent_matches.filter(m => m.result === "W").length}/
                  {stats.recent_matches.length} wins
                </span>
              </div>

              {/* Form dots */}
              <div className="flex gap-2 mb-4">
                {stats.recent_matches.map((m, i) => (
                  <motion.div
                    key={i}
                    initial={{ scale: 0, rotate: -90 }}
                    animate={{ scale: 1, rotate: 0 }}
                    transition={{ delay: i * 0.07, type: "spring" }}
                    className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-black text-white`}
                    style={{
                      background: m.result === "W"
                        ? `linear-gradient(135deg, #16a34a, #22c55e)`
                        : `rgba(239,68,68,0.35)`,
                      boxShadow: m.result === "W" ? "0 0 10px rgba(34,197,94,0.4)" : "none",
                    }}
                  >
                    {m.result}
                  </motion.div>
                ))}
              </div>

              {/* Match list */}
              <div className="space-y-2">
                {stats.recent_matches.map((m, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + i * 0.06 }}
                    className="flex items-center gap-3 text-sm bg-white/3 rounded-xl px-3 py-2.5"
                  >
                    <div
                      className={`w-2 h-8 rounded-full shrink-0`}
                      style={{ background: m.result === "W" ? "#22c55e" : "#ef4444" }}
                    />
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <TeamLogo team={m.team1} meta={teams[m.team1]} size={22} />
                      <span className="text-white font-medium text-xs">{m.team1}</span>
                      <span className="text-gray-600 text-xs">vs</span>
                      <TeamLogo team={m.team2} meta={teams[m.team2]} size={22} />
                      <span className="text-white font-medium text-xs">{m.team2}</span>
                    </div>
                    <span className="text-xs text-gray-500 shrink-0 hidden sm:block">
                      {m.venue?.split(",")[0]?.substring(0, 20)}
                    </span>
                    <span className={`text-xs font-bold shrink-0 ${m.result === "W" ? "text-green-400" : "text-red-400"}`}>
                      {m.result === "W" ? "WON" : "LOST"}
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
