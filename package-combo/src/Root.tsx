import React from 'react';
import {Composition} from 'remotion';
import {PackageCombo} from './PackageCombo';
import {DURATION, FPS, HEIGHT, WIDTH} from './theme';
import './fonts';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="PackageCombo"
    component={PackageCombo}
    durationInFrames={DURATION}
    fps={FPS}
    width={WIDTH}
    height={HEIGHT}
  />
);
