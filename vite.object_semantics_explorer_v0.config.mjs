import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  root: resolve(process.cwd(), "frontend/object_semantics_explorer_v0"),
  base: "./",
  server: {
    host: "0.0.0.0",
    port: 4173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  build: {
    outDir: resolve(process.cwd(), "frontend_dist/object_semantics_explorer_v0"),
    emptyOutDir: true,
  },
});
