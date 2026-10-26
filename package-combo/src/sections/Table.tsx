import React from 'react';
import {AbsoluteFill, Easing, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, FONT_SPARTAN, HEIGHT, L, T, WIDTH, bump, lerp, ramp, s} from '../theme';

type Line = {text: string; x: number; base: number; track?: number};
type Row = {start: number; cells: Line[][]};

// Centres and baselines measured on poster.png. Only the Royal row's third cell
// differs from the poster ("+ rebate 1-on-1" → "+ special price 1-on-1 sessions").
export const ROWS: Row[] = [
  {
    start: T.scholar,
    cells: [
      [{text: 'Scholar', x: 163, base: 348}],
      [{text: '1 subject group', x: 454, base: 348}],
      [
        {text: '+ free notes &', x: 829, base: 335},
        {text: 'exercise', x: 829, base: 365},
      ],
    ],
  },
  {
    start: T.knight,
    cells: [
      [{text: 'Knight', x: 159.5, base: 446}],
      [{text: '3 subject group', x: 453, base: 446}],
      [], // drawn by KnightOffer so "10%" can pop on its own
    ],
  },
  {
    start: T.noble,
    cells: [
      [{text: 'Noble', x: 158, base: 570, track: -1.3}],
      [{text: '5 subject group', x: 453.5, base: 570, track: -2.3}],
      [{text: '+ 15% off', x: 837.5, base: 570, track: -2.3}],
    ],
  },
  {
    start: T.royal,
    cells: [
      [{text: 'Royal', x: 158.5, base: 769}],
      [
        {text: '5 subject group +', x: 443, base: 752},
        {text: '2 sessions 1-on-1', x: 443.5, base: 786},
      ],
      [
        {text: '+ 15% off', x: 828.5, base: 698},
        {text: '+ academic', x: 832, base: 733},
        {text: 'performance report', x: 827.5, base: 768},
        {text: '+ special price', x: 831, base: 803},
        {text: '1-on-1 sessions', x: 831, base: 838},
      ],
    ],
  },
];

const SIZE = 39;
const CELL_STAGGER = 9;
const LINE_STAGGER = 5;

const cellRect = (r: number, c: number) => {
  const [x0, x1] = L.cols[c];
  const [y0, y1] = L.rows[r];
  return {x: x0 + 1.5, y: y0 + 1.5, w: x1 - x0 - 3, h: y1 - y0 - 3};
};

const CellText: React.FC<{line: Line; anchor?: 'middle' | 'start'; x?: number}> = ({line, anchor = 'middle', x}) => {
  const track = line.track ?? 0;
  const common = {
    textAnchor: anchor,
    fontFamily: FONT_SPARTAN,
    fontWeight: 700,
    fontSize: SIZE,
    letterSpacing: track,
    style: {whiteSpace: 'pre' as const},
  };
  // SVG adds the tracking after the last glyph too; shift back by half of it to stay centred.
  const tx = (x ?? line.x) - (anchor === 'middle' ? track / 2 : 0);
  return (
    <>
      <text {...common} x={tx + 2} y={line.base + 3} fill={C.cellShadow}>
        {line.text}
      </text>
      <text {...common} x={tx} y={line.base} fill={C.white}>
        {line.text}
      </text>
    </>
  );
};

/** One element sliding in from the left. */
const SlideIn: React.FC<{at: number; children: React.ReactNode}> = ({at, children}) => {
  const f = useCurrentFrame();
  const p = ramp(f, at, at + 16, Easing.bezier(0.16, 1, 0.3, 1));
  return (
    <g opacity={p} transform={`translate(${lerp(-46, 0, p)} 0)`}>
      {children}
    </g>
  );
};

/** 3–6 s: every cell box draws its border, then fills. */
const Frame: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <g>
      {L.rows.map((_, r) =>
        L.cols.map((__, c) => {
          const {x, y, w, h} = cellRect(r, c);
          const at = s(3.5) + r * 7 + c * 4;
          const draw = ramp(f, at, at + 26, Easing.inOut(Easing.cubic));
          const fill = ramp(f, at + 14, at + 40);
          return (
            <g key={`${r}-${c}`}>
              <rect x={x} y={y} width={w} height={h} fill={C.cellFill} fillOpacity={0.35 * fill} />
              <rect
                x={x}
                y={y}
                width={w}
                height={h}
                fill="none"
                stroke={C.cellStroke}
                strokeWidth={3}
                pathLength={1}
                strokeDasharray={1}
                strokeDashoffset={1 - draw}
              />
              {/* a gold spark rides the line as it draws */}
              <rect
                x={x}
                y={y}
                width={w}
                height={h}
                fill="none"
                stroke={C.gold}
                strokeWidth={3}
                pathLength={1}
                strokeDasharray="0.04 0.96"
                strokeDashoffset={1.04 - draw}
                opacity={draw > 0 && draw < 1 ? 1 : 0}
                filter="url(#goldGlow)"
              />
            </g>
          );
        }),
      )}
    </g>
  );
};

/** Gold border flash on a cell when its content lands. */
const CellFlash: React.FC<{r: number; c: number; at: number; strength?: number}> = ({r, c, at, strength = 0.9}) => {
  const f = useCurrentFrame();
  const {x, y, w, h} = cellRect(r, c);
  const o = bump(f, at, at + 8, at + 30) * strength;
  if (o <= 0) return null;
  return (
    <rect x={x} y={y} width={w} height={h} fill="rgba(255,200,90,0.06)" stroke={C.gold} strokeWidth={3} opacity={o} filter="url(#goldGlow)" />
  );
};

const RowContent: React.FC<{index: number}> = ({index}) => {
  const row = ROWS[index];
  const start = s(row.start) + 6;
  return (
    <g>
      {row.cells.map((lines, c) => {
        const at = start + c * CELL_STAGGER;
        return (
          <g key={c}>
            <CellFlash r={index} c={c} at={at + 4} />
            {lines.map((line, k) => (
              <SlideIn key={k} at={at + k * LINE_STAGGER}>
                <CellText line={line} />
              </SlideIn>
            ))}
          </g>
        );
      })}
    </g>
  );
};

/** Knight row, third cell: "+ 10% off" with the 10% popping in gold. */
const KnightOffer: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const at = s(T.knight) + 6 + 2 * CELL_STAGGER;
  // Widths at 39px League Spartan: "+ " 31, "+ 10%" 98.1, full 155.9; centre 829.5.
  const x0 = 829.5 - 155.9 / 2;
  const popAt = at + 18;
  const pop = spring({frame: f - popAt, fps, config: {damping: 7, stiffness: 160, mass: 0.6}});
  const flash = bump(f, popAt, popAt + 6, popAt + 34);
  const scale = f < popAt ? 0 : lerp(0, 1, pop) + flash * 0.25;
  const cx = x0 + 31 + 67.1 / 2;
  const base = 446;
  return (
    <g>
      <CellFlash r={1} c={2} at={at + 4} />
      <SlideIn at={at}>
        <CellText line={{text: '+ ', x: x0, base}} anchor="start" />
        <CellText line={{text: ' off', x: x0 + 98.1, base}} anchor="start" />
      </SlideIn>
      <g style={{transformOrigin: `${cx}px ${base - 14}px`, transform: `scale(${scale})`}}>
        <text
          x={cx}
          y={base}
          textAnchor="middle"
          fontFamily={FONT_SPARTAN}
          fontWeight={700}
          fontSize={SIZE}
          fill={C.gold}
          opacity={flash}
          filter="url(#goldGlowBig)"
        >
          10%
        </text>
        <CellText line={{text: '10%', x: cx, base}} />
        <text x={cx} y={base} textAnchor="middle" fontFamily={FONT_SPARTAN} fontWeight={700} fontSize={SIZE} fill={C.goldLight} opacity={flash * 0.9}>
          10%
        </text>
      </g>
    </g>
  );
};

/** Royal row: the whole row's border pulses gold through the climax. */
const RoyalPulse: React.FC = () => {
  const f = useCurrentFrame();
  const [y0, y1] = L.rows[3];
  const x0 = L.cols[0][0];
  const x1 = L.cols[2][1];
  const env = ramp(f, s(21.5), s(22.2)) * (1 - ramp(f, s(25.2), s(26)));
  const beat = 0.55 + 0.45 * Math.cos(((f - s(21.5)) / 30) * Math.PI * 2 * (100 / 60 / 2)); // half-time with the 100 BPM score
  const o = env * beat;
  if (o <= 0.001) return null;
  return (
    <g opacity={o}>
      <rect x={x0 - 2} y={y0 - 2} width={x1 - x0 + 4} height={y1 - y0 + 4} fill="none" stroke={C.gold} strokeWidth={5} filter="url(#goldGlowBig)" />
      <rect x={x0 - 2} y={y0 - 2} width={x1 - x0 + 4} height={y1 - y0 + 4} fill="none" stroke={C.goldLight} strokeWidth={2.5} />
    </g>
  );
};

export const Table: React.FC = () => (
  <AbsoluteFill>
    <svg width={WIDTH} height={HEIGHT} style={{position: 'absolute', inset: 0, overflow: 'visible'}}>
      <defs>
        <filter id="goldGlow" x="-10%" y="-10%" width="120%" height="120%">
          <feGaussianBlur stdDeviation="3" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="goldGlowBig" x="-20%" y="-40%" width="140%" height="180%">
          <feGaussianBlur stdDeviation="7" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <Frame />
      <ScholarRow />
      <KnightRow />
      <NobleRow />
      <RoyalRow />
    </svg>
  </AbsoluteFill>
);

/** 6–11 s */
export const ScholarRow: React.FC = () => <RowContent index={0} />;
/** 11–16 s */
export const KnightRow: React.FC = () => (
  <>
    <RowContent index={1} />
    <KnightOffer />
  </>
);
/** 16–21 s */
export const NobleRow: React.FC = () => <RowContent index={2} />;
/** 21–26 s */
export const RoyalRow: React.FC = () => (
  <>
    <RoyalPulse />
    <RowContent index={3} />
  </>
);

