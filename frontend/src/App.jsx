import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Header          from "./components/Header";
import MatchPredictor  from "./components/MatchPredictor";
import HeadToHead      from "./components/HeadToHead";
import TeamStats       from "./components/TeamStats";
import ModelInsights   from "./components/ModelInsights";
import WhatIf          from "./components/WhatIf";
import { fetchTeams, fetchVenues, fetchRecentMatches } from "./api/client";

const TABS = [
  { id: "predict",  label: "🏏 Predict Match" },
  { id: "whatif",   label: "⚗️ What-If"        },
  { id: "h2h",      label: "⚔️  Head-to-Head"  },
  { id: "teams",    label: "📊 Team Analytics" },
  { id: "model",    label: "🤖 Model Insights" },
];

export default function App() {
  const [tab,           setTab]    = useState("predict");
  const [teams,         setTeams]  = useState({});
  const [venues,        setVenues] = useState([]);
  const [recentMatches, setRecent] = useState([]);
  const [loading,       setLoading]= useState(true);

  useEffect(() => {
    Promise.all([fetchTeams(), fetchVenues(), fetchRecentMatches()])
      .then(([t, v, r]) => { setTeams(t); setVenues(v); setRecent(r); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <Header recentMatches={recentMatches} teams={teams} />

      {/* Tab navigation */}
      <nav className="sticky top-0 z-40 bg-brand-bg/90 backdrop-blur border-b border-brand-border">
        <div className="max-w-6xl mx-auto px-4 flex gap-1 py-2 overflow-x-auto">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all duration-200
                ${tab === t.id
                  ? "bg-violet-600 text-white shadow-lg shadow-violet-900/50"
                  : "text-gray-400 hover:text-white hover:bg-brand-card"
                }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Main content */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-400 text-lg animate-pulse">Loading IPL data…</div>
          </div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div
              key={tab}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{    opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
            >
              {tab === "predict" && <MatchPredictor teams={teams} venues={venues} />}
              {tab === "whatif"  && <WhatIf          teams={teams} venues={venues} />}
              {tab === "h2h"     && <HeadToHead     teams={teams} />}
              {tab === "teams"   && <TeamStats       teams={teams} />}
              {tab === "model"   && <ModelInsights />}
            </motion.div>
          </AnimatePresence>
        )}
      </main>

      <footer className="text-center text-xs text-gray-600 py-4 border-t border-brand-border">
        IPL Match Predictor · Ensemble ML (LR + RF + XGBoost + LightGBM) · Built with FastAPI + React
      </footer>
    </div>
  );
}
