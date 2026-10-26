import React from 'react';
import {Composition} from 'remotion';
import {PackageCombo} from './PackageCombo';
import {DURATION, FPS, HEIGHT, WIDTH} from './theme';
import './fonts';

const common = {component: PackageCombo, durationInFrames: DURATION, fps: FPS, width: WIDTH, height: HEIGHT};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="PackageCombo" {...common} defaultProps={{lang: 'en' as const}} />
    {/* Same picture, Bahasa Malaysia voice-over */}
    <Composition id="PackageComboBM" {...common} defaultProps={{lang: 'bm' as const}} />
  </>
);
