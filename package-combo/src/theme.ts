import {Easing, interpolate} from 'remotion';
import layout from '../public/layout.json';

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1440;
export const DURATION = 900;

export const s = (seconds: number) => Math.round(seconds * FPS);

// Colours sampled from poster.png
export const C = {
  navyDeep: '#08102b',
  cellFill: 'rgb(19, 8, 134)',
  cellStroke: '#4a65aa',
  cellShadow: '#4a3f1f',
  titleShadow: '#091e5b',
  white: '#ffffff',
  gold: '#f6c453',
  goldLight: '#ffe7a3',
  goldDeep: '#c8901e',
  cardRed: '#970c10',
};

export const FONT_SPARTAN = 'League Spartan';
export const FONT_POPPINS = 'Poppins';

export const L = layout as unknown as {
  cols: [number, number][];
  rows: [number, number][];
  card: [number, number, number, number, number];
  bar: [number, number, number, number, number];
  pieces: Record<string, [number, number, number, number]>;
  chars: Record<string, [number, number, number, number]>;
  logo: [number, number, number, number];
  header: [number, number, number, number];
};

// Section start times (seconds), straight from the brief
export const T = {
  intro: 0,
  title: 3,
  scholar: 6,
  knight: 11,
  noble: 16,
  royal: 21,
  card: 26,
  bar: 28,
  hold: 29.2,
};

const clampOpts = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** 0→1 between two frames with an ease. */
export const ramp = (
  frame: number,
  from: number,
  to: number,
  ease: (t: number) => number = Easing.bezier(0.22, 1, 0.36, 1),
) => interpolate(frame, [from, to], [0, 1], {...clampOpts, easing: ease});

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** Smooth 0→1→0 bump, used for one-off glows and flashes. */
export const bump = (frame: number, from: number, peak: number, to: number) =>
  interpolate(frame, [from, peak, to], [0, 1, 0], {
    ...clampOpts,
    easing: Easing.inOut(Easing.sin),
  });

/** Effects that wobble (flicker, parallax) settle to exactly zero for the final hold. */
export const settle = (frame: number) => 1 - ramp(frame, s(27.5), s(T.hold), Easing.inOut(Easing.cubic));
