import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import TeamLogo from "./TeamLogo";

/* Animated cricket ball SVG */
function CricketBall({ size = 28, className = "" }) {
  return (
    <svg
      width={size} height={size} viewBox="0 0 100 100"
      className={className}
      fill="none" xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="50" cy="50" r="48" fill="#C0392B" stroke="#922B21" strokeWidth="2"/>
      <circle cx="50" cy="50" r="48" fill="url(#ballGrad)" opacity="0.4"/>
      {/* Seam */}
      <path d="M50 4 C30 25, 30 75, 50 96" stroke="#F5F5F5" strokeWidth="3" fill="none" strokeLinecap="round"/>
      <path d="M50 4 C70 25, 70 75, 50 96" stroke="#F5F5F5" strokeWidth="3" fill="none" strokeLinecap="round"/>
      {/* Seam stitches */}
      <path d="M38 22 L42 18 M38 32 L42 28 M38 42 L42 38 M38 52 L42 48 M38 62 L42 58 M38 72 L42 68 M38 82 L42 78"
            stroke="#F5F5F5" strokeWidth="1.5" strokeLinecap="round"/>
      <path d="M62 22 L58 18 M62 32 L58 28 M62 42 L58 38 M62 52 L58 48 M62 62 L58 58 M62 72 L58 68 M62 82 L58 78"
            stroke="#F5F5F5" strokeWidth="1.5" strokeLinecap="round"/>
      <defs>
        <radialGradient id="ballGrad" cx="35%" cy="35%">
          <stop offset="0%" stopColor="white" stopOpacity="0.5"/>
          <stop offset="100%" stopColor="transparent"/>
        </radialGradient>
      </defs>
    </svg>
  );
}

/* Trophy SVG */
function Trophy({ size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <path d="M8 21h8M12 17v4M17 3H7l1 7c0 2.2 1.8 4 4 4s4-1.8 4-4l1-7z"
            stroke="#F5A623" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M7 3H4v3a3 3 0 003 3M17 3h3v3a3 3 0 01-3 3"
            stroke="#F5A623" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

export default function Header({ recentMatches, teams }) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const tickerItems = recentMatches.slice(0, 12).map(m =>
    `${m.team1}  vs  ${m.team2}   Winner: ${m.winner}   (${m.venue?.split(",")[0]})`
  );

  return (
    <header className="border-b border-violet-900/40 sticky top-0 z-50">
      {/* ── Hero banner ───────────────────────────────────────── */}
      <div className="stadium-bg overflow-hidden">
        <div className="max-w-6xl mx-auto px-4 py-6 relative">

          {/* Floating decorative balls */}
          <motion.div
            className="absolute right-12 top-4 opacity-20"
            animate={{ rotate: 360 }}
            transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
          >
            <CricketBall size={80} />
          </motion.div>
          <motion.div
            className="absolute left-4 bottom-2 opacity-10"
            animate={{ rotate: -360 }}
            transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
          >
            <CricketBall size={50} />
          </motion.div>

          {/* Main header content */}
          <div className="relative flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5 }}
              >
                <CricketBall size={52} className="cricket-ball-spin" />
              </motion.div>

              <div>
                <motion.h1
                  initial={{ x: -30, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  className="text-2xl sm:text-3xl font-extrabold leading-tight"
                >
                  <span className="bg-gradient-to-r from-amber-400 via-pink-400 to-violet-400 bg-clip-text text-transparent">
                    IPL Match Predictor
                  </span>
                </motion.h1>
                <p className="text-xs text-gray-500 mt-0.5">
                  Ensemble ML · 1700+ matches · 17 seasons · 4 models
                </p>
              </div>
            </div>

            {/* Live clock + status */}
            <div className="hidden sm:flex flex-col items-end gap-1.5">
              <div className="flex items-center gap-2 bg-green-900/30 border border-green-800/60 px-3 py-1.5 rounded-lg">
                <span className="w-2 h-2 rounded-full bg-green-400 pulse-glow" />
                <span className="text-xs font-bold text-green-400">IPL 2025 LIVE</span>
              </div>
              <span className="text-xs text-gray-600 font-mono">
                {time.toLocaleTimeString()}
              </span>
            </div>
          </div>

          {/* Team logo strip */}
          {Object.keys(teams).length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="mt-5 flex flex-wrap gap-3 items-center"
            >
              {Object.entries(teams).map(([id, meta], i) => (
                <motion.div
                  key={id}
                  initial={{ opacity: 0, scale: 0.6 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.04 }}
                  className="group relative"
                  title={meta.name}
                >
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300
                                group-hover:scale-125 group-hover:z-10 cursor-pointer"
                    style={{
                      background: meta.color + "18",
                      border: `1px solid ${meta.color}44`,
                    }}
                  >
                    <TeamLogo team={id} meta={meta} size={32} />
                  </div>

                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-1 rounded text-xs
                                  bg-gray-900 border border-gray-700 whitespace-nowrap opacity-0 group-hover:opacity-100
                                  transition-opacity pointer-events-none z-50">
                    {meta.name}
                    {meta.titles > 0 && (
                      <span className="ml-1 text-amber-400">
                        {'🏆'.repeat(meta.titles)}
                      </span>
                    )}
                  </div>
                </motion.div>
              ))}

              {/* Trophy tally */}
              <div className="ml-auto hidden sm:flex items-center gap-1.5 text-xs text-amber-400/70">
                <Trophy size={16} />
                <span>Hover teams for titles</span>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* ── Live results ticker ──────────────────────────────── */}
      {tickerItems.length > 0 && (
        <div className="bg-violet-950/70 border-t border-violet-900/50 overflow-hidden py-1.5">
          <div className="ticker-inner text-xs text-violet-300/70 gap-0">
            {[...tickerItems, ...tickerItems].map((item, i) => (
              <span key={i} className="mr-16">
                <span className="text-violet-500 mr-2">●</span>
                {item}
              </span>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
