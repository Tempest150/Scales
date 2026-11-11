import process from 'node:process'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Docker needs to bind on 0.0.0.0; locally VITE_HOST is unset and Vite keeps its default.
    host: process.env.VITE_HOST || undefined,
    // Bind mounts on Windows/macOS don't deliver file events into the container.
    watch: process.env.VITE_USE_POLLING ? { usePolling: true, interval: 300 } : undefined,
    proxy: {
      '/api': {
        // Proxy API requests to the Quart backend (overridden to http://backend:5010 in Docker)
        target: process.env.VITE_API_TARGET || 'http://localhost:5010',
        changeOrigin: true
      }
    }
  }
})
