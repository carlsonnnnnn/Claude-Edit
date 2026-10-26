import React from 'react';
import {AbsoluteFill} from 'remotion';
import {AudioMix} from './sections/AudioMix';
import {Background} from './sections/Background';
import {Characters} from './sections/Characters';
import {AvailableCard, ContactBar, Floor} from './sections/Finale';
import {GoldDust} from './sections/GoldDust';
import {Intro} from './sections/Intro';
import {Table} from './sections/Table';
import {Title} from './sections/Title';

export const PackageCombo: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: '#08102b'}}>
    <Background />
    <GoldDust layer="back" />
    <Intro />
    <Title />
    <Table />
    <Characters />
    <Floor />
    <AvailableCard />
    <ContactBar />
    <GoldDust layer="front" />
    <AudioMix />
  </AbsoluteFill>
);
