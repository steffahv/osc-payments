import { fileURLToPath, URL } from "node:url"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig, loadEnv } from "vite"

export default defineConfig(({ mode }) => {
  // Local configuration lives at the root; secrets never use the VITE_ prefix.
  const env = loadEnv(mode, "..", "")
  return {
    plugins: [react(), tailwindcss()],
    resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
    server: {
      port: 5173,
      strictPort: true,
      // Windows bind mounts may not deliver file events to Docker's Linux VM.
      watch: {
        usePolling: true,
        interval: 300,
      },
      proxy: {
        "/api": {
          target: process.env.API_PROXY_TARGET ?? env.API_PROXY_TARGET ?? "http://127.0.0.1:8000",
          changeOrigin: false,
        },
      },
    },
  }
})
