/**
 * SVG arena renderer — maps token positions onto a scaled 2D viewport.
 *
 * Renders tokens as coloured circles, weapon fire as dashed lines,
 * and a faint grid overlay for orientation.
 */

import type { FrameState, WeaponFiredEvent } from "./types";

const OWNER_COLOURS: Record<string, string> = {
  alice: "#60a5fa",
  bob: "#f87171",
  charlie: "#34d399",
  dave: "#fbbf24",
};

function ownerColour(owner: string): string {
  if (owner in OWNER_COLOURS) return OWNER_COLOURS[owner];
  let hash = 0;
  for (let i = 0; i < owner.length; i++) {
    hash = owner.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = ((hash % 360) + 360) % 360;
  return `hsl(${hue}, 70%, 60%)`;
}

interface ArenaViewProps {
  frame: FrameState;
  arenaSize: number;
  className?: string;
}

export function ArenaView({ frame, arenaSize, className }: ArenaViewProps) {
  const viewBox = `0 0 ${arenaSize} ${arenaSize}`;
  const gridStep = arenaSize / 10;
  const tokenRadius = arenaSize * 0.012;
  const fontSize = arenaSize * 0.014;

  return (
    <svg viewBox={viewBox} className={className} style={{ background: "#0a0a1a" }}>
      {/* Grid lines (10×10 classic overlay) */}
      {Array.from({ length: 11 }, (_, i) => (
        <g key={`grid-${i}`}>
          <line
            x1={i * gridStep}
            y1={0}
            x2={i * gridStep}
            y2={arenaSize}
            stroke="#1e293b"
            strokeWidth={arenaSize * 0.001}
          />
          <line
            x1={0}
            y1={i * gridStep}
            x2={arenaSize}
            y2={i * gridStep}
            stroke="#1e293b"
            strokeWidth={arenaSize * 0.001}
          />
        </g>
      ))}

      {/* Weapon fire lines */}
      {frame.lastShotEvents
        .filter((e): e is WeaponFiredEvent & { hit: true } => e.hit)
        .map((e, i) => {
          const attacker = frame.tokens.find((t) => t.id === e.attackerId);
          const target = frame.tokens.find((t) => t.id === e.targetId);
          if (!attacker || !target) return null;
          return (
            <line
              key={`shot-${i}`}
              x1={attacker.x}
              y1={attacker.y}
              x2={target.x}
              y2={target.y}
              stroke="#ef4444"
              strokeWidth={arenaSize * 0.002}
              strokeDasharray={`${arenaSize * 0.008} ${arenaSize * 0.004}`}
              opacity={0.7}
            />
          );
        })}

      {/* Tokens */}
      {frame.tokens.map((token) => {
        const colour = ownerColour(token.owner);
        const opacity = token.alive ? 1 : 0.25;
        return (
          <g key={token.id} opacity={opacity}>
            <circle
              cx={token.x}
              cy={token.y}
              r={tokenRadius}
              fill={colour}
              stroke="#fff"
              strokeWidth={arenaSize * 0.001}
            />
            <text
              x={token.x}
              y={token.y - tokenRadius * 1.4}
              textAnchor="middle"
              fill="#e2e8f0"
              fontSize={fontSize}
              fontFamily="monospace"
            >
              {token.id}
            </text>
            {token.alive && (
              <text
                x={token.x}
                y={token.y + tokenRadius * 2.2}
                textAnchor="middle"
                fill="#94a3b8"
                fontSize={fontSize * 0.8}
                fontFamily="monospace"
              >
                {token.hp}hp
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
