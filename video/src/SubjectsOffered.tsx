import { loadFont } from "@remotion/fonts";
import React, { useEffect, useState } from "react";
import { AbsoluteFill, Audio, continueRender, delayRender, interpolate, staticFile } from "remotion";
import layout from "../public/layout.json";
import { Background } from "./components/Background";
import { ContactBar } from "./components/ContactBar";
import { Header } from "./components/Header";
import { LevelsCard } from "./components/LevelsCard";
import { Table } from "./components/Table";
import { Title } from "./components/Title";
import { Tutors } from "./components/Tutors";
import { DURATION, FONT, FPS } from "./theme";

const fontsReady = Promise.all(
  [500, 600, 700].map((w) =>
    loadFont({ family: FONT, url: staticFile(`fonts/outfit-latin-${w}-normal.woff2`), weight: String(w) }),
  ),
).then(() => document.fonts.ready);

export const SubjectsOffered: React.FC = () => {
  // Text is measured for the price count-up, so wait for the font first.
  const [handle] = useState(() => delayRender("Loading Outfit"));
  const [ready, setReady] = useState(false);
  useEffect(() => {
    fontsReady.then(() => {
      setReady(true);
      continueRender(handle);
    });
  }, [handle]);
  if (!ready) return null;

  return (
    <AbsoluteFill style={{ backgroundColor: "#081027" }}>
      <Background />
      <Header />
      <Tutors />
      <Table />
      <Title />
      <LevelsCard />
      <ContactBar />
      {layout.music && (
        <Audio
          src={staticFile("music.mp3")}
          volume={(f) => interpolate(f, [DURATION - FPS, DURATION - 1], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}
        />
      )}
    </AbsoluteFill>
  );
};
