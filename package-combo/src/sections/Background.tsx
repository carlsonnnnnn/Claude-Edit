import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame} from 'remotion';
import {C, HEIGHT, WIDTH, ramp, s} from '../theme';

// Grid measured on the poster: vertical lines every 27.345px from x=20,
// horizontal every 29.77px from y=6.4.
const GX0 = 20;
const GPX = 27.345;
const GY0 = 6.4;
const GPY = 29.77;

const vLines = Array.from({length: Math.ceil(WIDTH / GPX) + 1}, (_, i) => GX0 + i * GPX - GPX);
const hLines = Array.from({length: Math.ceil(HEIGHT / GPY) + 1}, (_, i) => GY0 + i * GPY);

/** 0–3 s: navy plate with its faint grid fades up; afterwards a slow shimmer keeps it alive. */
export const Background: React.FC = () => {
  const f = useCurrentFrame();
  const fadeIn = ramp(f, 0, s(1.2));
  const t = f / 30;

  // A shimmer band that crawls diagonally along the grid lines, forever.
  const band = ((t * 90) % (WIDTH + HEIGHT + 600)) - 300;
  // A soft light pool drifting behind the table.
  const lx = 540 + Math.sin(t * 0.35) * 220;
  const ly = 560 + Math.cos(t * 0.27) * 160;

  return (
    <AbsoluteFill style={{backgroundColor: C.navyDeep}}>
      <AbsoluteFill style={{opacity: fadeIn}}>
        <Img src={staticFile('plate.png')} style={{width: WIDTH, height: HEIGHT}} />
        {/* softened horizon until the throne covers it, then the exact poster plate */}
        <Img
          src={staticFile('plate_early.png')}
          style={{position: 'absolute', inset: 0, width: WIDTH, height: HEIGHT, opacity: 1 - ramp(f, s(21.2), s(22.6))}}
        />
        <AbsoluteFill
          style={{
            background: `radial-gradient(520px 420px at ${lx}px ${ly}px, rgba(120,160,255,0.10), rgba(120,160,255,0) 70%)`,
            mixBlendMode: 'screen',
          }}
        />
        <svg width={WIDTH} height={HEIGHT} style={{position: 'absolute', inset: 0}}>
          <defs>
            <linearGradient id="gridBand" gradientUnits="userSpaceOnUse" x1={band - 260} y1={0} x2={band + 260} y2={260}>
              <stop offset="0" stopColor="#fff" stopOpacity="0" />
              <stop offset="0.5" stopColor="#fff" stopOpacity="1" />
              <stop offset="1" stopColor="#fff" stopOpacity="0" />
            </linearGradient>
            <mask id="gridMask">
              <rect width={WIDTH} height={HEIGHT} fill="url(#gridBand)" />
            </mask>
          </defs>
          <g mask="url(#gridMask)" stroke="rgba(150,185,255,0.22)" strokeWidth={1.2}>
            {vLines.map((x) => (
              <line key={`v${x}`} x1={x} y1={0} x2={x} y2={HEIGHT} />
            ))}
            {hLines.map((y) => (
              <line key={`h${y}`} x1={0} y1={y} x2={WIDTH} y2={y} />
            ))}
          </g>
        </svg>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
