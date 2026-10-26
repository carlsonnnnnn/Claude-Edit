import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, FONT_SPARTAN, HEIGHT, WIDTH, bump, lerp, ramp, s} from '../theme';

// Measured on the poster: ink spans x 267–814, cap top 175, baseline ≈ 236.
const CX = 539;
const BASE = 236;
const SIZE = 88;
const TRACK = -4.6;

/** 3–6 s: "Package Combo" bounces in, then a gold shine sweeps across it. */
export const Title: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const start = s(3);
  const pop = spring({frame: f - start, fps, config: {damping: 9, stiffness: 120, mass: 0.8}});
  const opacity = ramp(f, start, start + 8);
  const scale = lerp(0.25, 1, pop);

  // shine band travels left → right across the word
  const shine = ramp(f, s(3.9), s(4.9), (t) => t);
  const bandX = lerp(180, 900, shine);
  const shineOn = bump(f, s(3.85), s(4.4), s(5.0));
  const glow = bump(f, s(3.0), s(3.6), s(5.5));

  const textProps = {
    x: CX,
    y: BASE,
    textAnchor: 'middle' as const,
    fontFamily: FONT_SPARTAN,
    fontWeight: 700,
    fontSize: SIZE,
    letterSpacing: TRACK,
  };

  return (
    <AbsoluteFill style={{opacity}}>
      <svg
        width={WIDTH}
        height={HEIGHT}
        style={{position: 'absolute', inset: 0, overflow: 'visible'}}
      >
        <defs>
          <linearGradient id="titleShine" gradientUnits="userSpaceOnUse" x1={bandX - 90} y1={150} x2={bandX + 90} y2={260}>
            <stop offset="0" stopColor={C.goldLight} stopOpacity="0" />
            <stop offset="0.45" stopColor={C.goldLight} stopOpacity="1" />
            <stop offset="0.55" stopColor="#ffffff" stopOpacity="1" />
            <stop offset="1" stopColor={C.goldLight} stopOpacity="0" />
          </linearGradient>
          <filter id="titleShadowBlur" x="-10%" y="-30%" width="120%" height="160%">
            <feGaussianBlur stdDeviation="1.6" />
          </filter>
          <filter id="titleGlow" x="-20%" y="-60%" width="140%" height="220%">
            <feGaussianBlur stdDeviation="14" />
          </filter>
        </defs>
        <g style={{transformOrigin: `${CX}px ${BASE - 30}px`, transform: `scale(${scale})`}}>
          <text {...textProps} fill={C.gold} opacity={glow * 0.55} filter="url(#titleGlow)">
            Package Combo
          </text>
          <text {...textProps} x={CX + 12} y={BASE + 14} fill={C.titleShadow} opacity={0.35} filter="url(#titleShadowBlur)">
            Package Combo
          </text>
          <text {...textProps} x={CX + 6} y={BASE + 7} fill={C.titleShadow} opacity={0.9} filter="url(#titleShadowBlur)">
            Package Combo
          </text>
          <text {...textProps} fill={C.white}>
            Package Combo
          </text>
          <text {...textProps} fill="url(#titleShine)" opacity={shineOn}>
            Package Combo
          </text>
        </g>
      </svg>
    </AbsoluteFill>
  );
};
