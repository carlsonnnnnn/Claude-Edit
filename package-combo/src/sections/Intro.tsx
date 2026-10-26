import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame} from 'remotion';
import {L, bump, lerp, ramp, s, settle} from '../theme';

/** 0–3 s: logo and "Studyolution Academy" fade in with a warm halo. */
export const Intro: React.FC = () => {
  const f = useCurrentFrame();
  const [lx, ly, lw, lh] = L.logo;
  const [hx, hy, hw, hh] = L.header;

  const logoIn = ramp(f, s(0.4), s(1.6));
  const textIn = ramp(f, s(1.0), s(2.3));
  const halo = 0.35 * bump(f, s(0.4), s(1.6), s(4)) + 0.12 * settle(f) * ramp(f, s(1.6), s(3));

  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: lx + lw / 2 - 90,
          top: ly + lh / 2 - 90,
          width: 180,
          height: 180,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255,200,90,0.9) 0%, rgba(255,170,60,0.35) 35%, rgba(255,160,60,0) 70%)',
          opacity: halo,
          mixBlendMode: 'screen',
        }}
      />
      <Img
        src={staticFile('logo.png')}
        style={{
          position: 'absolute',
          left: lx,
          top: ly,
          width: lw,
          height: lh,
          opacity: logoIn,
          transform: `scale(${lerp(0.82, 1, logoIn)}) rotate(${lerp(-25, 0, logoIn)}deg)`,
          filter: `blur(${lerp(6, 0, logoIn)}px)`,
        }}
      />
      <Img
        src={staticFile('header.png')}
        style={{
          position: 'absolute',
          left: hx,
          top: hy,
          width: hw,
          height: hh,
          opacity: textIn,
          transform: `translateX(${lerp(-24, 0, textIn)}px)`,
          filter: `blur(${lerp(4, 0, textIn)}px)`,
        }}
      />
    </AbsoluteFill>
  );
};
