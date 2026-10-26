import { Easing, interpolate, spring } from "remotion";
import { FPS } from "./theme";

export const sec = (s: number) => Math.round(s * FPS);

// Scene start frames (see README timeline).
export const T = {
  header: 12,
  tutors: sec(3),
  title: sec(8),
  table: sec(10),
  group: [sec(10.6), sec(15), sec(20)],
  pulse: sec(23.6),
  card: sec(25),
  contact: sec(28),
};

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const easeOut = Easing.bezier(0.215, 0.61, 0.355, 1); // easeOutCubic
export const easeInOut = Easing.bezier(0.645, 0.045, 0.355, 1);

/** 0..1 progress over [start, start + dur] with easeOutCubic. */
export const prog = (frame: number, start: number, dur: number, ease = easeOut) =>
  interpolate(frame, [start, start + dur], [0, 1], { ...clamp, easing: ease });

/** Soft spring that settles without visible wobble. */
export const soft = (frame: number, start: number, fps = FPS, damping = 15, mass = 0.9) =>
  spring({ frame: frame - start, fps, config: { damping, mass, stiffness: 110 } });

/** Spring with a little overshoot, for punchy entrances. */
export const bouncy = (frame: number, start: number, fps = FPS) =>
  spring({ frame: frame - start, fps, config: { damping: 9, mass: 0.7, stiffness: 140 } });

export const mix = (a: number, b: number, t: number) => a + (b - a) * t;
