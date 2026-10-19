import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

function formatBuildTime(value: Date) {
  const part = (number: number) => String(number).padStart(2, "0");
  return `${value.getFullYear()}-${part(value.getMonth() + 1)}-${part(value.getDate())} ${part(value.getHours())}:${part(value.getMinutes())}`;
}

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
      "/api": "http://127.0.0.1:8000",
      "/accounts": "http://127.0.0.1:8000",
      "/admin": "http://127.0.0.1:8000",
      "/attachments": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/static": "http://127.0.0.1:8000",
    },
  },
});
