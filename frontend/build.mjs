import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";

const root = fileURLToPath(new URL("../", import.meta.url));
const license = readFileSync(new URL("vendor/liquid-glass-react/LICENSE", import.meta.url), "utf8");
const reactLicense = readFileSync(new URL("../node_modules/react/LICENSE", import.meta.url), "utf8");

await build({
  absWorkingDir: root,
  entryPoints: ["./frontend/liquid-glass-buttons.tsx"],
  outfile: "static/js/liquid-glass.js",
  bundle: true,
  minify: true,
  format: "iife",
  platform: "browser",
  target: ["es2020"],
  jsx: "automatic",
  define: { "process.env.NODE_ENV": '"production"' },
  legalComments: "eof",
  banner: {
    js: `/*!\nLiquid Glass React 1.1.1 — https://github.com/rdev/liquid-glass-react\nAdapted for native Django links; see frontend/README.md.\n${license}\nReact, React DOM and Scheduler:\n${reactLicense}\n*/`,
  },
  logLevel: "info",
});
