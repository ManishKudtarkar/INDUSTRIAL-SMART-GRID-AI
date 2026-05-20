import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// VITE_API_BASE_URL is set in:
//   - .env file for local dev (http://localhost:8000)
//   - Docker build arg for container (http://backend:8000 → proxied by nginx)
const API_TARGET = process.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',   // needed for Docker port binding
    // Dev proxy — only active when running `npm run dev` locally
    // In Docker, nginx handles proxying instead
    proxy: {
      '/state':     { target: API_TARGET, changeOrigin: true },
      '/telemetry': { target: API_TARGET, changeOrigin: true },
      '/anomaly':   { target: API_TARGET, changeOrigin: true },
      '/load':      { target: API_TARGET, changeOrigin: true },
      '/alerts':    { target: API_TARGET, changeOrigin: true },
      '/usb':       { target: API_TARGET, changeOrigin: true },
      '/predict':   { target: API_TARGET, changeOrigin: true },
      '/summary':   { target: API_TARGET, changeOrigin: true },
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    // Suppress the chunk size warning (Recharts is large)
    chunkSizeWarningLimit: 1000,
  }
})
