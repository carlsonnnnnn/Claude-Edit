import React from 'react';
import {AbsoluteFill, random, useCurrentFrame} from 'remotion';
import {HEIGHT, WIDTH, ramp, s} from '../theme';

type Mote = {x: number; y: number; r: number; speed: number; sway: number; phase: number; tw: number};

const makeMotes = (seed: string, n: number, rMin: number, rMax: number): Mote[] =>
  Array.from({length: n}, (_, i) => ({
    x: random(`${seed}x${i}`) * WIDTH,
    y: random(`${seed}y${i}`) * HEIGHT,
    r: rMin + random(`${seed}r${i}`) * (rMax - rMin),
    speed: 14 + random(`${seed}s${i}`) * 26, // px per second, upward
    sway: 6 + random(`${seed}w${i}`) * 18,
    phase: random(`${seed}p${i}`) * Math.PI * 2,
    tw: 0.6 + random(`${seed}t${i}`) * 1.4,
  }));

const BACK = makeMotes('back', 46, 1.0, 2.4);
const FRONT = makeMotes('front', 22, 1.8, 3.6);

/** Slow gold dust drifting upward for the whole film. `layer` picks the depth pass. */
export const GoldDust: React.FC<{layer: 'back' | 'front'}> = ({layer}) => {
  const f = useCurrentFrame();
  const t = f / 30;
  const motes = layer === 'back' ? BACK : FRONT;
  const fadeIn = ramp(f, s(0.3), s(2.2));
  const span = HEIGHT + 80;

  return (
    <AbsoluteFill style={{pointerEvents: 'none', opacity: fadeIn * (layer === 'back' ? 0.85 : 0.75)}}>
      {motes.map((m, i) => {
        const y = ((((m.y - t * m.speed) % span) + span) % span) - 40;
        const x = m.x + Math.sin(t * 0.6 + m.phase) * m.sway;
        const twinkle = 0.45 + 0.55 * (0.5 + 0.5 * Math.sin(t * m.tw * 2.2 + m.phase * 3));
        const d = m.r * 2;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x - m.r,
              top: y - m.r,
              width: d,
              height: d,
              borderRadius: '50%',
              opacity: twinkle,
              background: 'radial-gradient(circle, #fff6d6 0%, #ffd36b 45%, rgba(255,190,70,0) 100%)',
              boxShadow: `0 0 ${m.r * 3}px ${m.r * 0.8}px rgba(255, 196, 80, 0.45)`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
