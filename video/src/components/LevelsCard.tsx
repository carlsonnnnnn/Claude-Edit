import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { prog, soft, T } from "../anim";
import { C } from "../theme";
import { Layer, Txt } from "../text";

const CARD = { x: 128, y: 1224, w: 825, h: 109, r: 22 };
const BULLETS = [
  { text: "Sekolah Rendah (KSSR)", dotX: 168.5, x: 186, y: 1285 },
  { text: "Sekolah Menengah (KSSM)", dotX: 168.5, x: 186, y: 1320 },
  { text: "Primary (International Curricula)", dotX: 533.5, x: 552, y: 1285 },
  { text: "Secondary (International Curricula)", dotX: 533.5, x: 552, y: 1320 },
];

export const LevelsCard: React.FC = () => {
  const f = useCurrentFrame();
  if (f < T.card) return null;
  const s = soft(f, T.card, 30, 16, 1);
  const head = prog(f, T.card + 10, 14);
  return (
    <Layer>
      <g opacity={Math.min(1, s * 1.6)} transform={`translate(0 ${(1 - s) * 150})`}>
        <rect
          x={CARD.x}
          y={CARD.y}
          width={CARD.w}
          height={CARD.h}
          rx={CARD.r}
          fill={C.white}
          style={{ filter: "drop-shadow(0 6px 14px rgba(0, 10, 40, 0.35))" }}
        />
        <g
          opacity={head}
          style={{
            transformBox: "view-box",
            transformOrigin: "527px 1248px",
            transform: `scale(${interpolate(head, [0, 1], [0.9, 1])})`,
          }}
        >
          <Txt t="cardHead" x={527.5} y={1257} fill={C.red}>
            Available for all levels:
          </Txt>
        </g>
        {BULLETS.map((b, i) => {
          const p = prog(f, T.card + 20 + i * 11, 14);
          return (
            <g key={b.text} opacity={p} transform={`translate(${(1 - p) * -22} 0)`}>
              <circle cx={b.dotX} cy={b.y - 7.2} r={3.3} fill={C.bullet} />
              <Txt t="bullet" x={b.x} y={b.y} anchor="start" fill={C.bullet}>
                {b.text}
              </Txt>
            </g>
          );
        })}
      </g>
    </Layer>
  );
};
