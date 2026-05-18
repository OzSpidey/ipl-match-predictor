import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from "recharts";
import { fetchModelMetrics } from "../api/client";

const MODEL_META = {
  lr:       { name: "Logistic Regression", color: "#60a5fa", icon: "📈" },
  rf:       { name: "Random Forest",       color: "#34d399", icon: "🌲" },
  xgb:      { name: "XGBoost",             color: "#f59e0b", icon: "⚡" },
  lgbm:     { name: "LightGBM",            color: "#a78bfa", icon: "🚀" },
  ensemble: { name: "Ensemble",            color: "#f472b6", icon: "🎯" },
};

const FEAT_LABELS = {
  team1_overall_wr:    "Team 1 Overall Win Rate",
  team2_overall_wr:    "Team 2 Overall Win Rate",
  team1_form5:         "Team 1 Recent Form (5)",
  team2_form5:         "Team 2 Recent Form (5)",
  team1_form10:        "Team 1 Recent Form (10)",
  team2_form10:        "Team 2 Recent Form (10)",
  h2h_win_rate_team1:  "H2H Win Rate",
  team1_venue_wr:      "Team 1 Venue Win Rate",
  team2_venue_wr:      "Team 2 Venue Win Rate",
  toss_winner_is_team1:"Toss Winner",
  bat_first:           "Bat First",
  toss_and_bat_team1:  "Toss + Bat (Team 1)",
  season_norm:         "Season",
  wr_diff:             "Win Rate Differential",
  form5_diff:          "Form-5 Differential",
  form10_diff:         "Form-10 Differential",
  venue_wr_diff:       "Venue Win Rate Diff",
};

function MetricCard({ model, split, acc, auc, f1 }) {
  const meta = MODEL_META[model] || { name: model, color: "#888", icon: "•" };
  return (
    <motion.div
      className="glass p-4"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xl">{meta.icon}</span>
        <div>
          <p className="text-sm font-bold text-white">{meta.name}</p>
          <p className="text-xs text-gray-500 uppercase">{split} set</p>
        </div>
      </div>
      <div className="space-y-2">
        {[
          { label: "Accuracy",  value: `${(acc * 100).toFixed(1)}%` },
          { label: "AUC-ROC",   value: auc.toFixed(3)  },
          { label: "F1 Score",  value: f1.toFixed(3)   },
        ].map(m => (
          <div key={m.label} className="flex justify-between text-sm">
            <span className="text-gray-500">{m.label}</span>
            <span className="font-mono font-bold" style={{ color: meta.color }}>{m.value}</span>
          </div>
        ))}
        {/* Mini accuracy bar */}
        <div className="h-1 bg-white/10 rounded-full mt-2 overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ background: meta.color }}
            initial={{ width: 0 }}
            animate={{ width: `${acc * 100}%` }}
            transition={{ delay: 0.3, duration: 1 }}
          />
        </div>
      </div>
    </motion.div>
  );
}

export default function ModelInsights() {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    fetchModelMetrics()
      .then(setData)
      .catch(console.error)
      .finally(() => setBusy(false));
  }, []);

  if (busy) return (
    <div className="text-center text-gray-500 animate-pulse py-12">Loading model metrics…</div>
  );
  if (!data) return (
    <div className="glass p-8 text-center text-red-400">
      Could not load model metrics. Run <code>train.py</code> first.
    </div>
  );

  const { metrics, feature_importance, confusion_matrix: cm } = data;

  // Feature importance bar data
  const featData = Object.entries(feature_importance || {})
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10)
    .map(([k, v]) => ({
      name:  FEAT_LABELS[k] || k,
      value: Math.round(v * 1000) / 10,
    }));

  // Model comparison radar
  const modelRadar = Object.entries(metrics || {}).map(([id, m]) => ({
    model:    MODEL_META[id]?.icon + " " + (MODEL_META[id]?.name || id),
    accuracy: Math.round((m.test?.accuracy || 0) * 100),
    auc:      Math.round((m.test?.roc_auc  || 0) * 100),
    f1:       Math.round((m.test?.f1       || 0) * 100),
  }));

  // Confusion matrix cells
  const cmLabels = ["Team 2 Wins", "Team 1 Wins"];

  return (
    <div className="space-y-6">
      {/* Header info */}
      <div className="glass p-6">
        <h2 className="text-lg font-bold mb-2">🤖 Model Insights</h2>
        <div className="flex flex-wrap gap-3 text-sm text-gray-400">
          <span>Training: {data.train_seasons}</span>
          <span>•</span>
          <span>Test: {data.test_seasons}</span>
          <span>•</span>
          <span>{data.total_matches} total matches</span>
          <span>•</span>
          <span>17 features</span>
        </div>
        <div className="mt-4 p-3 bg-violet-900/20 border border-violet-800 rounded-xl text-sm text-violet-300">
          <strong>Architecture:</strong> Logistic Regression + Random Forest + XGBoost + LightGBM →
          Isotonic-calibrated soft-voting ensemble. All features are computed using expanding windows
          (no future leakage).
        </div>
      </div>

      {/* Per-model test metrics */}
      <div>
        <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">Test Set Performance</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(metrics || {}).map(([id, m]) => (
            <MetricCard
              key={id} model={id} split="test"
              acc={m.test?.accuracy || 0}
              auc={m.test?.roc_auc  || 0}
              f1={m.test?.f1        || 0}
            />
          ))}
        </div>
      </div>

      {/* Feature importance */}
      {featData.length > 0 && (
        <div className="glass p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wider">
            Top-10 Feature Importances (XGBoost)
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={featData} layout="vertical" margin={{ left: 10, right: 30 }}>
              <XAxis type="number" tick={{ fill: "#6b7280", fontSize: 10 }} tickFormatter={v => `${v}%`} />
              <YAxis type="category" dataKey="name" tick={{ fill: "#d1d5db", fontSize: 10 }} width={190} />
              <Tooltip
                contentStyle={{ background: "#12122a", border: "1px solid #1e1e40", borderRadius: 8 }}
                formatter={v => [`${v}%`, "Importance"]}
                labelStyle={{ color: "#fff" }}
              />
              <Bar dataKey="value" radius={[0,4,4,0]}>
                {featData.map((_, i) => (
                  <Cell
                    key={i}
                    fill={`hsl(${260 - i * 18}, 70%, ${60 - i * 2}%)`}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Confusion matrix */}
      {cm && (
        <div className="glass p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wider">
            Confusion Matrix (Ensemble · Test Set)
          </h3>
          <div className="flex justify-center">
            <div>
              <p className="text-xs text-center text-gray-600 mb-2">Predicted →</p>
              <div className="grid grid-cols-3 gap-1 text-sm">
                <div />
                {cmLabels.map(l => (
                  <div key={l} className="text-center text-xs text-gray-500 pb-1 px-2">{l}</div>
                ))}
                {cm.map((row, ri) => [
                  <div key={`l${ri}`} className="text-xs text-gray-500 flex items-center justify-end pr-2">
                    {cmLabels[ri]}
                  </div>,
                  ...row.map((val, ci) => (
                    <motion.div
                      key={`${ri}-${ci}`}
                      className="w-24 h-16 rounded-lg flex items-center justify-center font-bold text-lg"
                      style={{
                        background: ri === ci
                          ? `rgba(124,58,237,${0.3 + val / Math.max(...cm.flat()) * 0.5})`
                          : `rgba(239,68,68,${0.1 + val  / Math.max(...cm.flat()) * 0.4})`,
                        color: ri === ci ? "#c4b5fd" : "#fca5a5",
                      }}
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: (ri + ci) * 0.1 }}
                    >
                      {val}
                    </motion.div>
                  )),
                ])}
              </div>
              <p className="text-xs text-center text-gray-600 mt-3">↑ Actual</p>
            </div>
          </div>
        </div>
      )}

      {/* Model explanation callout */}
      <div className="glass p-6 border border-blue-900/50 bg-blue-950/20">
        <h3 className="text-sm font-semibold text-blue-300 mb-2">📘 How the model works</h3>
        <ul className="text-sm text-gray-400 space-y-1.5 list-disc list-inside">
          <li>Trained on 2008–2020 seasons; validated on 2021; tested on 2022–2024</li>
          <li>All stats (form, win rate, H2H) use expanding windows — no future data leakage</li>
          <li>Probabilities are isotonically calibrated for reliability</li>
          <li>Ensemble uses soft voting with higher weight on tree-based models</li>
          <li>Win-rate differential and venue advantage are the strongest predictors</li>
        </ul>
      </div>
    </div>
  );
}
