import {Config} from '@remotion/cli/config';

// Use the Chromium shipped with the container instead of downloading one.
Config.setBrowserExecutable(
  process.env.REMOTION_CHROME ??
    '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell',
);
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(95);
Config.setOverwriteOutput(true);
