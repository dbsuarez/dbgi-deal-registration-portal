import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

function formatBuildTime(value: Date) {
  const part = (number: number) => String(number).padStart(2, "0");
  return `${value.getFullYear()}-${part(value.getMonth() + 1)}-${part(value.getDate())} ${part(value.getHours())}:${part(value.getMinutes())}`;
}

// The guide screenshots use their own backend port, so a running local backend is left alone.
const backend = process.env.BACKEND_URL || "http://127.0.0.1:8000";

// https://vite.dev/config/
export default defineConfig({
  define: {
    __BUILD_TIME__: JSON.stringify(
      process.env.BUILD_TIME || formatBuildTime(new Date()),
    ),
  },
  plugins: [react()],
  server: {
    proxy: {
      "/api": backend,
      "/accounts": backend,
      "/admin": backend,
      "/attachments": backend,
      "/health": backend,
      "/static": backend,
    },
  },
});
