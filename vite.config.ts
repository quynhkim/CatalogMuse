import path from "node:path";
import { fileURLToPath } from "node:url";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(dirname, "./src"),
      react: path.resolve(dirname, "./node_modules/react"),
      "react-dom": path.resolve(dirname, "./node_modules/react-dom"),
    },
    dedupe: ["react", "react-dom"],
  },
});
