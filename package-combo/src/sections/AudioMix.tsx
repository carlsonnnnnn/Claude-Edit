import React from 'react';
import {Audio, Sequence, interpolate, staticFile} from 'remotion';
import {DURATION, FPS} from '../theme';
import voEn from '../vo.json';
import voBm from '../vo_bm.json';

type VoLine = {file: string; start: number; duration: number};
export type Lang = 'en' | 'bm';

// Voice-over per language: clip timing (written by src/package_combo_vo.py) and the public/ folder.
const VO: Record<Lang, {lines: VoLine[]; dir: string}> = {
  en: {lines: voEn as VoLine[], dir: 'vo'},
  bm: {lines: voBm as VoLine[], dir: 'vo_bm'},
};

const DUCK = 0.3; // music level under a voice line
const ATTACK = 0.25; // s, duck starts this long before the line
const RELEASE = 0.35; // s, music comes back over this long after it

/** Music gain at a given frame: full, ducked to 30% under each line, faded out over the last second. */
export const musicVolume = (lines: VoLine[], frame: number) => {
  const t = frame / FPS;
  let duck = 1;
  for (const v of lines) {
    const a = v.start - ATTACK;
    const b = v.start + v.duration;
    const g = interpolate(t, [a - 0.01, v.start, b, b + RELEASE], [1, DUCK, DUCK, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    duck = Math.min(duck, g);
  }
  const end = DURATION / FPS;
  const fadeOut = interpolate(t, [end - 1, end], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return duck * fadeOut;
};

export const AudioMix: React.FC<{lang: Lang}> = ({lang}) => {
  const {lines, dir} = VO[lang];
  return (
    <>
      <Audio src={staticFile('royal_fanfare_30s.mp3')} volume={(f) => musicVolume(lines, f)} />
      {lines.map((v) => (
        <Sequence key={v.file} from={Math.round(v.start * FPS)} durationInFrames={Math.ceil(v.duration * FPS) + 2}>
          <Audio src={staticFile(`${dir}/${v.file}`)} />
        </Sequence>
      ))}
    </>
  );
};
