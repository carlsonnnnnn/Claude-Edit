import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { bouncy, prog, soft, T } from "../anim";
import { C } from "../theme";
import { Layer, Txt } from "../text";

// Raised 2px from the poster position to stay inside the 40px safe margin.
const LIFT = -2;
const BAR = { x: 66, y: 1354, w: 926, h: 46 };
const BASE = 1381;

const MailIcon: React.FC<{ cx: number; cy: number }> = ({ cx, cy }) => (
  <g>
    <circle cx={cx} cy={cy} r={14} fill={C.contact} />
    <rect x={cx - 8} y={cy - 6} width={16} height={12} rx={2} fill="#fff" />
    <path d={`M ${cx - 6.6} ${cy - 4} L ${cx} ${cy + 0.9} L ${cx + 6.6} ${cy - 4}`} fill="none" stroke={C.contact} strokeWidth={1.6} strokeLinejoin="round" strokeLinecap="round" />
  </g>
);

const PhoneIcon: React.FC<{ cx: number; cy: number }> = ({ cx, cy }) => (
  <g>
    <circle cx={cx} cy={cy} r={14} fill={C.contact} />
    <path
      transform={`translate(${cx - 8.6} ${cy - 8.6}) scale(0.72)`}
      d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1L6.6 10.8z"
      fill="#fff"
    />
  </g>
);

const InstagramIcon: React.FC<{ cx: number; cy: number }> = ({ cx, cy }) => (
  <g fill="none" stroke={C.contact}>
    <rect x={cx - 11.5} y={cy - 11.5} width={23} height={23} rx={6.5} strokeWidth={2.4} />
    <circle cx={cx} cy={cy} r={5.4} strokeWidth={2.4} />
    <circle cx={cx + 6.2} cy={cy - 6.2} r={1.5} fill={C.contact} stroke="none" />
  </g>
);

const TikTokIcon: React.FC<{ cx: number; cy: number }> = ({ cx, cy }) => (
  <g>
    <circle cx={cx} cy={cy} r={13} fill={C.contact} />
    <path
      transform={`translate(${cx - 6.6} ${cy - 7.4}) scale(0.62)`}
      d="M16.6 5.8a4.3 4.3 0 0 1-3.3-3.8V1.6H10v13.7a2.9 2.9 0 1 1-2-2.7V9.2a6.2 6.2 0 1 0 5.3 6.1V8.6a7.5 7.5 0 0 0 4.4 1.4V6.7a4.3 4.3 0 0 1-1.1-.9z"
      fill="#fff"
    />
  </g>
);

const ITEMS: { icon?: React.ReactNode; text: string; x: number }[] = [
  { text: "More information:", x: 82 },
  { icon: <MailIcon cx={232.5} cy={1376.5} />, text: "studyolution@gmail.com", x: 254 },
  { icon: <PhoneIcon cx={453} cy={1376} />, text: "+60 14-803 4579 (Sir Isaac)", x: 475 },
  { icon: <InstagramIcon cx={703.5} cy={1376.5} />, text: "@studyolution", x: 724 },
  { icon: <TikTokIcon cx={845.5} cy={1376} />, text: "@studyolution", x: 869 },
];

const ICON_X = [0, 232.5, 453, 703.5, 845.5];

export const ContactBar: React.FC = () => {
  const f = useCurrentFrame();
  if (f < T.contact) return null;
  const s = soft(f, T.contact, 30, 16, 0.9);
  return (
    <Layer>
      <g opacity={Math.min(1, s * 1.6)} transform={`translate(0 ${(1 - s) * 90 + LIFT})`}>
        <rect
          x={BAR.x}
          y={BAR.y}
          width={BAR.w}
          height={BAR.h}
          rx={BAR.h / 2}
          fill={C.white}
          style={{ filter: "drop-shadow(0 4px 10px rgba(0, 10, 40, 0.3))" }}
        />
        {ITEMS.map((it, i) => {
          const start = T.contact + 6 + i * 5;
          const p = prog(f, start, 12);
          const pop = bouncy(f, start);
          return (
            <g key={i} opacity={p}>
              {it.icon && (
                <g
                  style={{
                    transformBox: "view-box",
                    transformOrigin: `${ICON_X[i]}px 1376px`,
                    transform: `scale(${interpolate(pop, [0, 1], [0.3, 1])})`,
                  }}
                >
                  {it.icon}
                </g>
              )}
              <g transform={`translate(${(1 - p) * 10} 0)`}>
                <Txt t="contact" x={it.x} y={BASE} anchor="start" fill={C.contact}>
                  {it.text}
                </Txt>
              </g>
            </g>
          );
        })}
      </g>
    </Layer>
  );
};
