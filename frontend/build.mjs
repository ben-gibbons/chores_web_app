import * as esbuild from "esbuild";
import { copyFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = resolve(here, "..", "app", "static");
mkdirSync(outDir, { recursive: true });

const watch = process.argv.includes("--watch");

const options = {
  entryPoints: [resolve(here, "src", "main.ts")],
  bundle: true,
  format: "iife",
  target: ["es2022"],
  sourcemap: true,
  outfile: resolve(outDir, "app.js"),
  logLevel: "info",
};

const copyCss = () =>
  copyFileSync(resolve(here, "src", "styles.css"), resolve(outDir, "styles.css"));

if (watch) {
  const ctx = await esbuild.context({
    ...options,
    plugins: [
      {
        name: "copy-css",
        setup(build) {
          build.onEnd(() => copyCss());
        },
      },
    ],
  });
  await ctx.watch();
  console.log("watching frontend/src for changes...");
} else {
  await esbuild.build(options);
  copyCss();
}
