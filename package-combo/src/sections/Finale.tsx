import React from 'react';
import {AbsoluteFill, Easing, Img, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {L, T, lerp, ramp, s} from '../theme';

/**
 * Dark "stage floor" over the lower frame. The poster's card and contact bar sit over the
 * bottom of the painting, so that strip is shaded until the card and bar arrive to cover it.
 */
export const Floor: React.FC = () => {
  const f = useCurrentFrame();
  const upper = 1 - ramp(f, s(T.card) + 2, s(T.card) + 22);
  const lower = 1 - ramp(f, s(T.bar) + 8, s(T.bar) + 18);
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 1060,
          height: 300,
          opacity: upper,
          background: 'linear-gradient(180deg, rgba(8,16,48,0) 0%, rgba(8,16,48,0.82) 45%, rgba(8,16,48,0.94) 100%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 1330,
          bottom: 0,
          opacity: lower,
          background: 'linear-gradient(180deg, rgba(8,16,48,0.94), rgba(8,16,48,0.97))',
        }}
      />
      {/* soften the hand-off between the two shades while both are up */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 1300,
          height: 60,
          opacity: Math.min(upper, lower),
          background: 'rgba(8,16,48,0.94)',
        }}
      />
    </AbsoluteFill>
  );
};

const Piece: React.FC<{name: string; dx?: number; opacity: number; offset?: number; scale?: number; originX?: number}> = ({
  name,
  dx = 0,
  opacity,
  offset = 0,
  scale = 1,
}) => {
  const [x0, y0, x1, y1] = L.pieces[name];
  return (
    <Img
      src={staticFile(`${name}.png`)}
      style={{
        position: 'absolute',
        left: x0 + dx,
        top: y0 + offset,
        width: x1 - x0,
        height: y1 - y0,
        opacity,
        transform: `scale(${scale})`,
      }}
    />
  );
};

/** 26–28 s: white card slides up, then the four levels appear one by one. */
export const AvailableCard: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const at = s(T.card);
  const p = spring({frame: f - at, fps, config: {damping: 15, stiffness: 110, mass: 0.9}});
  if (f < at) return null;
  const [x0, y0, x1, y1, r] = L.card;
  const dy = lerp(330, 0, p);
  const titleIn = ramp(f, at + 10, at + 22);
  const bullets = ['card_b1', 'card_b3', 'card_b2', 'card_b4'];
  return (
    <AbsoluteFill style={{transform: `translateY(${dy}px)`, opacity: ramp(f, at, at + 8)}}>
      <div
        style={{
          position: 'absolute',
          left: x0,
          top: y0,
          width: x1 - x0,
          height: y1 - y0,
          borderRadius: r,
          background: '#ffffff',
        }}
      />
      <Piece name="card_title" opacity={titleIn} offset={lerp(8, 0, titleIn)} />
      {bullets.map((b, i) => {
        const bi = ramp(f, at + 20 + i * 8, at + 32 + i * 8, Easing.bezier(0.16, 1, 0.3, 1));
        return <Piece key={b} name={b} opacity={bi} dx={lerp(-26, 0, bi)} />;
      })}
    </AbsoluteFill>
  );
};

/** 28–30 s: contact bar slides up, its icons pop in, then everything holds on the poster layout. */
export const ContactBar: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const at = s(T.bar);
  if (f < at) return null;
  const p = spring({frame: f - at, fps, config: {damping: 16, stiffness: 120, mass: 0.8}});
  const [x0, y0, x1, y1, r] = L.bar;
  const groups = ['bar_label', 'bar_email', 'bar_phone', 'bar_insta', 'bar_tiktok'];
  return (
    <AbsoluteFill style={{transform: `translateY(${lerp(120, 0, p)}px)`, opacity: ramp(f, at, at + 6)}}>
      <div
        style={{
          position: 'absolute',
          left: x0,
          top: y0,
          width: x1 - x0,
          height: y1 - y0,
          borderRadius: r,
          background: '#ffffff',
        }}
      />
      {groups.map((g, i) => {
        const gi = spring({frame: f - (at + 6 + i * 3), fps, config: {damping: 11, stiffness: 170, mass: 0.6}});
        return <Piece key={g} name={g} opacity={Math.min(1, gi * 1.4)} scale={lerp(0.6, 1, Math.min(gi, 1.15))} />;
      })}
    </AbsoluteFill>
  );
};
