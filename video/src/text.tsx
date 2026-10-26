import React from "react";
import { C, FONT } from "./theme";

// Type styles fitted to the poster's text boxes (Outfit is the closest free
// match to the poster face; the poster sets it a little tighter).
export const TYPE = {
  body: { size: 24.5, weight: 700, ls: -1.3, ws: 3 },
  title: { size: 66.5, weight: 700, ls: -5.9, ws: 8 },
  label: { size: 17.6, weight: 700, ls: -0.55, ws: 1.5 },
  brand: { size: 27.5, weight: 600, ls: 0.85, ws: 0 },
  cardHead: { size: 31.5, weight: 700, ls: -1.2, ws: 2 },
  bullet: { size: 24.5, weight: 700, ls: -1.0, ws: 2.5 },
  contact: { size: 15.6, weight: 700, ls: -0.2, ws: 0.5 },
} as const;
export type TypeName = keyof typeof TYPE;

let ctx: CanvasRenderingContext2D | null = null;
/** Advance width of an SVG text run (letter-spacing is added after every glyph, word-spacing after every space). */
export const measure = (text: string, t: TypeName) => {
  const s = TYPE[t];
  if (!ctx) ctx = document.createElement("canvas").getContext("2d");
  ctx!.font = `${s.weight} ${s.size}px ${FONT}`;
  return ctx!.measureText(text).width + s.ls * [...text].length + s.ws * (text.split(" ").length - 1);
};

type TextProps = {
  t: TypeName;
  x: number;
  y: number; // baseline
  anchor?: "start" | "middle" | "end";
  fill?: string;
  opacity?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
};

export const Txt: React.FC<TextProps> = ({ t, x, y, anchor = "middle", fill = C.white, opacity, children, style }) => {
  const s = TYPE[t];
  return (
    <text
      x={x}
      y={y}
      textAnchor={anchor}
      fill={fill}
      opacity={opacity}
      style={{
        fontFamily: FONT,
        fontSize: s.size,
        fontWeight: s.weight,
        letterSpacing: s.ls,
        wordSpacing: s.ws,
        whiteSpace: "pre",
        fontKerning: "normal",
        ...style,
      }}
    >
      {children}
    </text>
  );
};

/** Full-canvas SVG layer. */
export const Layer: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <svg
    width={1080}
    height={1440}
    viewBox="0 0 1080 1440"
    style={{ position: "absolute", left: 0, top: 0, overflow: "visible", ...style }}
  >
    {children}
  </svg>
);

// Soft dark drop shadow the poster puts under white text on navy.
export const TEXT_SHADOW = "drop-shadow(1px 2px 1.6px rgba(0, 8, 40, 0.75))";
