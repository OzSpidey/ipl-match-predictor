import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";
import { fetchH2H } from "../api/client";
import TeamLogo from "./TeamLogo";

export default function HeadToHead({ teams }) {
  const [t1,   setT1]   = useState("MI");
  const [t2,   setT2]   = useState("CSK");
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    if (!t1 || !t2 || t1 === t2) return;
    setBusy(true);
    try { setData(await fetchH2H(t1, t2)); }
    finally { setBusy(false); }
  };

  useEffect(() => { load(); }, [t1, t2]);

  const seasonData = data?.matches?.reduce((acc, m) => {
    acc[m.season] = acc[m.season] || { season: String(m.season), [t1]: 0, [t2]: 0 };
    if (m.winner === t1) acc[m.season][t1]++;
    else acc[m.season][t2]++;
    return acc;
  }, {});

  const seasonArr = seasonData
    ? Object.values(seasonData).sort((a, b) => +a.season - +b.season)
    : [];

  const t1w = data?.team1_wins || 0;
  const t2w = data?.team2_wins || 0;
  const total = data?.total || 0;
  const t1pct = total > 0 ? ((t1w / total) * 100).toFixed(0) : 50;
  const t2pct = total > 0 ? ((t2w / total) * 100).toFixed(0) : 50;

  return (
    <div className="space-y-6">
      {/* Team selector */}
      <div className="glass p-6">
        <h2 className="text-lg font-bold mb-5">⚔️ Head-to-Head</h2>
        <div className="grid grid-cols-2 gap-6">
          {["team1", "team2"].map((slot, si) => {
            const val     = si === 0 ? t1 : t2;
            const setVal  = si === 0 ? setT1 : setT2;
            const exclude = si === 0 ? t2 : t1;
            return (
              <div key={slot}>
                <p className="text-xs text-gray-500 uppercase tracking-widest mb-3">
                  {si === 0 ? "Team 1" : "Team 2"}
                </p>
                <div className="grid grid-cols-4 sm:grid-cols-5 gap-2">
                  {Object.entries(teams).map(([id, meta]) => (
                    <motion.div
                      key={id}
                      whileHover={{ scale: 1.08 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => { if (id !== exclude) setVal(id); }}
                      className={`flex flex-col items-center gap-1 p-2 rounded-xl cursor-pointer border-2 transition-all
                        ${id === exclude ? "opacity-20 pointer-events-none" : ""}
                        ${val === id ? "scale-105" : ""}`}
                      style={{
                        borderColor: val === id ? meta.color : "rgba(255,255,255,0.07)",
                        background:  val === id ? meta.color + "18" : "rgba(255,255,255,0.02)",
                        boxShadow:   val === id ? `0 0 16px ${meta.color}44` : "none",
                      }}
                    >
                      <TeamLogo team={id} meta={meta} size={34} glow={val === id} />
                      <span className="text-[9px] font-bold" style={{ color: val === id ? meta.color : "#6b7280" }}>
                        {id}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {busy && (
        <div className="text-center text-gray-500 animate-pulse py-8">Loading H2H data…</div>
      )}

      {!busy && data && (
        <>
          {/* Hero H2H card */}
          <motion.div
            className="glass overflow-hidden"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {/* Gradient header */}
            <div
              className="h-1.5"
              style={{ background: `linear-gradient(90deg, ${teams[t1]?.color}, ${teams[t2]?.color})` }}
            />
            <div className="p-6">
              <div className="flex items-center justify-around">
                {/* Team 1 */}
                <div className="flex flex-col items-center gap-2">
                  <TeamLogo team={t1} meta={teams[t1]} size={80} glow />
                  <p className="text-sm font-bold text-white">{teams[t1]?.name}</p>
                  <p className="text-4xl font-black" style={{ color: teams[t1]?.color }}>{t1w}</p>
                  <p className="text-xs text-gray-500">wins ({t1pct}%)</p>
                  {teams[t1]?.titles > 0 && (
                    <p className="text-xs text-amber-400">{"🏆".repeat(teams[t1].titles)} {teams[t1].titles}x champions</p>
                  )}
                </div>

                {/* Center stats */}
                <div className="flex flex-col items-center gap-2 px-4">
                  <div className="text-xs text-gray-600 uppercase tracking-widest">Total Played</div>
                  <div className="text-5xl font-black text-gray-400">{total}</div>
                  <div className="text-xs text-gray-600">matches</div>
                </div>

                {/* Team 2 */}
                <div className="flex flex-col items-center gap-2">
                  <TeamLogo team={t2} meta={teams[t2]} size={80} glow />
                  <p className="text-sm font-bold text-white">{teams[t2]?.name}</p>
                  <p className="text-4xl font-black" style={{ color: teams[t2]?.color }}>{t2w}</p>
                  <p className="text-xs text-gray-500">wins ({t2pct}%)</p>
                  {teams[t2]?.titles > 0 && (
                    <p className="text-xs text-amber-400">{"🏆".repeat(teams[t2].titles)} {teams[t2].titles}x champions</p>
                  )}
                </div>
              </div>

              {/* Win share bar */}
              <div className="mt-6">
                <div className="flex justify-between text-xs text-gray-500 mb-1.5">
                  <span>{t1}</span>
                  <span>Win share</span>
                  <span>{t2}</span>
                </div>
                <div className="flex h-5 rounded-full overflow-hidden gap-0.5">
                  <motion.div
                    className="flex items-center justify-center text-[10px] font-bold text-white"
                    style={{ background: teams[t1]?.color }}
                    initial={{ flex: 0 }}
                    animate={{ flex: t1w || 0.01 }}
                    transition={{ duration: 1, ease: "easeOut" }}
                  >
                    {t1w > 2 && t1}
                  </motion.div>
                  <motion.div
                    className="flex items-center justify-center text-[10px] font-bold text-white"
                    style={{ background: teams[t2]?.color }}
                    initial={{ flex: 0 }}
                    animate={{ flex: t2w || 0.01 }}
                    transition={{ duration: 1, ease: "easeOut" }}
                  >
                    {t2w > 2 && t2}
                  </motion.div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Season chart */}
          {seasonArr.length > 0 && (
            <div className="glass p-6">
              <h3 className="text-sm font-semibold text-gray-400 mb-4">Season-by-Season Wins</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={seasonArr} barGap={3} barCategoryGap="30%">
                  <XAxis dataKey="season" tick={{ fill: "#6b7280", fontSize: 10 }} />
                  <YAxis allowDecimals={false} tick={{ fill: "#6b7280", fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{ background: "#12122a", border: "1px solid #1e1e40", borderRadius: 10 }}
                    labelStyle={{ color: "#fff" }}
                    cursor={{ fill: "rgba(255,255,255,0.04)" }}
                  />
                  <Bar dataKey={t1} fill={teams[t1]?.color || "#7c3aed"} radius={[4,4,0,0]} />
                  <Bar dataKey={t2} fill={teams[t2]?.color || "#f5a623"} radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Last 5 encounters */}
          {data.last5?.length > 0 && (
            <div className="glass p-6">
              <h3 className="text-sm font-semibold text-gray-400 mb-4">Last {data.last5.length} Encounters</h3>
              <div className="flex gap-3 flex-wrap">
                {data.last5.map((winner, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.08, type: "spring" }}
                    className="flex flex-col items-center gap-1.5 p-3 rounded-2xl"
                    style={{
                      background: (teams[winner]?.color || "#666") + "18",
                      border: `1px solid ${teams[winner]?.color || "#666"}33`,
                    }}
                  >
                    <TeamLogo team={winner} meta={teams[winner]} size={36} />
                    <span className="text-[10px] font-bold" style={{ color: teams[winner]?.color }}>
                      {winner}
                    </span>
                    <span className="text-[9px] text-gray-600">won</span>
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
