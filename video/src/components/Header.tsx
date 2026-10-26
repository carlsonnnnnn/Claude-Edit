import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { prog, soft, T } from "../anim";
import { LOGO } from "../theme";
import { Layer, TEXT_SHADOW, Txt } from "../text";

export const Header: React.FC = () => {
  const f = useCurrentFrame();
  const s1 = soft(f, T.header);
  const s2 = soft(f, T.header + 10);
  const size = (LOGO.r + 2) * 2 + 1;
  return (
    <AbsoluteFill>
      <Img
        src={staticFile("logo.png")}
        style={{
          position: "absolute",
          left: LOGO.cx - size / 2,
          top: LOGO.cy - size / 2,
          width: size,
          height: size,
          opacity: prog(f, T.header, 18),
          transform: `scale(${interpolate(s1, [0, 1], [0.55, 1])}) rotate(${interpolate(s1, [0, 1], [-25, 0])}deg)`,
          filter: `drop-shadow(0 0 ${interpolate(s1, [0, 0.6, 1], [0, 14, 4])}px rgba(120, 190, 255, 0.55))`,
        }}
      />
      <Layer>
        <g
          opacity={prog(f, T.header + 10, 18)}
          style={{
            transformBox: "fill-box",
            transformOrigin: "0% 60%",
            transform: `translateX(${interpolate(s2, [0, 1], [-14, 0])}px) scale(${interpolate(s2, [0, 1], [0.86, 1])})`,
            filter: TEXT_SHADOW,
          }}
        >
          <Txt t="brand" x={564.5} y={81} anchor="middle">
            Studyolution Academy
          </Txt>
        </g>
      </Layer>
    </AbsoluteFill>
  );
};
