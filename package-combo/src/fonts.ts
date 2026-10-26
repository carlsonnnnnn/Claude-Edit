import {continueRender, delayRender, staticFile} from 'remotion';
import {FONT_POPPINS, FONT_SPARTAN} from './theme';

const faces = [
  new FontFace(FONT_SPARTAN, `url(${staticFile('fonts/league-spartan-latin-700-normal.woff2')})`, {weight: '700'}),
  new FontFace(FONT_POPPINS, `url(${staticFile('fonts/poppins-latin-600-normal.woff2')})`, {weight: '600'}),
];

const handle = delayRender('Loading fonts');
Promise.all(faces.map((f) => f.load()))
  .then((loaded) => {
    loaded.forEach((f) => document.fonts.add(f));
    continueRender(handle);
  })
  .catch((err) => {
    console.error(err);
    continueRender(handle);
  });
