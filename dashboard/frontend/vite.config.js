import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy all /api calls to the FastAPI backend during development
      '/state':       { target: 'http://localhost:8000', changeOrigin: true },
      '/telemetry':   { target: 'http://localhost:8000', changeOrigin: true },
      '/anomaly':     { target: 'http://localhost:8000', changeOrigin: true },
      '/load':        { target: 'http://localhost:8000', changeOrigin: true },
      '/alerts':      { target: 'http://localhost:8000', changeOrigin: true },
      '/usb':         { target: 'http://localhost:8000', changeOrigin: true },
      '/predict':     { target: 'http://localhost:8000', changeOrigin: true },
      '/summary':     { target: 'http://localhost:8000', changeOrigin: true },
    }
  }
})
