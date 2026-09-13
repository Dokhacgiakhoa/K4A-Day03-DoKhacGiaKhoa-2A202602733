import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Build ra ../static_react để FastAPI serve. base tương đối để chạy được ở mọi mount path.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "./",
  build: {
    outDir: "../static_react",
    emptyOutDir: true,
  },
  server: {
    // Khi chạy `npm run dev`, proxy các call /api sang FastAPI (cổng 8000)
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
