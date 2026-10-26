import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { bouncy, prog, T } from "../anim";
import { Layer, Txt } from "../text";

const CX = 528.5;
const BASELINE = 385;

export const Title: React.FC = () => {
  const f = useCurrentFrame();
  const s = bouncy(f, T.title);
  const scale = interpolate(s, [0, 1], [0.35, 1]);
  // Glow flares on impact and settles back to the poster's navy shadow.
  const glow = interpolate(f, [T.title + 4, T.title + 12, T.title + 50], [0, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const shadow = `drop-shadow(5px 6px 2.5px rgba(15, 27, 66, 0.92))`;
  const halo = glow > 0.001 ? ` drop-shadow(0 0 ${6 + glow * 16}px rgba(130, 200, 255, ${glow * 0.9}))` : "";
  return (
    <Layer>
      <g
        opacity={prog(f, T.title, 7)}
        style={{
          transformBox: "view-box",
          transformOrigin: `${CX}px ${BASELINE - 22}px`,
          transform: `scale(${scale})`,
          filter: shadow + halo,
        }}
      >
        <Txt t="title" x={CX} y={BASELINE}>
          Subjects Offered
        </Txt>
      </g>
    </Layer>
  );
};
