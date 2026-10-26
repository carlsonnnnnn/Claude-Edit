import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { prog, soft, T } from "../anim";
import { TUTOR_BOX, TUTOR_DEPTH, TUTORS } from "../theme";
import { Layer, TEXT_SHADOW, Txt } from "../text";

const WAVE_GAP = 16; // frames between centre, inner pair and outer pair

const start = (wave: number) => T.tutors + 4 + wave * WAVE_GAP;

export const Tutors: React.FC = () => {
  const f = useCurrentFrame();
  const B = TUTOR_BOX;
  // Until the table arrives the busts fade out at the bottom (the poster's
  // table and title hide the painted-over area underneath).
  const fadePx = interpolate(f, [T.table, T.table + 30], [90, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const mask = `linear-gradient(to bottom, black 0px, black ${B.h - fadePx}px, transparent ${B.h + 0.01}px)`;

  return (
    <AbsoluteFill>
      {/* Busts rise from behind the line where the table top will sit. */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: 1080,
          height: B.y + B.h,
          overflow: "hidden",
        }}
      >
        {TUTOR_DEPTH.map((id) => {
          const t = TUTORS.find((x) => x.id === id)!;
          const s = soft(f, start(t.wave), 30, 14, 1);
          return (
            <Img
              key={id}
              src={staticFile(`tutor_${id}.png`)}
              style={{
                position: "absolute",
                left: B.x,
                top: B.y,
                width: B.w,
                height: B.h,
                transform: `translateY(${(1 - s) * 270}px)`,
                opacity: Math.min(1, s * 1.8),
                WebkitMaskImage: mask,
                maskImage: mask,
              }}
            />
          );
        })}
      </div>
      <Layer>
        {TUTORS.map((t) => {
          const p = prog(f, start(t.wave) + 14, 16);
          return (
            <g key={t.id} opacity={p} transform={`translate(0 ${(1 - p) * 10})`} style={{ filter: TEXT_SHADOW }}>
              {t.lines.map((line, i) => (
                <Txt key={i} t="label" x={t.cx} y={t.baselines[i]}>
                  {line}
                </Txt>
              ))}
            </g>
          );
        })}
      </Layer>
    </AbsoluteFill>
  );
};
