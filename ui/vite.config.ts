import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Holo UI geliştirme sunucusu; /ws ve REST'i Jarvis API'sine yönlendirir.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/ws": { target: "ws://localhost:8000", ws: true },
      "/chat": "http://localhost:8000",
      "/agent": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
