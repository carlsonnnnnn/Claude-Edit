import React from 'react';
import {AbsoluteFill, Easing, Img, staticFile, useCurrentFrame} from 'remotion';
import {C, HEIGHT, T, WIDTH, bump, lerp, ramp, s, settle} from '../theme';

type Name = 'scholar' | 'knight' | 'noble' | 'king';

const RISE = s(1.5);
const riseEase = Easing.bezier(0.16, 1, 0.3, 1);

/** Candle-like flicker: a few incommensurate sines, never a random jump. */
const flicker = (t: number, seed: number) =>
  0.5 * Math.sin(t * 7.3 + seed) + 0.3 * Math.sin(t * 12.9 + seed * 2.1) + 0.2 * Math.sin(t * 21.7 + seed * 3.7);

/**
 * A character cut-out. It only ever translates (rise-in and a slow parallax drift),
 * scales uniformly about its base, and gets light effects — the art is never warped.
 */
const Character: React.FC<{
  name: Name;
  at: number;
  depth: number;
  seed: number;
  startScale?: number;
  origin: string;
  children?: React.ReactNode;
}> = ({name, at, depth, seed, startScale = 1, origin, children}) => {
  const f = useCurrentFrame();
  const t = f / 30;
  const p = ramp(f, at, at + RISE, riseEase);
  if (p <= 0) return null;
  const k = settle(f);
  const dx = Math.sin(t * 0.21 + seed) * 7 * depth * k;
  const dy = lerp(190, 0, p) + Math.sin(t * 0.17 + seed * 2) * 2.5 * depth * k;
  const scale = lerp(startScale, 1, ramp(f, at, at + RISE + 12, Easing.inOut(Easing.cubic)));
  const bright = 1 + 0.035 * flicker(t, seed) * k;
  return (
    <AbsoluteFill
      style={{
        opacity: ramp(f, at, at + RISE * 0.6),
        transform: `translate(${dx}px, ${dy}px) scale(${scale})`,
        transformOrigin: origin,
        filter: `brightness(${bright})`,
      }}
    >
      <Img src={staticFile(`char_${name}.png`)} style={{width: WIDTH, height: HEIGHT}} />
      {children}
    </AbsoluteFill>
  );
};

/** Light that only lands on a character: a gradient clipped by the cut-out's own alpha. */
const MaskedLight: React.FC<{name: Name; background: string; opacity: number; blend?: string}> = ({
  name,
  background,
  opacity,
  blend = 'screen',
}) => {
  if (opacity <= 0.001) return null;
  const mask = `url(${staticFile(`char_${name}.png`)})`;
  return (
    <AbsoluteFill
      style={{
        background,
        opacity,
        mixBlendMode: blend as React.CSSProperties['mixBlendMode'],
        WebkitMaskImage: mask,
        maskImage: mask,
        WebkitMaskSize: `${WIDTH}px ${HEIGHT}px`,
        maskSize: `${WIDTH}px ${HEIGHT}px`,
      }}
    />
  );
};

const Candle: React.FC<{name: Name; o: number}> = ({name, o}) => (
  <MaskedLight
    name={name}
    background="radial-gradient(900px 600px at 540px 1250px, rgba(255,150,60,1), rgba(255,150,60,0) 75%)"
    opacity={o}
    blend="soft-light"
  />
);

const Glow: React.FC<{x: number; y: number; r: number; color: string; opacity: number}> = ({x, y, r, color, opacity}) =>
  opacity <= 0.001 ? null : (
    <div
      style={{
        position: 'absolute',
        left: x - r,
        top: y - r,
        width: r * 2,
        height: r * 2,
        borderRadius: '50%',
        background: `radial-gradient(circle, ${color} 0%, rgba(0,0,0,0) 70%)`,
        opacity,
        mixBlendMode: 'screen',
      }}
    />
  );

/** Four-point star used for the crown sparkle. */
const Sparkle: React.FC<{x: number; y: number; size: number; o: number; rot: number}> = ({x, y, size, o, rot}) =>
  o <= 0.001 ? null : (
    <svg
      width={size * 2}
      height={size * 2}
      viewBox="-1 -1 2 2"
      style={{position: 'absolute', left: x - size, top: y - size, opacity: o, transform: `rotate(${rot}deg) scale(${0.4 + o * 0.6})`}}
    >
      <defs>
        <radialGradient id="spk">
          <stop offset="0" stopColor="#fff" />
          <stop offset="0.4" stopColor={C.goldLight} />
          <stop offset="1" stopColor={C.gold} stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle r="0.55" fill="url(#spk)" opacity="0.8" />
      <path d="M0,-1 C0.08,-0.08 0.08,-0.08 1,0 C0.08,0.08 0.08,0.08 0,1 C-0.08,0.08 -0.08,0.08 -1,0 C-0.08,-0.08 -0.08,-0.08 0,-1Z" fill="#fffbe8" />
    </svg>
  );

/** 21 s: gold light bursts behind the throne. */
const ThroneBurst: React.FC = () => {
  const f = useCurrentFrame();
  const at = s(T.royal);
  const burst = bump(f, at + 4, at + 22, at + 110);
  const rest = 0.28 * ramp(f, at + 30, at + 70) * settle(f);
  const o = Math.max(burst, rest);
  if (o <= 0.001) return null;
  const rot = ((f - at) / 30) * 6;
  const cx = 360;
  const cy = 975;
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen'}}>
      <div
        style={{
          position: 'absolute',
          left: cx - 520,
          top: cy - 520,
          width: 1040,
          height: 1040,
          borderRadius: '50%',
          opacity: o * 0.75,
          transform: `rotate(${rot}deg) scale(${lerp(0.6, 1.05, ramp(f, at, at + 40))})`,
          background:
            'repeating-conic-gradient(from 0deg, rgba(255,214,120,0.85) 0deg 4deg, rgba(255,214,120,0) 4deg 15deg)',
          WebkitMaskImage: 'radial-gradient(circle, #000 0%, rgba(0,0,0,0.6) 30%, transparent 68%)',
          maskImage: 'radial-gradient(circle, #000 0%, rgba(0,0,0,0.6) 30%, transparent 68%)',
        }}
      />
      <Glow x={cx} y={cy} r={360} color="rgba(255,200,100,0.95)" opacity={o} />
      <Glow x={cx} y={cy - 40} r={170} color="rgba(255,240,200,1)" opacity={burst * 0.8} />
    </AbsoluteFill>
  );
};

export const Characters: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / 30;
  const k = settle(f);

  const scholarAt = s(T.scholar) + 6;
  const knightAt = s(T.knight) + 6;
  const nobleAt = s(T.noble) + 6;
  const kingAt = s(T.royal) + 4;

  // Scholar: a warm lamp glow comes up with him and stays as a soft flicker.
  const scholarGlow =
    bump(f, scholarAt, scholarAt + 30, scholarAt + 120) * 0.9 + 0.25 * ramp(f, scholarAt + 20, scholarAt + 60) * k;
  // Knight: a metallic glint sweeps across the armour once he lands.
  const glint = ramp(f, knightAt + 34, knightAt + 62, Easing.inOut(Easing.quad));
  const glintX = lerp(-300, 360, glint);
  const glintOn = bump(f, knightAt + 32, knightAt + 48, knightAt + 64);
  // Prince: sparkles over the crown.
  const crown = [
    {x: 658, y: 880, d: 0},
    {x: 690, y: 868, d: 7},
    {x: 626, y: 893, d: 13},
    {x: 712, y: 889, d: 20},
  ];
  // Candlelight that washes over everyone.
  const candle = (0.16 + 0.05 * flicker(t, 1.3)) * ramp(f, scholarAt, scholarAt + 40) * k;

  return (
    <AbsoluteFill>
      <ThroneBurst />
      <Character name="king" at={kingAt} depth={0.6} seed={4.1} startScale={1.07} origin="360px 1300px">
        <MaskedLight
          name="king"
          background="radial-gradient(500px 420px at 360px 960px, rgba(255,215,130,1), rgba(255,215,130,0) 70%)"
          opacity={bump(f, kingAt, kingAt + 24, kingAt + 90) * 0.6}
        />
        <Candle name="king" o={candle} />
      </Character>
      <Character name="knight" at={knightAt} depth={1} seed={2.2} origin="110px 1300px">
        <MaskedLight
          name="knight"
          background={`linear-gradient(115deg, rgba(255,255,255,0) ${glintX}px, rgba(255,255,255,0.95) ${glintX + 40}px, rgba(255,236,190,0.6) ${glintX + 60}px, rgba(255,255,255,0) ${glintX + 110}px)`}
          opacity={glintOn}
        />
        <Candle name="knight" o={candle} />
      </Character>
      <Character name="noble" at={nobleAt} depth={1} seed={0.7} origin="700px 1300px">
        <Candle name="noble" o={candle} />
      </Character>
      <Glow x={960} y={1010} r={260} color="rgba(255,170,70,0.95)" opacity={scholarGlow * 0.55} />
      <Character name="scholar" at={scholarAt} depth={1.3} seed={5.5} origin="950px 1300px">
        <MaskedLight
          name="scholar"
          background="radial-gradient(420px 360px at 980px 1180px, rgba(255,170,80,0.9), rgba(255,170,80,0) 70%)"
          opacity={scholarGlow * 0.5}
        />
        <Candle name="scholar" o={candle} />
      </Character>

      {crown.map((c, i) => {
        const at = nobleAt + 30 + c.d;
        const o = bump(f, at, at + 8, at + 26) + bump(f, at + 40, at + 48, at + 66) * 0.7;
        return <Sparkle key={i} x={c.x} y={c.y} size={26 - i * 3} o={o} rot={(f - at) * 3} />;
      })}
    </AbsoluteFill>
  );
};
