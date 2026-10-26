// Render preview stills with one bundle: node scripts/stills.mjs [frame ...]
// Default frames: 90 270 450 600 899 -> ../build/so/stills/frame-<n>.png
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const outDir = path.resolve(root, "../build/so/stills");
const frames = process.argv.slice(2).map(Number);
const list = frames.length ? frames : [90, 270, 450, 600, 899];
const LOCAL_SHELL = "/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell";
const browserExecutable = fs.existsSync(LOCAL_SHELL) ? LOCAL_SHELL : null;

fs.mkdirSync(outDir, { recursive: true });
const serveUrl = await bundle({ entryPoint: path.join(root, "src/index.ts"), publicDir: path.join(root, "public") });
const composition = await selectComposition({ serveUrl, id: "SubjectsOffered", browserExecutable });
for (const frame of list) {
  const output = path.join(outDir, `frame-${frame}.png`);
  await renderStill({ serveUrl, composition, frame, output, browserExecutable, imageFormat: "png" });
  console.log("wrote", output);
}
