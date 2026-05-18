import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ReactConfetti from "react-confetti";
import { postPredict } from "../api/client";
import TeamLogo from "./TeamLogo";

/* ── Small sub-components ─────────────────────────────────────────────────── */
function TeamCard({ id, meta, selected, onClick, dim }) {
  return (
    <motion.div
      whileHover={{ scale: dim ? 1 : 1.07 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={`flex flex-col items-center justify-center rounded-2xl cursor-pointer
                  border-2 transition-all duration-250 p-2.5 select-none relative overflow-hidden
                  ${dim ? "opacity-25 pointer-events-none" : ""}`}
      style={{
        borderColor: selected ? meta?.color : "rgba(255,255,255,0.08)",
        background:   selected
          ? `linear-gradient(135deg, ${meta?.color}22, ${meta?.color}08)`
          : "rgba(255,255,255,0.03)",
        boxShadow: selected ? `0 0 22px ${meta?.color}55, inset 0 0 12px ${meta?.color}18` : "none",
        minWidth: 72,
      }}
    >
      {/* Glow ring when selected */}
      {selected && (
        <div
          className="absolute inset-0 rounded-2xl pointer-events-none"
          style={{ boxShadow: `inset 0 0 20px ${meta?.color}33` }}
        />
      )}

      <TeamLogo team={id} meta={meta} size={44} glow={selected} />
      <span
        className="text-[10px] font-extrabold mt-1.5 tracking-wide"
        style={{ color: selected ? meta?.color : "#6b7280" }}
      >
        {id}
      </span>
      {meta?.titles > 0 && (
        <span className="text-[8px] text-amber-400/70 -mt-0.5">
          {"🏆".repeat(Math.min(meta.titles, 3))}
        </span>
      )}
    </motion.div>
  );
}

function ProbabilityGauge({ prob, color, team, meta, isWinner }) {
  return (
    <div className="flex-1 min-w-0 flex flex-col items-center gap-3">
      {/* Team logo + name */}
      <div className="flex flex-col items-center gap-1.5">
        <motion.div
          animate={isWinner ? { scale: [1, 1.08, 1] } : {}}
          transition={{ repeat: Infinity, duration: 2.5 }}
        >
          <TeamLogo team={team} meta={meta} size={72} glow={isWinner} />
        </motion.div>
        <span
          className={`text-sm font-black ${isWinner ? "text-white" : "text-gray-500"}`}
          style={isWinner ? { color } : {}}
        >
          {team}
        </span>
        <span className="text-xs text-gray-600 text-center leading-tight max-w-[100px]">
          {meta?.name}
        </span>
      </div>

      {/* Circular probability arc */}
      <div className="relative">
        <svg width={120} height={70} viewBox="0 0 120 70">
          {/* Track */}
          <path d="M 12 65 A 50 50 0 0 1 108 65" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" strokeLinecap="round"/>
          {/* Fill */}
          <motion.path
            d="M 12 65 A 50 50 0 0 1 108 65"
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray="157"
            initial={{ strokeDashoffset: 157 }}
            animate={{ strokeDashoffset: 157 - (prob * 157) }}
            transition={{ duration: 1.4, ease: "easeOut" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
          <motion.span
            className="text-2xl font-black"
            style={{ color: isWinner ? color : "#6b7280" }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
          >
            {(prob * 100).toFixed(1)}%
          </motion.span>
        </div>
      </div>

      {isWinner && (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
          className="px-3 py-1 rounded-full text-xs font-bold"
          style={{ background: color + "22", color, border: `1px solid ${color}55` }}
        >
          ⚡ PREDICTED WINNER
        </motion.div>
      )}
    </div>
  );
}

function ConfidenceBadge({ level }) {
  const cfg = {
    "very high": { bg: "from-green-600  to-emerald-500", label: "Very High Confidence 🔥" },
    "high":      { bg: "from-blue-600   to-cyan-500",    label: "High Confidence ⚡"       },
    "moderate":  { bg: "from-yellow-600 to-amber-500",   label: "Moderate Confidence"      },
    "low":       { bg: "from-red-700    to-rose-500",    label: "Low Confidence"           },
  };
  const c = cfg[level] || cfg["moderate"];
  return (
    <span className={`px-4 py-1.5 rounded-full text-xs font-bold bg-gradient-to-r ${c.bg} text-white shadow-lg`}>
      {c.label}
    </span>
  );
}

/* ── Main component ───────────────────────────────────────────────────────── */
export default function MatchPredictor({ teams, venues }) {
  const [team1,        setTeam1]    = useState(null);
  const [team2,        setTeam2]    = useState(null);
  const [venue,        setVenue]    = useState("");
  const [tossWinner,   setToss]     = useState("");
  const [tossDec,      setDec]      = useState("bat");
  const [result,       setResult]   = useState(null);
  const [loading,      setLoading]  = useState(false);
  const [error,        setError]    = useState("");
  const [showConfetti, setConfetti] = useState(false);

  const teamIds    = Object.keys(teams);
  const canPredict = team1 && team2 && venue && tossWinner;

  const handlePredict = async () => {
    if (!canPredict) return;
    setLoading(true);
    setError("");
    try {
      const data = await postPredict({
        team1, team2, venue, toss_winner: tossWinner, toss_decision: tossDec,
      });
      setResult(data);
      setConfetti(true);
      setTimeout(() => setConfetti(false), 5000);
    } catch {
      setError("Prediction failed — make sure the backend is running (uvicorn api.main:app).");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setTeam1(null); setTeam2(null); setVenue("");
    setToss(""); setDec("bat"); setResult(null); setError("");
  };

  const winnerMeta = result ? teams[result.predicted_winner] : null;

  return (
    <div className="space-y-6">
      {showConfetti && winnerMeta && (
        <ReactConfetti
          width={window.innerWidth}
          height={window.innerHeight}
          recycle={false}
          numberOfPieces={350}
          colors={[winnerMeta.color, winnerMeta.secondary || "#fff", "#f5a623", "#ffffff"]}
        />
      )}

      {/* ── Step 1: Team selection ──────────────────────────── */}
      <motion.div
        className="glass p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h2 className="text-base font-bold mb-5 text-gray-200 flex items-center gap-2">
          <span className="w-6 h-6 rounded-full bg-violet-600 flex items-center justify-center text-xs">1</span>
          Select Teams
        </h2>

        <div className="grid grid-cols-2 gap-4 sm:gap-8">
          {/* Team 1 */}
          <div>
            <p className="text-xs text-gray-500 mb-3 uppercase tracking-widest">Team 1</p>
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
              {teamIds.map(id => (
                <TeamCard
                  key={id} id={id} meta={teams[id]}
                  selected={team1 === id} dim={team2 === id}
                  onClick={() => { if (team2 !== id) { setTeam1(id); if (!tossWinner) setToss(id); } }}
                />
              ))}
            </div>
          </div>

          {/* Team 2 */}
          <div className="border-l border-brand-border pl-4 sm:pl-8">
            <p className="text-xs text-gray-500 mb-3 uppercase tracking-widest">Team 2</p>
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
              {teamIds.map(id => (
                <TeamCard
                  key={id} id={id} meta={teams[id]}
                  selected={team2 === id} dim={team1 === id}
                  onClick={() => { if (team1 !== id) setTeam2(id); }}
                />
              ))}
            </div>
          </div>
        </div>

        {/* VS card — shows when both teams are selected */}
        <AnimatePresence>
          {team1 && team2 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.85, y: 10 }}
              animate={{ opacity: 1, scale: 1,    y: 0  }}
              exit={{ opacity: 0, scale: 0.85 }}
              className="mt-6 flex items-center justify-center gap-6 p-4 rounded-2xl"
              style={{
                background: `linear-gradient(135deg,
                  ${teams[team1]?.color}12, transparent 40%,
                  transparent 60%, ${teams[team2]?.color}12)`,
                border: `1px solid rgba(255,255,255,0.07)`,
              }}
            >
              {/* Team 1 */}
              <div className="flex flex-col items-center gap-1.5">
                <TeamLogo team={team1} meta={teams[team1]} size={64} glow />
                <span className="text-xs font-bold text-gray-300">{teams[team1]?.name?.split(" ").slice(-2).join(" ")}</span>
                {teams[team1]?.titles > 0 && (
                  <span className="text-[10px] text-amber-400">{"🏆".repeat(teams[team1].titles)} {teams[team1].titles}x Champs</span>
                )}
              </div>

              {/* VS */}
              <div className="flex flex-col items-center">
                <motion.div
                  animate={{ scale: [1, 1.2, 1], opacity: [0.6, 1, 0.6] }}
                  transition={{ repeat: Infinity, duration: 1.8 }}
                  className="text-3xl font-black text-gray-500 tracking-widest"
                >
                  VS
                </motion.div>
                <span className="text-[9px] text-gray-600 mt-1 uppercase tracking-widest">IPL 2025</span>
              </div>

              {/* Team 2 */}
              <div className="flex flex-col items-center gap-1.5">
                <TeamLogo team={team2} meta={teams[team2]} size={64} glow />
                <span className="text-xs font-bold text-gray-300">{teams[team2]?.name?.split(" ").slice(-2).join(" ")}</span>
                {teams[team2]?.titles > 0 && (
                  <span className="text-[10px] text-amber-400">{"🏆".repeat(teams[team2].titles)} {teams[team2].titles}x Champs</span>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* ── Step 2: Match setup ─────────────────────────────── */}
      <AnimatePresence>
        {team1 && team2 && (
          <motion.div
            className="glass p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <h2 className="text-base font-bold mb-5 text-gray-200 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-violet-600 flex items-center justify-center text-xs">2</span>
              Match Setup
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Venue */}
              <div>
                <label className="text-xs text-gray-500 uppercase tracking-widest block mb-2">Venue</label>
                <select
                  value={venue}
                  onChange={e => setVenue(e.target.value)}
                  className="w-full bg-brand-bg border border-brand-border rounded-xl px-3 py-3 text-sm text-white
                             focus:outline-none focus:border-violet-500 transition-colors"
                >
                  <option value="">Select venue…</option>
                  {venues.map(v => (
                    <option key={v.name} value={v.name}>{v.name} ({v.city})</option>
                  ))}
                </select>
              </div>

              {/* Toss winner */}
              <div>
                <label className="text-xs text-gray-500 uppercase tracking-widest block mb-2">Toss Winner</label>
                <div className="flex gap-2 h-[46px]">
                  {[team1, team2].map(t => (
                    <button
                      key={t}
                      onClick={() => setToss(t)}
                      className="flex-1 rounded-xl text-sm font-bold border-2 transition-all duration-200 flex items-center justify-center gap-2"
                      style={tossWinner === t ? {
                        background:   teams[t]?.color + "30",
                        borderColor:  teams[t]?.color,
                        color:        teams[t]?.color,
                        boxShadow:    `0 0 14px ${teams[t]?.color}55`,
                      } : {
                        borderColor: "rgba(255,255,255,0.1)",
                        color: "#6b7280",
                      }}
                    >
                      <TeamLogo team={t} meta={teams[t]} size={20} />
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              {/* Toss decision */}
              <div>
                <label className="text-xs text-gray-500 uppercase tracking-widest block mb-2">Decision</label>
                <div className="flex gap-2 h-[46px]">
                  {["bat", "field"].map(d => (
                    <button
                      key={d}
                      onClick={() => setDec(d)}
                      className={`flex-1 rounded-xl text-sm font-bold border-2 transition-all duration-200 ${
                        tossDec === d
                          ? "bg-violet-600/30 border-violet-500 text-white shadow-lg shadow-violet-900/40"
                          : "border-white/10 text-gray-500 hover:text-white hover:border-gray-600"
                      }`}
                    >
                      {d === "bat" ? "🏏 Bat" : "🧤 Field"}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Predict button */}
            <div className="mt-6 flex gap-3">
              <motion.button
                whileHover={{ scale: canPredict ? 1.02 : 1 }}
                whileTap={{ scale: 0.97 }}
                disabled={!canPredict || loading}
                onClick={handlePredict}
                className={`btn-glow flex-1 py-4 rounded-xl text-base font-extrabold uppercase tracking-widest
                  ${canPredict
                    ? "bg-gradient-to-r from-violet-600 via-purple-600 to-indigo-600 text-white cursor-pointer"
                    : "bg-gray-800 text-gray-600 cursor-not-allowed shadow-none"
                  }`}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <motion.span
                      animate={{ rotate: 360 }}
                      transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
                    >⚙️</motion.span>
                    Predicting…
                  </span>
                ) : "⚡ Predict Winner"}
              </motion.button>

              <button
                onClick={reset}
                className="px-5 rounded-xl border border-brand-border text-gray-500 hover:text-white text-sm transition-colors"
              >
                Reset
              </button>
            </div>

            {error && (
              <p className="mt-3 text-sm text-red-400 bg-red-900/20 border border-red-800 rounded-xl px-4 py-3">
                ⚠️ {error}
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Step 3: Result ──────────────────────────────────── */}
      <AnimatePresence>
        {result && (
          <motion.div
            className="glass overflow-hidden"
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ type: "spring", stiffness: 180, damping: 18 }}
          >
            {/* Colored winner header bar */}
            <div
              className="h-1.5 w-full"
              style={{
                background: `linear-gradient(90deg, ${teams[result.predicted_winner]?.color}, transparent)`,
              }}
            />

            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-base font-bold text-gray-200">Prediction Result</h2>
                <ConfidenceBadge level={result.confidence} />
              </div>

              {/* Probability gauges */}
              <div className="flex items-center gap-4">
                <ProbabilityGauge
                  prob={result.team1_win_probability}
                  color={teams[team1]?.color || "#7c3aed"}
                  team={team1}
                  meta={teams[team1]}
                  isWinner={result.predicted_winner === team1}
                />

                <div className="flex flex-col items-center gap-2 shrink-0">
                  <div className="text-xl font-black text-gray-600">VS</div>
                  {/* Vertical probability bar */}
                  <div className="h-24 w-2 bg-white/10 rounded-full overflow-hidden relative">
                    <motion.div
                      className="absolute bottom-0 left-0 right-0 rounded-full"
                      style={{ background: teams[team1]?.color || "#7c3aed" }}
                      initial={{ height: "50%" }}
                      animate={{ height: `${result.team1_win_probability * 100}%` }}
                      transition={{ duration: 1.2, ease: "easeOut" }}
                    />
                  </div>
                </div>

                <ProbabilityGauge
                  prob={result.team2_win_probability}
                  color={teams[team2]?.color || "#f5a623"}
                  team={team2}
                  meta={teams[team2]}
                  isWinner={result.predicted_winner === team2}
                />
              </div>

              {/* Winner announcement */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="mt-6 flex items-center justify-center gap-3 p-4 rounded-2xl"
                style={{
                  background: `linear-gradient(135deg, ${winnerMeta?.color}18, transparent)`,
                  border: `1px solid ${winnerMeta?.color}33`,
                }}
              >
                <TeamLogo team={result.predicted_winner} meta={winnerMeta} size={48} glow />
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-widest">Predicted to win</p>
                  <p className="text-2xl font-black" style={{ color: winnerMeta?.color }}>
                    {winnerMeta?.name}
                  </p>
                  <p className="text-sm text-gray-400">
                    {(Math.max(result.team1_win_probability, result.team2_win_probability) * 100).toFixed(1)}% probability
                    {winnerMeta?.titles > 0 && ` · ${winnerMeta.titles}x IPL Champions`}
                  </p>
                </div>
              </motion.div>

              {/* Key factors */}
              {result.key_factors?.length > 0 && (
                <div className="mt-5">
                  <p className="text-xs text-gray-600 uppercase tracking-widest mb-3">Why this prediction?</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {result.key_factors.map((f, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -16 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.7 + i * 0.1 }}
                        className="flex items-center gap-3 bg-white/5 rounded-xl px-3 py-2.5"
                      >
                        <TeamLogo team={f.team} meta={teams[f.team]} size={28} />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs text-gray-300 truncate">{f.label}</p>
                          <div className="mt-1 h-1 bg-white/10 rounded-full overflow-hidden">
                            <motion.div
                              className="h-full rounded-full"
                              style={{ background: teams[f.team]?.color || "#7c3aed" }}
                              initial={{ width: 0 }}
                              animate={{ width: `${Math.min(f.delta * 500, 100)}%` }}
                              transition={{ delay: 0.8 + i * 0.1, duration: 0.8 }}
                            />
                          </div>
                        </div>
                        <span className="text-xs font-mono text-gray-500">
                          +{(f.delta * 100).toFixed(1)}%
                        </span>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
