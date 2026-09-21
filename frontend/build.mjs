import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { build, transform } from "esbuild";
import postcss from "postcss";
import tailwindcss from "tailwindcss";

const root = fileURLToPath(new URL("../", import.meta.url));
const license = readFileSync(new URL("vendor/liquid-glass-react/LICENSE", import.meta.url), "utf8");
const reactLicense = readFileSync(new URL("../node_modules/react/LICENSE", import.meta.url), "utf8");
const motionLicense = readFileSync(new URL("../node_modules/framer-motion/LICENSE.md", import.meta.url), "utf8");

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

await build({
  absWorkingDir: root,
  entryPoints: ["./frontend/about.tsx"],
  outfile: "static/js/about.js",
  bundle: true,
  minify: true,
  format: "iife",
  platform: "browser",
  target: ["es2020"],
  jsx: "automatic",
  define: { "process.env.NODE_ENV": '"production"' },
  legalComments: "eof",
  banner: {
    js: `/*!\nPortfolio About section. See frontend/README.md.\nReact, React DOM and Scheduler:\n${reactLicense}\nFramer Motion:\n${motionLicense}\n*/`,
  },
  logLevel: "info",
});

const cssSource = new URL("about.css", import.meta.url);
const css = await postcss([tailwindcss({
  content: [
    fileURLToPath(new URL("about.tsx", import.meta.url)),
    fileURLToPath(new URL("../templates/index.html", import.meta.url)),
  ],
  prefix: "tw-",
  corePlugins: { preflight: false },
})]).process(readFileSync(cssSource, "utf8"), { from: fileURLToPath(cssSource) });
const compiled = await transform(css.css, { loader: "css", minify: true, legalComments: "eof" });
mkdirSync(new URL("../static/css/", import.meta.url), { recursive: true });
writeFileSync(new URL("../static/css/about.css", import.meta.url), compiled.code);
