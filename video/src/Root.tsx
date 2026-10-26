import React from "react";
import { Composition } from "remotion";
import { SubjectsOffered } from "./SubjectsOffered";
import { DURATION, FPS, H, W } from "./theme";

export const RemotionRoot: React.FC = () => (
  <Composition id="SubjectsOffered" component={SubjectsOffered} durationInFrames={DURATION} fps={FPS} width={W} height={H} />
);
