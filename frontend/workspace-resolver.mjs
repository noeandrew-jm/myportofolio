import { existsSync, readFileSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, extname, isAbsolute, resolve } from "node:path";

// Feed esbuild source through Node so its native resolver doesn't need to scan
// ancestor directories outside the workspace in restricted Windows sessions.
export function workspaceResolver(root) {
  const extensions = ["", ".tsx", ".ts", ".jsx", ".js", ".mjs", ".json"];
  return {
    name: "workspace-source",
    setup(builder) {
      builder.onResolve({ filter: /.*/ }, args => {
        const importer = args.importer || resolve(root, "package.json");
        let path;
        if (args.kind === "entry-point" || args.path.startsWith(".") || isAbsolute(args.path)) {
          const base = resolve(args.importer ? dirname(importer) : root, args.path);
          path = extensions.map(extension => base + extension)
            .find(candidate => existsSync(candidate) && statSync(candidate).isFile());
          if (!path) path = createRequire(importer).resolve(base);
        } else {
          path = createRequire(importer).resolve(args.path);
        }
        return { path, namespace: "workspace-source" };
      });
      builder.onLoad({ filter: /.*/, namespace: "workspace-source" }, args => ({
        contents: readFileSync(args.path, "utf8"),
        loader: ({ ".tsx": "tsx", ".ts": "ts", ".jsx": "jsx", ".json": "json" })[extname(args.path)] || "js",
      }));
    },
  };
}
