import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy API calls in development so CORS is handled locally
    proxy: {
      "/pipeline": "http://localhost:8000",
      "/stream":   "http://localhost:8000",
      "/download-pdf": "http://localhost:8000",
      "/health":   "http://localhost:8000",
    },
  },
});
