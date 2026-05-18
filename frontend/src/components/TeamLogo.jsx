import { useState } from "react";

/**
 * Shows the team's downloaded PNG logo.
 * Falls back to a colored monogram if the image fails to load.
 */
export default function TeamLogo({ team, meta, size = 48, className = "", glow = false }) {
  const [failed, setFailed] = useState(false);
  const color = meta?.color || "#888";

  const glowStyle = glow
    ? { filter: `drop-shadow(0 0 12px ${color}cc)` }
    : {};

  if (failed) {
    return (
      <div
        className={`flex items-center justify-center font-black rounded-xl shrink-0 ${className}`}
        style={{
          width: size, height: size,
          background: color + "22",
          color,
          fontSize: size * 0.32,
          border: `2px solid ${color}55`,
          ...glowStyle,
        }}
      >
        {team}
      </div>
    );
  }

  return (
    <img
      src={`/logos/${team}.png`}
      alt={team}
      width={size}
      height={size}
      className={`object-contain shrink-0 ${className}`}
      style={glowStyle}
      onError={() => setFailed(true)}
    />
  );
}
