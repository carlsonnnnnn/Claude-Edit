import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { easeInOut, prog, T } from "../anim";
import { C, COL, FRAME, Group, GROUPS, MID_CX, Price, PRICE_CX, ROW_H, rowTop, SUBJ_CX } from "../theme";
import { Layer, measure, TEXT_SHADOW, Txt } from "../text";

const STAGGER = 7; // frames between subject cells
const CELL_DUR = 16;

// Frame: stroke centred on the measured 6px border.
const FR = {
  x: FRAME.x0 + FRAME.stroke / 2,
  y: FRAME.y0 + FRAME.stroke / 2,
  w: FRAME.x1 - FRAME.x0 - FRAME.stroke,
  h: FRAME.y1 - FRAME.y0 - FRAME.stroke,
  r: FRAME.r - FRAME.stroke / 2,
};
// Glossy rim peeking out around the frame on the poster.
const RIM = { x: 97, y: 397.5, w: 876, h: 819, r: 40 };
const RIM_SEGMENTS: [number, number, number, number][] = [
  [70, 370, 170, 140], // top-left corner
  [835, 370, 175, 140], // top-right corner
  [70, 1110, 170, 130], // bottom-left corner
  [835, 1110, 175, 130], // bottom-right corner
  [70, 565, 60, 450], // left side
  [950, 555, 60, 450], // right side
];

const bell = (f: number, start: number, dur: number) =>
  interpolate(f, [start, start + dur * 0.4, start + dur], [0, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeInOut,
  });

const groupTimes = (g: Group, gi: number) => {
  const gs = T.group[gi];
  const mid = gs + g.rows.length * STAGGER + 2;
  return { gs, mid, starting: mid + 8, price: (k: number) => mid + 16 + k * 10 };
};

const PriceLine: React.FC<{ p: Price; start: number; f: number }> = ({ p, start, f }) => {
  const a = prog(f, start, 14);
  const count = Math.round(p.amount * prog(f, start, 28));
  const prefix = "RM ";
  const num = String(p.amount);
  const suffix = `${p.slash}month for`;
  // Lay the line out once with the final number, so counting never shifts it.
  const wp = measure(prefix, "body");
  const wn = measure(num, "body");
  const ws = measure(suffix, "body");
  const x0 = PRICE_CX - (wp + wn + ws) / 2;
  return (
    <g opacity={a} transform={`translate(0 ${(1 - a) * 12})`}>
      <Txt t="body" x={x0} y={p.baseline} anchor="start">
        {prefix}
      </Txt>
      <Txt t="body" x={x0 + wp + wn} y={p.baseline} anchor="end">
        {String(count)}
      </Txt>
      <Txt t="body" x={x0 + wp + wn} y={p.baseline} anchor="start">
        {suffix}
      </Txt>
      <Txt t="body" x={PRICE_CX} y={p.baseline + 20}>
        {p.mode}
      </Txt>
    </g>
  );
};

const GroupView: React.FC<{ g: Group; gi: number; f: number }> = ({ g, gi, f }) => {
  const tm = groupTimes(g, gi);
  const structure = prog(f, tm.gs + 4, 20);
  const midP = prog(f, tm.mid, 16);
  const rows = g.rows.map((_, i) => g.firstRow + i);
  const last = rows[rows.length - 1];
  const RX = COL.priceX1 - 1.5; // right border x
  const pulse = bell(f, T.pulse + gi * 7, 24);

  return (
    <g>
      {/* Middle + price columns: group outline and segmented dividers. */}
      <g opacity={structure}>
        <path
          d={`M ${COL.subjX1} ${g.y0 + 1.25} H ${RX - 12} Q ${RX} ${g.y0 + 1.25} ${RX} ${g.y0 + 13}`}
          fill="none"
          stroke={C.royal}
          strokeWidth={2.5}
        />
        <path
          d={`M ${COL.subjX1} ${g.y1 - 1.25} H ${RX - 12} Q ${RX} ${g.y1 - 1.25} ${RX} ${g.y1 - 13}`}
          fill="none"
          stroke={C.royal}
          strokeWidth={2.5}
        />
        {rows.map((r) => {
          const top = rowTop(r);
          const y0 = r === g.firstRow ? g.y0 + 13 : top + 3;
          const y1 = r === last ? g.y1 - 13 : top + ROW_H - 3;
          return <line key={`r${r}`} x1={RX} x2={RX} y1={y0} y2={y1} stroke={C.royal} strokeWidth={2.5} strokeLinecap="round" />;
        })}
        <g style={{ filter: "drop-shadow(0 0 2.5px rgba(59,190,236,0.9))" }}>
          {rows.map((r) =>
            [COL.subjX1 - 0.5, COL.midX1].map((x) => (
              <line key={`d${r}-${x}`} x1={x} x2={x} y1={rowTop(r) + 0.5} y2={rowTop(r) + ROW_H - 0.5} stroke={C.divider} strokeWidth={2} />
            )),
          )}
        </g>
      </g>

      {/* Price-cell highlight pulse. */}
      {pulse > 0.001 && (
        <rect
          x={COL.midX1 + 2}
          y={g.y0 + 2}
          width={RX - COL.midX1 - 3}
          height={g.y1 - g.y0 - 4}
          rx={12}
          fill={`rgba(59,190,236,${0.2 * pulse})`}
          stroke={`rgba(120,220,255,${0.9 * pulse})`}
          strokeWidth={2}
          style={{ filter: `drop-shadow(0 0 ${10 * pulse}px rgba(59,190,236,${0.9 * pulse}))` }}
        />
      )}

      {/* Subject cells slide in from the left, one by one. */}
      {g.rows.map((name, i) => {
        const r = g.firstRow + i;
        const p = prog(f, tm.gs + i * STAGGER, CELL_DUR);
        const top = rowTop(r);
        return (
          <g key={name} opacity={p} transform={`translate(${(1 - p) * -70} 0)`}>
            <rect
              x={COL.subjX0 + 1.5}
              y={top + 1.5}
              width={COL.subjX1 - COL.subjX0 - 3}
              height={ROW_H - 3}
              rx={8}
              fill={C.navy}
              stroke={C.cellBorder}
              strokeWidth={3}
              style={{ filter: `drop-shadow(0 0 ${6 * (1 - p)}px rgba(59,190,236,${0.8 * (1 - p)}))` }}
            />
            <g style={{ filter: TEXT_SHADOW }}>
              <Txt t="body" x={SUBJ_CX} y={top + 28.2}>
                {name}
              </Txt>
            </g>
          </g>
        );
      })}

      {/* Middle cell text. */}
      <g
        opacity={midP}
        style={{
          filter: TEXT_SHADOW,
          transformBox: "view-box",
          transformOrigin: `${MID_CX}px ${(g.y0 + g.y1) / 2}px`,
          transform: `scale(${0.94 + 0.06 * midP})`,
        }}
      >
        {g.mid.map((m) => (
          <Txt key={m.text + m.baseline} t="body" x={MID_CX} y={m.baseline}>
            {m.text}
          </Txt>
        ))}
      </g>

      {/* Price cell. */}
      <g style={{ filter: TEXT_SHADOW }}>
        <g opacity={prog(f, tm.starting, 14)}>
          <Txt t="body" x={PRICE_CX} y={g.startingBaseline}>
            Starting at
          </Txt>
        </g>
        {g.prices.map((p, k) => (
          <PriceLine key={k} p={p} start={tm.price(k)} f={f} />
        ))}
      </g>
    </g>
  );
};

export const Table: React.FC = () => {
  const f = useCurrentFrame();
  if (f < T.table) return null;
  const draw = prog(f, T.table, 42, easeInOut);
  const fill = prog(f, T.table + 6, 26);
  const rim = prog(f, T.table + 22, 26);
  const glowPulse = bell(f, T.pulse, 40);

  return (
    <Layer>
      <defs>
        <linearGradient id="rimGrad" x1="0" y1="0" x2="0.25" y2="1">
          <stop offset="0" stopColor="#5FD3F7" />
          <stop offset="0.25" stopColor="#1E6FB8" />
          <stop offset="0.5" stopColor="#3BBEEC" />
          <stop offset="0.75" stopColor="#1A5DA6" />
          <stop offset="1" stopColor="#47C6F0" />
        </linearGradient>
        <filter id="rimSoft" x="-10%" y="-10%" width="120%" height="120%">
          <feGaussianBlur stdDeviation="14" />
        </filter>
        <mask id="rimMask" maskUnits="userSpaceOnUse" x="0" y="0" width="1080" height="1440">
          <g filter="url(#rimSoft)">
            {RIM_SEGMENTS.map(([x, y, w, h], i) => (
              <rect key={i} x={x} y={y} width={w} height={h} fill="white" />
            ))}
          </g>
        </mask>
      </defs>

      {/* Soft blue glow around the table. */}
      <rect
        x={FR.x}
        y={FR.y}
        width={FR.w}
        height={FR.h}
        rx={FR.r}
        fill="none"
        stroke={C.cyan}
        strokeWidth={10}
        opacity={0.22 * fill + 0.35 * glowPulse}
        style={{ filter: "blur(16px)" }}
      />
      {/* Glossy rim. */}
      <rect
        x={RIM.x}
        y={RIM.y}
        width={RIM.w}
        height={RIM.h}
        rx={RIM.r}
        fill="none"
        stroke="url(#rimGrad)"
        strokeWidth={7}
        mask="url(#rimMask)"
        opacity={rim}
      />
      {/* Panel. */}
      <rect x={FR.x} y={FR.y} width={FR.w} height={FR.h} rx={FR.r} fill={C.navy} opacity={fill} />
      {/* Border draws itself. */}
      <rect
        x={FR.x}
        y={FR.y}
        width={FR.w}
        height={FR.h}
        rx={FR.r}
        fill="none"
        stroke={C.royal}
        strokeWidth={FRAME.stroke}
        pathLength={1}
        strokeDasharray="1 1"
        strokeDashoffset={1 - draw}
        style={{ filter: `drop-shadow(0 0 ${2 + 8 * (1 - fill)}px rgba(59,190,236,${0.85 * (1 - fill)}))` }}
      />
      {GROUPS.map((g, gi) => (f >= T.group[gi] ? <GroupView key={gi} g={g} gi={gi} f={f} /> : null))}
    </Layer>
  );
};
