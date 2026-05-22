import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// VITE_API_BASE_URL is set in local env for dev; Docker uses nginx proxying.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  const apiTarget = env.VITE_API_BASE_URL || 'http://localhost:8000'

  return {
    plugins: [react()],
    server: {
      port: 5173,
      host: '0.0.0.0',
      proxy: {
        '/state': { target: apiTarget, changeOrigin: true },
        '/telemetry': { target: apiTarget, changeOrigin: true },
        '/anomaly': { target: apiTarget, changeOrigin: true },
        '/load': { target: apiTarget, changeOrigin: true },
        '/alerts': { target: apiTarget, changeOrigin: true },
        '/usb': { target: apiTarget, changeOrigin: true },
        '/predict': { target: apiTarget, changeOrigin: true },
        '/summary': { target: apiTarget, changeOrigin: true },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      chunkSizeWarningLimit: 1000,
    },
  }
})
