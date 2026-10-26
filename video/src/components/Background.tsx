import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { easeInOut, prog } from "../anim";
import { C } from "../theme";

// Poster background (content removed) with a slow drift that never stops,
// a diagonal light sweep on the intro and a faint recurring one after.
export const Background: React.FC = () => {
  const f = useCurrentFrame();
  const fadeIn = prog(f, 0, 36);
  const dx = Math.sin(f / 170) * 5 + Math.sin(f / 61) * 1.2;
  const dy = Math.cos(f / 210) * 4;
  const scale = 1.018 + Math.sin(f / 260) * 0.006;

  // Intro sweep: a wide soft band travelling top-left -> bottom-right.
  const sweep = interpolate(f, [10, 95], [-0.45, 1.45], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeInOut });
  const sweepAlpha = interpolate(f, [10, 30, 80, 95], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // Later: a very faint band every 9 s keeps the backdrop alive.
  const cyc = ((f - 95) % 270) / 270;
  const slow = f > 95 ? -0.45 + cyc * 1.9 : -1;
  const slowAlpha = f > 95 ? Math.sin(Math.PI * cyc) * 0.35 : 0;

  const band = (pos: number, alpha: number, width: number) => (
    <AbsoluteFill
      style={{
        background: `linear-gradient(120deg, transparent ${(pos - width) * 100}%, rgba(140, 200, 255, ${0.28 * alpha}) ${pos * 100}%, transparent ${(pos + width) * 100}%)`,
        mixBlendMode: "screen",
      }}
    />
  );

  return (
    <AbsoluteFill style={{ backgroundColor: C.deep, overflow: "hidden" }}>
      <AbsoluteFill style={{ opacity: fadeIn }}>
        <Img
          src={staticFile("bg.png")}
          style={{
            width: 1080,
            height: 1440,
            transform: `translate(${dx}px, ${dy}px) scale(${scale})`,
            transformOrigin: "50% 45%",
          }}
        />
        {/* Grid shimmer: brightness breathes very slightly. */}
        <AbsoluteFill
          style={{
            background: "radial-gradient(ellipse 70% 45% at 50% 55%, rgba(80,140,230,0.10), transparent 70%)",
            opacity: 0.6 + Math.sin(f / 45) * 0.4,
            mixBlendMode: "screen",
          }}
        />
        {band(sweep, sweepAlpha, 0.18)}
        {band(slow, slowAlpha, 0.22)}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
